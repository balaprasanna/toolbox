"""Code execution tools — mirrors solveit's Python execution
Persistent IPython shell + subprocess fallback for isolation.
"""
import subprocess
import sys
from typing import Optional

__all__ = [
    "pyrun",
    "pyrun_subprocess",
    "reset_shell",
    "eval_python",
]

# Module-level persistent shell (lazy initialized from toolslm)
_SHELL = None


def _get_shell():
    """Lazy initialization of persistent IPython shell."""
    global _SHELL
    if _SHELL is None:
        from toolslm.shell import get_shell
        _SHELL = get_shell()
    return _SHELL


def reset_shell() -> str:
    """Reset the persistent IPython shell, clearing all state and variables."""
    global _SHELL
    _SHELL = None
    return "shell reset"


def pyrun(code: str, timeout: int = 30) -> str:
    """Run Python `code` in a persistent IPython shell.
    
    State persists across calls (variables, imports, definitions).
    Perfect for multi-step coding tasks.
    
    Args:
        code: Python code to execute
        timeout: Timeout in seconds (default: 30)
    
    Returns:
        stdout + result or error messages
    """
    sh = _get_shell()
    res = sh.run_cell(code, timeout=timeout)
    
    out = res.stdout or ""
    if res.error_in_exec:
        out += f"\n[error] {type(res.error_in_exec).__name__}: {res.error_in_exec}"
    if res.error_before_exec:
        out += f"\n[parse error] {res.error_before_exec}"
    if res.result is not None and not res.error_in_exec:
        out += f"\n=> {res.result!r}" if out else f"{res.result!r}"
    
    return out or "(no output)"


def pyrun_subprocess(code: str, timeout: int = 60) -> str:
    """Run Python `code` in a fresh subprocess (no shared state).
    
    Use for isolated runs where you don't want to pollute the persistent shell.
    Better for testing code that might crash or have side effects.
    
    Args:
        code: Python code to execute
        timeout: Timeout in seconds (default: 60)
    """
    try:
        r = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode:
            out += f"\n[exit {r.returncode}]"
        return out
    except subprocess.TimeoutExpired:
        return f"error: timed out after {timeout}s"


def eval_python(expr: str, timeout: int = 10) -> str:
    """Quickly evaluate a Python expression and return the result.
    
    Convenience wrapper for simple expressions (no statements).
    Uses persistent shell for consistency.
    """
    return pyrun(f"repr({expr})", timeout=timeout)