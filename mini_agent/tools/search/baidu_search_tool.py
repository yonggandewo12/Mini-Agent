"""Baidu search tool for Chinese network environment."""
import asyncio
from typing import Any
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup

from .base_search_tool import BaseSearchTool


def _is_safe_url(url: str) -> bool:
    """Validate URL is safe (only http/https, no dangerous schemes).

    Args:
        url: The URL to validate

    Returns:
        True if URL is safe, False otherwise
    """
    try:
        parsed = urlparse(url)
        # Only allow http and https schemes
        if parsed.scheme not in ("http", "https"):
            return False
        # Reject URLs with no netloc (e.g., javascript:, data:, etc.)
        if not parsed.netloc:
            return False
        return True
    except Exception:
        return False


class BaiduSearchTool(BaseSearchTool):
    """Tool for searching the web using Baidu (optimized for Chinese users)."""

    @property
    def name(self) -> str:
        """Tool name."""
        return "WebSearch"

    @property
    def description(self) -> str:
        """Tool description."""
        return "使用百度搜索互联网上的最新信息。适用于获取中文内容、当前事件、最新数据等不在训练数据中的信息。"

    @property
    def parameters(self) -> dict[str, Any]:
        """Tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "要搜索的关键词",
                    "minLength": 2,
                },
                "max_results": {
                    "type": "integer",
                    "description": "最多返回的搜索结果数量 (默认: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    async def _execute_search(self, query: str, max_results: int, **kwargs) -> list[dict]:
        """Execute Baidu search."""
        return await asyncio.to_thread(self._search_sync, query, max_results)

    def _search_sync(self, query: str, max_results: int) -> list[dict]:
        """Synchronous Baidu search implementation."""
        url = f"https://www.baidu.com/s?wd={quote(query)}&rn={max_results * 2}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }

        response = requests.get(url, headers=headers, timeout=self._timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        result_items = soup.select(".result.c-container, .result-op.c-container")

        for item in result_items[:max_results]:
            try:
                title_elem = item.select_one("h3 a")
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                raw_url = title_elem.get("href", "")

                # Validate URL before including in results
                if not _is_safe_url(raw_url):
                    continue

                abstract_elem = item.select_one(".c-abstract, .c-span-last p")
                abstract = abstract_elem.get_text(strip=True) if abstract_elem else "无摘要"

                if title and raw_url:
                    results.append({
                        "title": title,
                        "url": raw_url,
                        "abstract": abstract
                    })
            except Exception:
                continue

        return results
