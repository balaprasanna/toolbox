"""Tool registry — unified abstraction for tools the LLM can call.

Two ways to use this package:

**Path 1 — raw functions** (simplest):
    from toolbox import fs, search
    chat = Chat(tools=[fs.read, fs.view, search.grep])  # claudette style

**Path 2 — explicit registry** (for MCP unification, custom dispatch, multiple sources):
    from toolbox import registry, fs, search, intro
    r = registry.ToolRegistry()
    r.add_module(fs, only=["read", "view", "ls"])
    r.add_module(intro)                            # all of intro
    r.add(search.grep)
    schemas = r.to_anthropic_tools()               # for Anthropic API
    result  = await r.dispatch(name, **args)       # for tool execution

Tools are named module-qualified by default — ``fs.read``, ``search.grep``, ``intro.symsrc``.
This avoids collisions and reads naturally in Claude's tool_use blocks.

No global singleton, no side effects on import. The consumer constructs their own registry.
"""
from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    runtime_checkable,
)


# ---- Enums + dataclasses ----

class ToolSource(Enum):
    """Where a tool comes from."""
    INTERNAL = auto()  # Native Python function in this process
    MCP = auto()       # Tool exposed by an MCP server (executor calls over network)


@dataclass(frozen=True)
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass(frozen=True)
class ToolSchema:
    name: str
    description: str
    parameters: List[ToolParameter]
    returns: Optional[str] = None


@runtime_checkable
class ToolExecutor(Protocol):
    """Anything callable can be a ToolExecutor (sync or async)."""
    def __call__(self, **kwargs) -> Any: ...


@dataclass
class Tool:
    """A single tool the LLM can call.

    Wraps either a local Python function (source=INTERNAL) or a remote
    MCP-server tool (source=MCP, executor calls over the network).
    """
    name: str
    description: str
    schema: ToolSchema
    source: ToolSource
    executor: Callable[..., Any]
    source_id: Optional[str] = None  # e.g. "xray" for an MCP-sourced tool
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Render as the dict Anthropic's Messages API expects in `tools=[...]`."""
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for p in self.schema.parameters:
            prop: Dict[str, Any] = {"type": p.type, "description": p.description}
            if p.enum:
                prop["enum"] = p.enum
            properties[p.name] = prop
            if p.required:
                required.append(p.name)
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    async def execute(self, **kwargs) -> Any:
        """Run the tool. Async if the executor is a coroutine; otherwise off-thread."""
        if inspect.iscoroutinefunction(self.executor):
            return await self.executor(**kwargs)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.executor(**kwargs))


# ---- Schema-from-function ----

_PY_TO_JSON: Dict[Any, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    type(None): "null",
}


def _resolve_annotation(annotation: Any) -> str:
    """Turn a Python annotation into a JSON-schema type string. Falls back to 'string'."""
    if annotation is inspect.Parameter.empty:
        return "string"
    # Unwrap Optional[X] / Union[X, None] -> X
    try:
        from typing import get_origin, get_args, Union
        if get_origin(annotation) is Union:
            args = [a for a in get_args(annotation) if a is not type(None)]
            if args:
                annotation = args[0]
        # List[X] -> array
        if get_origin(annotation) in (list, List):
            return "array"
        if get_origin(annotation) in (dict, Dict):
            return "object"
    except Exception:
        pass
    return _PY_TO_JSON.get(annotation, "string")


def make_tool_from_function(
    func: Callable[..., Any],
    name: Optional[str] = None,
    description: Optional[str] = None,
    source: ToolSource = ToolSource.INTERNAL,
    source_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Tool:
    """Introspect a Python function's signature and build a Tool from it."""
    name = name or func.__name__
    description = description or (func.__doc__ or "").strip().split("\n")[0] or name

    sig = inspect.signature(func)
    # Try to resolve annotations; fall back to bare signature (some annotations
    # reference types that don't import in this scope, e.g. httpx._types).
    try:
        type_hints = inspect.get_annotations(func, eval_str=True)
    except Exception:
        type_hints = {}

    parameters: List[ToolParameter] = []
    for pname, param in sig.parameters.items():
        if pname == "self":
            continue
        anno = type_hints.get(pname, param.annotation)
        json_type = _resolve_annotation(anno)
        is_required = param.default is inspect.Parameter.empty
        parameters.append(ToolParameter(
            name=pname,
            type=json_type,
            description=f"Parameter: {pname}",
            required=is_required,
            default=None if is_required else param.default,
        ))

    schema = ToolSchema(name=name, description=description, parameters=parameters)
    return Tool(
        name=name,
        description=description,
        schema=schema,
        source=source,
        executor=func,
        source_id=source_id,
        metadata=metadata or {},
    )


# ---- Registry ----

class ToolRegistry:
    """A collection of Tools that can be queried, listed, and dispatched.

    No global state — instantiate one per consumer. Tool names are unique;
    re-registering a name raises ValueError.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}
        self._by_source: Dict[str, List[str]] = {}  # source_id -> tool names

    # --- registration ---

    def add_tool(self, tool: Tool) -> Tool:
        """Add a pre-built Tool to the registry."""
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name!r} already registered")
        self._tools[tool.name] = tool
        if tool.source_id:
            self._by_source.setdefault(tool.source_id, []).append(tool.name)
        return tool

    def add(
        self,
        func: Callable[..., Any],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Tool:
        """Wrap a single Python function as a Tool and register it."""
        return self.add_tool(make_tool_from_function(func, name=name, description=description))

    def add_module(
        self,
        module: Any,
        only: Optional[List[str]] = None,
        skip: Optional[List[str]] = None,
    ) -> List[Tool]:
        """Register every function in ``module.__all__`` (or all public callables) as a tool.

        Tool names are module-qualified (``fs.read``, ``search.grep``).

        Args:
            module: a Python module with public functions.
            only: optional whitelist of function names to register.
            skip: optional blacklist of function names to exclude.
        """
        short_name = module.__name__.rsplit(".", 1)[-1]
        names = getattr(module, "__all__", None)
        if names is None:
            names = [n for n in dir(module) if not n.startswith("_")]

        if only is not None:
            only_set = set(only)
            names = [n for n in names if n in only_set]
        if skip is not None:
            skip_set = set(skip)
            names = [n for n in names if n not in skip_set]

        registered: List[Tool] = []
        for fn_name in names:
            obj = getattr(module, fn_name, None)
            if not callable(obj) or isinstance(obj, type):
                continue
            qualified = f"{short_name}.{fn_name}"
            try:
                tool = make_tool_from_function(
                    obj,
                    name=qualified,
                    metadata={"module": short_name, "original_name": fn_name},
                )
                self.add_tool(tool)
                registered.append(tool)
            except Exception:
                # Some functions resist introspection; skip silently rather than crash collection.
                continue
        return registered

    def add_mcp(
        self,
        schema_dict: Dict[str, Any],
        executor: Callable[..., Awaitable[Any]],
        source_id: str,
    ) -> Tool:
        """Register a tool whose schema came from an MCP server's list_tools() response.

        Args:
            schema_dict: ``{"name": ..., "description": ..., "input_schema": {...}}``
                in Anthropic format (toolslm/MCP both produce this shape).
            executor: an async callable that performs the actual MCP call_tool roundtrip.
            source_id: a label for the MCP server (e.g. ``"xray"``).
        """
        name = schema_dict["name"]
        description = schema_dict.get("description", "")
        input_schema = schema_dict.get("input_schema", {})
        properties = input_schema.get("properties", {})
        required = set(input_schema.get("required", []))
        parameters = [
            ToolParameter(
                name=pname,
                type=pdef.get("type", "string"),
                description=pdef.get("description", ""),
                required=pname in required,
                enum=pdef.get("enum"),
            )
            for pname, pdef in properties.items()
        ]
        schema = ToolSchema(name=name, description=description, parameters=parameters)
        tool = Tool(
            name=name,
            description=description,
            schema=schema,
            source=ToolSource.MCP,
            executor=executor,
            source_id=source_id,
            metadata={"mcp_server": source_id},
        )
        return self.add_tool(tool)

    # --- queries ---

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self, source: Optional[ToolSource] = None) -> List[Tool]:
        tools = list(self._tools.values())
        if source is not None:
            tools = [t for t in tools if t.source is source]
        return tools

    def list_by_source(self, source_id: str) -> List[Tool]:
        names = self._by_source.get(source_id, [])
        return [self._tools[n] for n in names if n in self._tools]

    def to_anthropic_tools(self) -> List[Dict[str, Any]]:
        """Render the whole registry as Anthropic-format tools, sorted by name (stable cache prefix)."""
        return sorted(
            (t.to_anthropic_format() for t in self._tools.values()),
            key=lambda t: t["name"],
        )

    async def dispatch(self, name: str, **arguments: Any) -> Any:
        """Look up and execute a tool by name."""
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool {name!r} not in registry")
        return await tool.execute(**arguments)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)

    def __iter__(self):
        return iter(self._tools.values())


# ---- Convenience: collect every toolbox module into one registry ----

def collect_all(only_modules: Optional[List[str]] = None) -> ToolRegistry:
    """Build a fresh registry with every toolbox module registered.

    Use as a starting point when you want the whole tool surface; otherwise
    construct ``ToolRegistry()`` and ``.add_module(...)`` selectively.

    Args:
        only_modules: optional list of module short names to include
            (e.g. ``["fs", "search", "intro"]``). Default: all eleven modules.
    """
    from . import fs, edit, search, code, intro, git, github, web, notebook, shell, extended

    all_modules = {
        "fs": fs, "edit": edit, "search": search, "code": code,
        "intro": intro, "git": git, "github": github, "web": web,
        "notebook": notebook, "shell": shell, "extended": extended,
    }
    if only_modules is not None:
        chosen = {k: v for k, v in all_modules.items() if k in only_modules}
    else:
        chosen = all_modules

    r = ToolRegistry()
    for mod in chosen.values():
        r.add_module(mod)
    return r
