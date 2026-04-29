"""toolbox — utility tool functions for Claude-style agents.

Two ways to use this:

**Path 1 — raw functions** (simplest):
    from toolbox import fs, search
    chat = Chat(tools=[fs.read, search.grep])

**Path 2 — explicit registry** (for MCP unification, multi-source dispatch):
    from toolbox import registry, fs, search, intro
    r = registry.ToolRegistry()
    r.add_module(fs, only=["read", "view"])
    r.add_module(intro)
    schemas = r.to_anthropic_tools()
    result  = await r.dispatch(name, **args)

Or, for the whole tool surface in one call:
    from toolbox import collect_all
    r = collect_all()                        # all 11 modules
    r = collect_all(only_modules=["fs"])     # subset

Importing this package has **no side effects** — no global registry is built,
no tools are registered. Build your own registry when you want one.
"""
__version__ = "0.5.2"

# Tool modules — usable directly as Path 1
from . import (
    fs,
    edit,
    search,
    code,
    intro,
    git,
    github,
    web,
    notebook,
    shell,
    extended,
)

# Registry abstraction (Path 2)
from . import registry
from .registry import (
    Tool,
    ToolParameter,
    ToolSchema,
    ToolSource,
    ToolRegistry,
    ToolExecutor,
    make_tool_from_function,
    collect_all,
)

__all__ = [
    "__version__",
    # Tool modules
    "fs", "edit", "search", "code", "intro",
    "git", "github", "web", "notebook", "shell", "extended",
    # Registry
    "registry",
    "Tool",
    "ToolParameter",
    "ToolSchema",
    "ToolSource",
    "ToolRegistry",
    "ToolExecutor",
    "make_tool_from_function",
    "collect_all",
]
