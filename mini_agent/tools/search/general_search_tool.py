"""General search tool with multi-engine fallback support."""
from typing import Any

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

from .base_search_tool import BaseSearchTool


class GeneralSearchTool(BaseSearchTool):
    """General search tool with multi-engine fallback.

    Search engine priority chain:
    1. Bing (primary)
    2. 360 Search (backup 1)
    3. Sogou Search (backup 2)
    4. DuckDuckGo (backup 3)
    """

    # Search engine configurations
    ENGINES = [
        {
            "name": "Bing",
            "url_template": "https://www.bing.com/search?q={query}&count={max_results}",
            "result_selector": ".b_algo",
            "title_selector": "h2 a",
            "abstract_selector": ".b_paractl",
        },
        {
            "name": "360",
            "url_template": "https://www.so.com/s?q={query}&pn=1&rn={max_results}",
            "result_selector": ".res-list",
            "title_selector": "h3 a",
            "abstract_selector": ".res-desc",
        },
        {
            "name": "Sogou",
            "url_template": "https://www.sogou.com/web?query={query}&num={max_results}",
            "result_selector": ".vrwrap, .rb",
            "title_selector": "h3 a, .vr-title a",
            "abstract_selector": ".space-txt, .str_info",
        },
        {
            "name": "DuckDuckGo",
            "url_template": "https://html.duckduckgo.com/html/?q={query}",
            "result_selector": ".result",
            "title_selector": ".result__a",
            "abstract_selector": ".result__snippet",
        },
        {
            "name": "Baidu",
            "url_template": "https://www.baidu.com/s?wd={query}&rn={max_results}",
            "result_selector": ".result.c-container, .result-op.c-container",
            "title_selector": "h3 a",
            "abstract_selector": ".c-abstract, .c-span-last p",
        },
    ]

    def __init__(self, rate_limit: float = 1.0, timeout: int = 10):
        """Initialize general search tool.

        Args:
            rate_limit: Minimum seconds between requests (default: 1.0)
            timeout: Request timeout in seconds (default: 10)
        """
        super().__init__(rate_limit=rate_limit, timeout=timeout)

    @property
    def name(self) -> str:
        """Tool name."""
        return "GeneralSearch"

    @property
    def description(self) -> str:
        """Tool description."""
        return "通用网络搜索工具，自动切换多个搜索引擎以获取最新信息。支持 Bing、360搜索、搜狗搜索和 DuckDuckGo。当某个引擎失败时会自动尝试下一个引擎。"

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
        """Execute search with multi-engine fallback.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            **kwargs: Additional parameters

        Returns:
            List of result dictionaries with 'title', 'url', 'abstract' keys
        """
        import asyncio

        last_error = None

        for engine in self.ENGINES:
            try:
                results = await asyncio.to_thread(
                    self._search_with_engine, query, max_results, engine
                )
                if results:
                    return results
            except Exception as e:
                last_error = e
                continue

        # All engines failed
        if last_error:
            raise last_error
        return []

    def _search_with_engine(self, query: str, max_results: int, engine: dict) -> list[dict]:
        """Search using a specific engine.

        Args:
            query: Search query string
            max_results: Maximum number of results
            engine: Engine configuration dictionary

        Returns:
            List of search results
        """
        url = engine["url_template"].format(
            query=quote(query),
            max_results=max_results * 2  # Request more to filter invalid results
        )

        response = requests.get(
            url,
            headers=self.DEFAULT_HEADERS,
            timeout=self._timeout
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        result_items = soup.select(engine["result_selector"])

        for item in result_items[:max_results]:
            try:
                title_elem = item.select_one(engine["title_selector"])
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                raw_url = title_elem.get("href", "")

                abstract_elem = item.select_one(engine["abstract_selector"])
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
