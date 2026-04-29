"""Extended tools — beyond solveit's capabilities
Additional utilities for testing, validation, documentation, etc.
"""
import subprocess
from typing import List, Optional, Dict, Any

__all__ = [
    # Testing
    "run_tests",
    "run_pytest",
    "run_unittest",
    # Validation
    "lint_code",
    "type_check",
    "format_code",
    "security_check",
    # Documentation
    "generate_docs",
    "doc_preview",
    # Utilities
    "count_lines",
    "dependency_graph",
    "code_stats",
]


# ============ Testing Tools ============

def run_tests(
    path: str = ".",
    runner: str = "pytest",
    args: Optional[List[str]] = None,
    timeout: int = 120
) -> str:
    """Run test suite at `path`.
    
    Args:
        path: Directory or specific test file
        runner: Test runner ('pytest', 'unittest')
        args: Additional arguments
        timeout: Max seconds to wait
    
    Returns:
        Test output and summary.
    """
    if runner == "pytest":
        return run_pytest(path, args, timeout)
    elif runner == "unittest":
        return run_unittest(path, args, timeout)
    else:
        return f"unknown runner: {runner}"


def run_pytest(
    path: str = ".",
    args: Optional[List[str]] = None,
    timeout: int = 120
) -> str:
    """Run pytest at `path`.
    
    Args:
        path: Test directory or file
        args: Additional pytest arguments
        timeout: Max seconds
    
    Returns:
        Test output with summary.
    """
    cmd = ["python", "-m", "pytest", path, "-v", "--tb=short"]
    if args:
        cmd.extend(args)
    
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode:
            out += f"\n[exit {r.returncode}]"
        return out
    except subprocess.TimeoutExpired:
        return f"pytest timed out after {timeout}s"


def run_unittest(
    path: str = ".",
    args: Optional[List[str]] = None,
    timeout: int = 120
) -> str:
    """Run unittest discover at `path`.
    
    Args:
        path: Directory to discover tests
        args: Additional unittest arguments
        timeout: Max seconds
    
    Returns:
        Test output with summary.
    """
    cmd = ["python", "-m", "unittest", "discover", "-v", "-s", path]
    if args:
        cmd.extend(args)
    
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode:
            out += f"\n[exit {r.returncode}]"
        return out
    except subprocess.TimeoutExpired:
        return f"unittest timed out after {timeout}s"


# ============ Validation Tools ============

def lint_code(
    path: str = ".",
    tool: str = "ruff",
    fix: bool = False
) -> str:
    """Lint Python code.
    
    Args:
        path: File or directory to lint
        tool: Linter tool ('ruff', 'flake8', 'pylint')
        fix: Auto-fix issues if supported
    
    Returns:
        Linting output with issues found.
    """
    if tool == "ruff":
        cmd = ["ruff", "check", path]
        if fix:
            cmd.append("--fix")
    elif tool == "flake8":
        cmd = ["flake8", path]
    elif tool == "pylint":
        cmd = ["pylint", path]
    else:
        return f"unknown linter: {tool}"
    
    r = subprocess.run(cmd, capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "") or "no linting issues found"


def type_check(
    path: str = ".",
    tool: str = "mypy"
) -> str:
    """Type check Python code.
    
    Args:
        path: File or directory to check
        tool: Type checker ('mypy', 'pyright')
    
    Returns:
        Type checking output.
    """
    if tool == "mypy":
        cmd = ["mypy", path]
    elif tool == "pyright":
        cmd = ["pyright", path]
    else:
        return f"unknown type checker: {tool}"
    
    r = subprocess.run(cmd, capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "")


def format_code(
    path: str = ".",
    tool: str = "ruff",
    check_only: bool = False
) -> str:
    """Format Python code.
    
    Args:
        path: File or directory to format
        tool: Formatter ('ruff', 'black')
        check_only: Only check formatting, don't apply
    
    Returns:
        Formatting output.
    """
    if tool == "ruff":
        cmd = ["ruff", "format", path]
        if check_only:
            cmd.append("--check")
    elif tool == "black":
        cmd = ["black", "--check" if check_only else "", path]
        cmd = [c for c in cmd if c]  # Remove empty
    else:
        return f"unknown formatter: {tool}"
    
    r = subprocess.run(cmd, capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "") or "formatting complete"


def security_check(
    path: str = ".",
    tool: str = "bandit"
) -> str:
    """Run security checks on Python code.
    
    Args:
        path: File or directory to check
        tool: Security tool ('bandit', 'safety')
    
    Returns:
        Security scan results.
    """
    if tool == "bandit":
        cmd = ["bandit", "-r", path]
    elif tool == "safety":
        cmd = ["safety", "check"]
    else:
        return f"unknown security tool: {tool}"
    
    r = subprocess.run(cmd, capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "")


# ============ Documentation Tools ============

def generate_docs(
    path: str = ".",
    output: str = "docs",
    tool: str = "pdoc"
) -> str:
    """Generate documentation from code.
    
    Args:
        path: Package or module path
        output: Output directory
        tool: Doc generator ('pdoc', 'pdoc3', 'mkdocs')
    
    Returns:
        Status message with output location.
    """
    if tool == "pdoc":
        cmd = ["pdoc", "-o", output, path]
    elif tool == "pdoc3":
        cmd = ["pdoc3", "--output-dir", output, path]
    elif tool == "mkdocs":
        cmd = ["mkdocs", "build", "-d", output]
    else:
        return f"unknown doc tool: {tool}"
    
    r = subprocess.run(cmd, capture_output=True, text=True)
    status = "completed" if r.returncode == 0 else "failed"
    return f"documentation {status}: {output}/\n" + (r.stdout or "") + (r.stderr or "")


def doc_preview(
    path: str,
    max_lines: int = 50
) -> str:
    """Preview docstrings and module documentation.
    
    Args:
        path: Python file to analyze
        max_lines: Max output lines
    
    Returns:
        Extracted docstrings and signatures.
    """
    import ast
    
    source = Path(path).read_text()
    tree = ast.parse(source)
    
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            name = node.name
            doc = ast.get_docstring(node)
            line = node.lineno
            
            if doc:
                preview = doc[:200].replace("\n", " ")
                if len(doc) > 200:
                    preview += "..."
                out.append(f"L{line}: {name} - {preview}")
            else:
                out.append(f"L{line}: {name} (no docstring)")
    
    out.sort(key=lambda x: int(x.split(":")[0][1:]))
    return "\n".join(out[:max_lines])


# ============ Utility Tools ============

def count_lines(
    path: str = ".",
    include_tests: bool = False
) -> Dict[str, int]:
    """Count lines of code by type.
    
    Args:
        path: Directory to analyze
        include_tests: Include test files
    
    Returns:
        Dict with code, blank, comment, and total counts.
    """
    from pathlib import Path
    
    stats = {"code": 0, "blank": 0, "comment": 0, "total": 0}
    
    for p in Path(path).rglob("*.py"):
        if not include_tests and ("test" in p.name or "test_" in str(p)):
            continue
            
        try:
            lines = p.read_text().splitlines()
            for line in lines:
                stats["total"] += 1
                stripped = line.strip()
                if not stripped:
                    stats["blank"] += 1
                elif stripped.startswith("#"):
                    stats["comment"] += 1
                else:
                    stats["code"] += 1
        except:
            pass
    
    return stats


def dependency_graph(
    path: str,
    output: str = "deps.png"
) -> str:
    """Generate dependency graph for Python module.
    
    Args:
        path: Python file or package
        output: Output image file
    
    Returns:
        Status message.
    """
    cmd = ["pydeps", path, "-o", output]
    r = subprocess.run(cmd, capture_output=True, text=True)
    
    if r.returncode == 0:
        return f"dependency graph saved to: {output}"
    return f"pydeps failed: {r.stderr}"


def code_stats(
    path: str = "."
) -> Dict[str, Any]:
    """Generate comprehensive code statistics.
    
    Args:
        path: Directory to analyze
    
    Returns:
        Dict with files, functions, classes, lines, etc.
    """
    import ast
    from pathlib import Path
    
    stats = {
        "files": 0,
        "functions": 0,
        "classes": 0,
        "imports": 0,
        "docstrings": 0,
        "lines": 0,
    }
    
    for p in Path(path).rglob("*.py"):
        if "__pycache__" in str(p):
            continue
            
        stats["files"] += 1
        
        try:
            source = p.read_text()
            stats["lines"] += len(source.splitlines())
            
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    stats["functions"] += 1
                    if ast.get_docstring(node):
                        stats["docstrings"] += 1
                elif isinstance(node, ast.ClassDef):
                    stats["classes"] += 1
                    if ast.get_docstring(node):
                        stats["docstrings"] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    stats["imports"] += 1
        except:
            pass
    
    return stats