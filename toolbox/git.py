"""Git tools — mirrors solveit's git capabilities
Comprehensive git operations via subprocess.
"""
import subprocess
from typing import Optional, List

__all__ = [
    "git_status",
    "git_diff",
    "git_log",
    "git_add",
    "git_commit",
    "git_branch",
    "git_checkout",
    "git_push",
    "git_pull",
    "git_clone",
    "git_remote",
    "git_stash",
    "git_reset",
    "git_show",
]


def _git(args: List[str], cwd: Optional[str] = None) -> str:
    """Internal: run git command."""
    r = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=cwd
    )
    return (r.stdout or "") + (r.stderr or "")


def git_status(cwd: Optional[str] = None, short: bool = True) -> str:
    """Show git working tree status."""
    args = ["status"]
    if short:
        args.extend(["--short", "--branch"])
    return _git(args, cwd)


def git_diff(
    path: Optional[str] = None,
    staged: bool = False,
    cwd: Optional[str] = None
) -> str:
    """Show git diff.
    
    Args:
        path: Optional specific file path
        staged: If True, shows index vs HEAD; else working tree vs index
        cwd: Working directory
    """
    args = ["diff"]
    if staged:
        args.append("--cached")
    if path:
        args.append(path)
    return _git(args, cwd)


def git_log(n: int = 10, oneline: bool = True, cwd: Optional[str] = None) -> str:
    """Show recent git log.
    
    Args:
        n: Number of commits (default: 10)
        oneline: Show one line per commit
        cwd: Working directory
    """
    args = ["log", f"-n{n}"]
    if oneline:
        args.extend(["--oneline", "--decorate"])
    return _git(args, cwd)


def git_add(path: str = ".", cwd: Optional[str] = None) -> str:
    """Stage changes at `path` (default: all)."""
    _git(["add", path], cwd)
    return f"staged: {path}"


def git_commit(message: str, cwd: Optional[str] = None) -> str:
    """Create a git commit with `message`."""
    out = _git(["commit", "-m", message], cwd)
    return out or f"committed: {message[:50]}..."


def git_branch(name: Optional[str] = None, cwd: Optional[str] = None) -> str:
    """List branches, or create and checkout new `name`."""
    if name:
        out = _git(["checkout", "-b", name], cwd)
        return out or f"created and switched to branch: {name}"
    else:
        return _git(["branch", "--show-current"], cwd)


def git_checkout(ref: str, cwd: Optional[str] = None) -> str:
    """Checkout branch or commit `ref`."""
    return _git(["checkout", ref], cwd)


def git_push(
    remote: str = "origin",
    branch: Optional[str] = None,
    cwd: Optional[str] = None
) -> str:
    """Push to remote (default: origin)."""
    args = ["push", remote]
    if branch:
        args.append(branch)
    return _git(args, cwd)


def git_pull(
    remote: str = "origin",
    branch: Optional[str] = None,
    cwd: Optional[str] = None
) -> str:
    """Pull from remote (default: origin)."""
    args = ["pull", remote]
    if branch:
        args.append(branch)
    return _git(args, cwd)


def git_clone(url: str, dest: Optional[str] = None, cwd: Optional[str] = None) -> str:
    """Clone repository from `url`.
    
    Args:
        url: Repository URL
        dest: Destination directory (default: inferred from URL)
        cwd: Working directory for relative paths
    """
    args = ["clone", url]
    if dest:
        args.append(dest)
    return _git(args, cwd)


def git_remote(cwd: Optional[str] = None) -> str:
    """Show remote repositories."""
    return _git(["remote", "-v"], cwd)


def git_stash(message: Optional[str] = None, cwd: Optional[str] = None) -> str:
    """Stash changes (optionally with message)."""
    args = ["stash"]
    if message:
        args.extend(["push", "-m", message])
    return _git(args, cwd)


def git_reset(
    hard: bool = False,
    ref: str = "HEAD",
    cwd: Optional[str] = None
) -> str:
    """Reset to ref (default: HEAD).
    
    Use hard=True to discard changes (dangerous!).
    """
    args = ["reset"]
    if hard:
        args.append("--hard")
    args.append(ref)
    return _git(args, cwd)


def git_show(ref: str = "HEAD", cwd: Optional[str] = None) -> str:
    """Show commit details for `ref`."""
    return _git(["show", ref], cwd)