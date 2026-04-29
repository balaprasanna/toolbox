"""Search tools — mirrors solveit's search capabilities
Uses system tools (rg, ast-grep) + pyskills for glob.
"""
import subprocess
from pyskills.core import globtastic
from typing import List, Optional

__all__ = [
    "rg",
    "sed",
    "grep",
    "glob_files", 
    "ast_grep",
    "find",
]


def rg(
    argstr: str,
    allow_re: Optional[str] = None,
    disallow_re: Optional[str] = None
) -> str:
    """Run ripgrep with raw args string (like solveit's rg tool).
    
    Args:
        argstr: All args to rg, split with shlex. No shell escaping needed for regex chars like `|`.
        allow_re: Optional regex - command only runs if argstr matches
        disallow_re: Optional regex - command blocked if argstr matches
    
    Examples:
        rg("--help")                                      # Show ripgrep help
        rg("--no-heading 'class.*:' '*.py'")             # Find class definitions
        rg("-A 5 -B 2 'def ' '*.py'")                    # Context around function defs
    """
    import shlex
    import re
    
    if allow_re and not re.search(allow_re, argstr):
        return f"error: command doesn't match allow_re: {allow_re}"
    if disallow_re and re.search(disallow_re, argstr):
        return f"error: command matches disallow_re: {disallow_re}"
    
    cmd = ["rg"] + shlex.split(argstr)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else (r.stderr or "no matches")


def sed(
    argstr: str,
    allow_re: Optional[str] = None,
    disallow_re: Optional[str] = None
) -> str:
    """Run sed with raw args string (like solveit's sed tool).
    
    Useful for reading/selecting sections of files.
    
    Args:
        argstr: All args to sed, split with shlex. No shell escaping needed.
        allow_re: Optional regex - command only runs if argstr matches
        disallow_re: Optional regex - command blocked if argstr matches
    
    Examples:
        sed("-n '10,20p' myfile.txt")          # Print lines 10-20
        sed("'/^def /,/^def /p' myfile.py")   # Print from first def to next def
    """
    import shlex
    import re
    
    if allow_re and not re.search(allow_re, argstr):
        return f"error: command doesn't match allow_re: {allow_re}"
    if disallow_re and re.search(disallow_re, argstr):
        return f"error: command matches disallow_re: {disallow_re}"
    
    cmd = ["sed"] + shlex.split(argstr)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else (r.stderr or "")


def grep(
    pattern: str,
    path: str = ".",
    glob: Optional[str] = None,
    ignore_case: bool = False,
    max_count: Optional[int] = None,
    context_lines: int = 0
) -> str:
    """Search for `pattern` (regex) in files under `path` using ripgrep.
    
    Args:
        pattern: Regex pattern to search
        path: Directory to search (default: current)
        glob: File glob filter (e.g., '*.py')
        ignore_case: Case-insensitive search
        max_count: Max matches per file
        context_lines: Lines of context around matches
    """
    cmd = ["rg", "--line-number", "--no-heading", "--color=never"]
    if ignore_case:
        cmd.append("-i")
    if max_count:
        cmd += ["-m", str(max_count)]
    if context_lines:
        cmd += ["-C", str(context_lines)]
    if glob:
        cmd += ["-g", glob]
    cmd += [pattern, path]
    
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode > 1:  # 0 = matches, 1 = no matches, 2+ = error
        return f"error: {r.stderr}"
    return r.stdout or "no matches"


def glob_files(
    path: str = ".",
    file_glob: Optional[str] = None,
    file_re: Optional[str] = None,
    recursive: bool = True,
    types: Optional[str] = None
) -> List[str]:
    """Find files under `path`.
    
    Filters:
        file_glob: Glob pattern (e.g., '*.py')
        file_re: Regex pattern for filenames
        types: Comma-separated extensions (e.g., 'py,js')
    
    Powered by globtastic from pyskills.
    """
    return list(globtastic(
        path,
        recursive=recursive,
        file_glob=file_glob,
        file_re=file_re,
        types=types
    ))


def ast_grep(pattern: str, path: str = ".", lang: str = "python") -> str:
    """Search code by AST pattern using ast-grep.
    
    Pattern syntax:
        $VAR - captures single node
        $$$ - captures multiple nodes
        Example: 'def $F($$$)' finds all function definitions
    
    Args:
        pattern: AST pattern to match
        path: Directory to search
        lang: Language (python, js, ts, etc.)
    """
    cmd = ["ast-grep", "run", "-p", pattern, "-l", lang, path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout or r.stderr or "no matches"


def find(
    path: str = ".",
    name: Optional[str] = None,
    type: Optional[str] = None,  # 'f' for file, 'd' for directory
    maxdepth: Optional[int] = None
) -> List[str]:
    """Find files/directories using system `find` command.
    
    Simpler alternative to glob_files for basic needs.
    """
    cmd = ["find", path]
    if maxdepth:
        cmd += ["-maxdepth", str(maxdepth)]
    if type:
        cmd += ["-type", type]
    if name:
        cmd += ["-name", name]
    
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip().split("\n") if r.stdout else []
