"""Shell tools — mirrors solveit's shell execution capabilities
Run shell commands with timeout and working directory control.
"""
import subprocess
from typing import Optional

__all__ = ["shell", "which", "run_cmd"]


def shell(cmd: str, cwd: Optional[str] = None, timeout: int = 60) -> str:
    """Run shell `cmd` and return combined stdout/stderr.
    
    Args:
        cmd: Shell command to run (can include pipes, redirects)
        cwd: Working directory (default: current)
        timeout: Timeout in seconds (default: 60)
    
    Returns:
        Combined stdout + stderr, with exit code if non-zero
    """
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout
        )
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode:
            out += f"\n[exit {r.returncode}]"
        return out
    except subprocess.TimeoutExpired:
        return f"error: command timed out after {timeout}s"


def run_cmd(
    cmd: list,
    cwd: Optional[str] = None,
    timeout: int = 60,
    shell: bool = False
) -> str:
    """Run command as list (safer, no shell interpretation).
    
    Use this when you don't need shell features (pipes, wildcards).
    More secure for user-provided input.
    """
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
            shell=shell
        )
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode:
            out += f"\n[exit {r.returncode}]"
        return out
    except subprocess.TimeoutExpired:
        return f"error: command timed out after {timeout}s"


def which(cmd: str) -> Optional[str]:
    """Find full path of executable `cmd` (returns None if not found)."""
    r = subprocess.run(["which", cmd], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None