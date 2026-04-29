"""Web tools — re-exports from toolslm + custom fetch
Mirrors solveit's web capabilities.
"""
from __future__ import annotations
from toolslm.download import read_md, read_html, read_docs, html2md, find_docs
from typing import List, Dict, Optional
import httpx
# Import httpx types for forward references in read_md
from httpx._types import QueryParamTypes, HeaderTypes, CookieTypes, AuthTypes, ProxyTypes, TimeoutTypes

__all__ = [
    "read_md",
    "read_html",
    "read_docs",
    "html2md",
    "find_docs",
    "fetch",
    "fetch_json",
    "fetch_bytes",
    "web_search",
]


def fetch(url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> str:
    """Fetch raw text content of URL (no parsing).
    
    Use `read_html` or `html2md` to convert to markdown.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        headers: Optional custom headers
    
    Returns:
        Raw text content
    """
    default_headers = {"User-Agent": "toolbox/0.2"}
    if headers:
        default_headers.update(headers)
    
    r = httpx.get(
        url,
        timeout=timeout,
        follow_redirects=True,
        headers=default_headers
    )
    r.raise_for_status()
    return r.text


def fetch_json(url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> Dict:
    """GET URL and return parsed JSON.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        headers: Optional custom headers
    
    Returns:
        Parsed JSON as dict
    """
    default_headers = {"User-Agent": "toolbox/0.2"}
    if headers:
        default_headers.update(headers)
    
    r = httpx.get(
        url,
        timeout=timeout,
        follow_redirects=True,
        headers=default_headers
    )
    r.raise_for_status()
    return r.json()


def fetch_bytes(url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> bytes:
    """Fetch raw binary content from URL.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        headers: Optional custom headers
    
    Returns:
        Raw bytes content
    """
    default_headers = {"User-Agent": "toolbox/0.2"}
    if headers:
        default_headers.update(headers)
    
    r = httpx.get(
        url,
        timeout=timeout,
        follow_redirects=True,
        headers=default_headers
    )
    r.raise_for_status()
    return r.content


def web_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Search the web via DuckDuckGo HTML.
    
    Args:
        query: Search query
        max_results: Maximum results to return (default: 10)
    
    Returns:
        List of dicts with title, url, snippet for each result.
    """
    from urllib.parse import quote_plus
    from bs4 import BeautifulSoup
    
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    
    r = httpx.post(
        url,
        headers={"User-Agent": "Mozilla/5.0 toolbox/0.2"},
        timeout=30,
        follow_redirects=True
    )
    
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    
    for res in soup.select(".result")[:max_results]:
        a = res.select_one(".result__a")
        snip = res.select_one(".result__snippet")
        
        if a:
            out.append({
                "title": a.get_text(strip=True),
                "url": a.get("href", ""),
                "snippet": snip.get_text(strip=True) if snip else "",
            })
    
    return out