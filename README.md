# toolbox

Utility tool functions for Claude-style agents. A library of well-tested, channel-agnostic tools that any agent (Slack bot, CLI, web UI, MCP server) can pick up and hand to the LLM.

Modeled on solveit's tool organization, restructured for use across multiple agent projects.

## Install

```sh
pip install claude-toolbox
```

The PyPI dist name is `claude-toolbox` (the unprefixed `toolbox` was taken). The Python import name stays `toolbox`:

```python
import toolbox
from toolbox import fs, search, intro
from toolbox.registry import ToolRegistry
```

### System binaries used by some tools

A few modules shell out to external binaries — install via your platform package manager (or `conda install -c conda-forge ripgrep ast-grep git`):

| Module / tool | Needs | Install (macOS) | Install (Linux) |
|---|---|---|---|
| `search.grep`, `search.rg` | `rg` (ripgrep) | `brew install ripgrep` | `apt install ripgrep` |
| `search.ast_grep` | `ast-grep` | `brew install ast-grep` | `apt install ast-grep` |
| `git.*` | `git` | (preinstalled) | `apt install git` |

Tools fail at call-time with a clear error if the binary isn't on `PATH`.

## Two ways to use it

### Path 1 — raw functions (simplest)

Just import the function and pass it where the LLM expects callables (e.g. claudette's `Chat(tools=[...])`):

```python
from toolbox import fs, search, intro

chat = Chat(tools=[fs.read, fs.view, search.grep, intro.symsrc])
```

No abstraction, no registry. The functions have docstrings and type hints; claudette / toolslm derive schemas via `get_schema`.

### Path 2 — explicit registry (for MCP unification, custom dispatch, multi-source)

When you need to merge local Python tools with MCP-server tools, or apply path-scoping wrappers, or curate per-agent subsets:

```python
from toolbox import registry, fs, search, intro

r = registry.ToolRegistry()
r.add_module(fs, only=["read", "view", "ls"])     # selective subset
r.add_module(intro)                                # whole module
r.add(search.grep)                                 # one function
r.add_mcp(schema, executor, source_id="xray")     # MCP-sourced tool

# Render for Anthropic's Messages API
schemas = r.to_anthropic_tools()

# Dispatch a tool_use from a model response
result = await r.dispatch(name, **arguments)
```

Tools registered via `add_module` get **module-qualified names**: `fs.read`, `search.grep`, `intro.symsrc`. No collisions, self-documenting in `tool_use` blocks.

### Convenience: `collect_all`

Build a registry pre-populated with every toolbox module:

```python
from toolbox import collect_all

r = collect_all()                                       # all 96 tools
r = collect_all(only_modules=["fs", "search", "intro"]) # subset
```

## What's inside

96 tools across 11 modules:

| Module | Count | What's in it |
|---|---|---|
| `fs` | 11 | File system: `read`, `write`, `view`, `ls`, `mkdir`, `rm`, `mv`, `cp`, `exists`, `is_file`, `is_dir` |
| `edit` | 5 | Surgical file edits: `str_replace`, `strs_replace`, `insert_line`, `replace_lines`, `del_lines` |
| `search` | 6 | Code search: `rg`, `sed`, `grep`, `ast_grep`, `glob_files`, `find` |
| `code` | 4 | Python execution: `pyrun` (persistent IPython), `pyrun_subprocess`, `eval_python`, `reset_shell` |
| `intro` | 11 | Symbol introspection (re-exports from `toolslm.inspecttools`): `symsrc`, `symsearch`, `symdir`, `symval`, `symtype`, `symslice`, `symnth`, `symlen`, `symfiles_folder`, `symfiles_package`, `importmodule` |
| `git` | 14 | Git ops: `git_status`, `git_diff`, `git_log`, `git_show`, `git_add`, `git_commit`, `git_branch`, `git_checkout`, `git_push`, `git_pull`, `git_clone`, `git_remote`, `git_stash`, `git_reset` |
| `github` | 9 | GitHub API: `gh_repo`, `gh_pr`, `gh_issue`, `gh_search_code`, `gh_list_files`, `gh_read_file`, plus `repo2ctx`, `folder2ctx`, `parse_gh_url` from toolslm |
| `web` | 9 | Web fetching: `read_md`, `read_html`, `read_docs`, `html2md`, `find_docs`, `fetch`, `fetch_json`, `fetch_bytes`, `web_search` (DuckDuckGo) |
| `notebook` | 12 | Jupyter `.ipynb` operations: `view_nb`, `view_cell`, `cell_*` editors, `nb_add_cell`, `nb_delete_cell`, `mk_cell`, `read_nb`, `write_nb` |
| `shell` | 3 | Shell commands: `shell`, `run_cmd`, `which` |
| `extended` | 12 | Testing/validation: `run_tests`, `run_pytest`, `run_unittest`, `lint_code`, `type_check`, `format_code`, `security_check`, `generate_docs`, `doc_preview`, `count_lines`, `dependency_graph`, `code_stats` |

## Design principles

- **No global state.** `import toolbox` has no side effects — no auto-registration, no print spam, no eager imports of every dep.
- **Modules over abstractions.** Each module is a flat namespace of functions you can use directly. The `Tool` / `ToolRegistry` abstraction is opt-in.
- **Module-qualified names** in registries (`fs.read`, not `fsread`). Self-documenting and collision-free.
- **Sync functions, async dispatch.** Tools are sync Python functions; `Tool.execute` runs them off-thread when called from async code.
- **Tested individually.** Each tool is verified in isolation; the registry just composes them.

## API reference (Path 2 essentials)

### `Tool`
```python
@dataclass
class Tool:
    name: str
    description: str
    schema: ToolSchema
    source: ToolSource          # INTERNAL | MCP
    executor: Callable[..., Any]
    source_id: Optional[str]
    metadata: Dict[str, Any]

    def to_anthropic_format() -> dict
    async def execute(**kwargs) -> Any
```

### `ToolRegistry`
```python
class ToolRegistry:
    def add_tool(tool: Tool) -> Tool
    def add(func, name=None, description=None) -> Tool
    def add_module(module, only=None, skip=None) -> List[Tool]
    def add_mcp(schema_dict, executor, source_id) -> Tool

    def get(name: str) -> Optional[Tool]
    def list_tools(source: Optional[ToolSource] = None) -> List[Tool]
    def list_by_source(source_id: str) -> List[Tool]

    def to_anthropic_tools() -> List[dict]            # for Anthropic API
    async def dispatch(name: str, **arguments) -> Any  # for tool_use execution
```

### `make_tool_from_function`
```python
def make_tool_from_function(
    func, name=None, description=None,
    source=ToolSource.INTERNAL, source_id=None, metadata=None,
) -> Tool
```

### `collect_all`
```python
def collect_all(only_modules: Optional[List[str]] = None) -> ToolRegistry
```

## License

Internal library — pick a license before publishing publicly.
