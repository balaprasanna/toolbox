"""GitHub tools — re-exports from toolslm + ghapi wrappers
Mirrors solveit's GitHub capabilities.
"""
from toolslm.xml import repo2ctx, folder2ctx, parse_gh_url
from typing import Optional, List, Dict, Any

__all__ = [
    "repo2ctx",
    "folder2ctx",
    "parse_gh_url",
    "gh_repo",
    "gh_pr",
    "gh_issue",
    "gh_search_code",
    "gh_list_files",
    "gh_read_file",
]


def _api(token: Optional[str] = None):
    """Internal: get ghapi instance."""
    from ghapi.all import GhApi
    return GhApi(token=token)


def gh_repo(owner: str, repo: Optional[str] = None, token: Optional[str] = None) -> Dict[str, Any]:
    """Get GitHub repo metadata.
    
    Args:
        owner: Owner name (or 'owner/repo' if repo is None)
        repo: Repository name
        token: Optional GitHub token for private repos
    
    Returns:
        Dict with name, full_name, description, default_branch,
        stargazers_count, forks_count, language, topics, open_issues_count, etc.
    """
    if repo is None and "/" in owner:
        owner, repo = owner.split("/", 1)
    
    r = _api(token).repos.get(owner, repo)
    return {
        k: r[k]
        for k in (
            "name", "full_name", "description", "default_branch",
            "stargazers_count", "forks_count", "language", "topics",
            "open_issues_count", "homepage", "license"
        )
        if k in r
    }


def gh_pr(
    owner: str,
    repo: Optional[str] = None,
    pr_number: Optional[int] = None,
    with_diff: bool = True,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """Get GitHub PR details.
    
    Args:
        owner: Owner name (or 'owner/repo' if repo is None)
        repo: Repository name
        pr_number: PR number
        with_diff: Include diff text (default: True)
        token: Optional GitHub token
    
    Returns:
        Dict with title, body, state, user, head, base, merged, mergeable, and optionally diff.
    """
    import httpx
    
    if repo is None and "/" in owner:
        owner, repo = owner.split("/", 1)
    
    api = _api(token)
    pr = api.pulls.get(owner, repo, pr_number)
    
    out = {
        k: pr[k]
        for k in ("title", "body", "state", "user", "head", "base", "merged", "mergeable")
        if k in pr
    }
    
    if with_diff:
        url = pr.get("diff_url")
        if url:
            out["diff"] = httpx.get(url, follow_redirects=True, timeout=30).text
    
    return out


def gh_issue(
    owner: str,
    repo: Optional[str] = None,
    issue_number: Optional[int] = None,
    with_comments: bool = False,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """Get GitHub issue details.
    
    Args:
        owner: Owner name (or 'owner/repo' if repo is None)
        repo: Repository name
        issue_number: Issue number
        with_comments: Include comments list
        token: Optional GitHub token
    
    Returns:
        Dict with title, body, state, user, labels, and optionally comments.
    """
    if repo is None and "/" in owner:
        owner, repo = owner.split("/", 1)
    
    api = _api(token)
    iss = api.issues.get(owner, repo, issue_number)
    
    out = {
        k: iss[k]
        for k in ("title", "body", "state", "user", "labels")
        if k in iss
    }
    
    if with_comments:
        comments = api.issues.list_comments(owner, repo, issue_number)
        out["comments"] = [
            {"user": c["user"]["login"], "body": c["body"]}
            for c in comments
        ]
    
    return out


def gh_search_code(
    query: str,
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    token: Optional[str] = None
) -> List[Dict[str, str]]:
    """Search code on GitHub.
    
    Args:
        query: Search query
        owner: Optional owner to restrict to
        repo: Optional repo to restrict to (requires owner)
        token: Optional GitHub token
    
    Returns:
        List of dicts with path, repo, url for each match.
    """
    api = _api(token)
    q = query
    if owner and repo:
        q += f" repo:{owner}/{repo}"
    elif owner:
        q += f" user:{owner}"
    
    res = api.search.code(q)
    return [
        {
            "path": i["path"],
            "repo": i["repository"]["full_name"],
            "url": i["html_url"]
        }
        for i in res.get("items", [])
    ]


def gh_list_files(
    owner: str,
    repo: Optional[str] = None,
    path: str = "",
    ref: Optional[str] = None,
    token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List files in a GitHub repo directory.
    
    Args:
        owner: Owner name (or 'owner/repo' if repo is None)
        repo: Repository name
        path: Directory path (default: root)
        ref: Branch/tag/commit (default: default branch)
        token: Optional GitHub token
    
    Returns:
        List of file/directory entries with name, type, size, download_url.
    """
    if repo is None and "/" in owner:
        owner, repo = owner.split("/", 1)
    
    api = _api(token)
    args = {"owner": owner, "repo": repo, "path": path}
    if ref:
        args["ref"] = ref
    
    contents = api.repos.get_content(**args)
    if not isinstance(contents, list):
        contents = [contents]
    
    return [
        {
            "name": c["name"],
            "type": c["type"],
            "path": c["path"],
            "size": c.get("size", 0),
            "download_url": c.get("download_url"),
        }
        for c in contents
    ]


def gh_read_file(
    owner: str,
    repo: Optional[str] = None,
    path: str = "",
    ref: Optional[str] = None,
    token: Optional[str] = None
) -> str:
    """Read file content from GitHub.
    
    Args:
        owner: Owner name (or 'owner/repo' if repo is None)
        repo: Repository name
        path: File path in repo
        ref: Branch/tag/commit (default: default branch)
        token: Optional GitHub token
    
    Returns:
        File content as text.
    """
    import base64
    
    if repo is None and "/" in owner:
        owner, repo = owner.split("/", 1)
    
    api = _api(token)
    args = {"owner": owner, "repo": repo, "path": path}
    if ref:
        args["ref"] = ref
    
    content = api.repos.get_content(**args)
    
    if isinstance(content, list):
        raise ValueError(f"{path} is a directory, not a file")
    
    if content.get("encoding") == "base64":
        return base64.b64decode(content["content"]).decode("utf-8")
    return content.get("content", "")