"""File system tools — equivalent to pyskills + dialoghelper file ops
View, read, write, list directories with line numbers and ranges.
"""
from pathlib import Path
from typing import List, Optional, Union

__all__ = [
    "read", "write", "view", "ls", "mkdir", "exists", 
    "is_file", "is_dir", "rm", "mv", "cp"
]


def read(path: str, encoding: str = "utf-8") -> str:
    """Read text content of file at `path`."""
    return Path(path).read_text(encoding=encoding)


def write(path: str, content: str, encoding: str = "utf-8") -> str:
    """Write `content` to file at `path`, creating parent dirs. Returns status."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding=encoding)
    return f"wrote {len(content)} chars to {path}"


def view(
    path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    nums: bool = True
) -> str:
    """View directory listing OR file content.
    
    For files: optional 1-based [start_line, end_line] range and line numbers.
    For dirs: sorted list of entries.
    """
    p = Path(path)
    if p.is_dir():
        entries = sorted(p.iterdir(), key=lambda x: x.name.lower())
        lines = []
        for o in entries:
            name = o.name
            suffix = "/" if o.is_dir() else ""
            size = ""
            if o.is_file():
                size_kb = o.stat().st_size / 1024
                size = f" ({size_kb:.1f}k)" if size_kb < 1024 else f" ({size_kb/1024:.1f}M)"
            lines.append(f"  {name}{suffix}{size}")
        return f"{path}/\n" + "\n".join(lines)
    
    lines = p.read_text().splitlines()
    s = (start_line or 1) - 1
    e = end_line if end_line else len(lines)
    
    if not nums:
        return "\n".join(lines[s:e])
    
    # Line numbers with proper alignment
    width = len(str(e))
    return "\n".join(f"{i+1:>{width}}│ {l}" for i, l in enumerate(lines[s:e], start=s))


def ls(path: str = ".") -> List[str]:
    """List entries in directory `path` as a flat list of names."""
    return sorted(
        o.name + ("/" if o.is_dir() else "")
        for o in Path(path).iterdir()
    )


def mkdir(path: str, parents: bool = True) -> str:
    """Create directory (and parents if needed)."""
    Path(path).mkdir(parents=parents, exist_ok=True)
    return f"created directory: {path}"


def exists(path: str) -> bool:
    """Check if path exists."""
    return Path(path).exists()


def is_file(path: str) -> bool:
    """Check if path is a file."""
    return Path(path).is_file()


def is_dir(path: str) -> bool:
    """Check if path is a directory."""
    return Path(path).is_dir()


def rm(path: str, recursive: bool = False) -> str:
    """Remove file or directory. Use recursive=True for non-empty dirs."""
    p = Path(path)
    if p.is_file():
        p.unlink()
        return f"removed file: {path}"
    elif p.is_dir():
        if recursive:
            import shutil
            shutil.rmtree(p)
            return f"removed directory (recursive): {path}"
        else:
            p.rmdir()
            return f"removed empty directory: {path}"
    return f"path not found: {path}"


def mv(src: str, dst: str) -> str:
    """Move/rename file or directory from `src` to `dst`."""
    Path(src).rename(dst)
    return f"moved: {src} -> {dst}"


def cp(src: str, dst: str) -> str:
    """Copy file from `src` to `dst`."""
    import shutil
    shutil.copy2(src, dst)
    return f"copied: {src} -> {dst}"