"""Tech search tool."""

from typing import Any

from .base_search_tool import BaseSearchTool


class TechSearchTool(BaseSearchTool):
    """Technology and programming search tool.

    Suitable for finding technical documentation, programming resources, and tech news.
    Uses search engines with site-specific operators to avoid anti-bot detection.
    """

    # Search engine configurations for tech search
    ENGINES = [
        {
            "name": "Bing Stack Overflow",
            "url_template": "https://www.bing.com/search?q=site%3Astackoverflow.com+{query}&count={max_results}",
            "result_selector": ".b_algo",
            "title_selector": "h2 a",
            "abstract_selector": ".b_paractl",
        },
        {
            "name": "Bing GitHub",
            "url_template": "https://www.bing.com/search?q=site%3Agithub.com+{query}&count={max_results}",
            "result_selector": ".b_algo",
            "title_selector": "h2 a",
            "abstract_selector": ".b_paractl",
        },
        {
            "name": "Sogou",
            "url_template": "https://www.sogou.com/web?query=stackoverflow.com+OR+github.com+{query}&num={max_results}",
            "result_selector": ".vrwrap, .rb",
            "title_selector": "h3 a, .vr-title a",
            "abstract_selector": ".space-txt, .str_info",
        },
    ]

    def __init__(self, rate_limit: float = 1.0, timeout: int = 10):
        """Initialize tech search tool."""
        super().__init__(rate_limit=rate_limit, timeout=timeout)

    @property
    def name(self) -> str:
        """Tool name."""
        return "TechSearch"

    @property
    def description(self) -> str:
        """Tool description."""
        return "搜索技术文档、编程资源和科技资讯。"

    @property
    def parameters(self) -> dict[str, Any]:
        """Tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "要搜索的技术关键词",
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
        """Execute tech search using search engines.

        Engine fallback chain:
        - Bing Stack Overflow (主要)
        - Bing GitHub (备用)
        - Sogou (备用)
        - Baidu (最终兜底)
        """
        import asyncio
        from urllib.parse import quote

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

        # Final fallback: Baidu tech search
        try:
            return await self._search_baidu(query, max_results)
        except Exception as e:
            last_error = e

        if last_error:
            raise last_error
        return []

    async def _search_baidu(self, query: str, max_results: int) -> list[dict]:
        """Search using Baidu as final fallback."""
        import urllib.parse
        import requests
        from bs4 import BeautifulSoup

        encoded_query = urllib.parse.quote(f"技术 {query}")
        url = f"https://www.baidu.com/s?wd={encoded_query}&rn={max_results * 2}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        response = requests.get(url, headers=headers, timeout=self._timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for item in soup.select(".result.c-container, .result-op.c-container")[:max_results]:
            try:
                title_elem = item.select_one("h3 a")
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                raw_url = title_elem.get("href", "")

                abstract_elem = item.select_one(".c-abstract, .c-span-last p")
                abstract = abstract_elem.get_text(strip=True) if abstract_elem else "无摘要"

                if title and raw_url:
                    results.append({
                        "title": title,
                        "url": raw_url,
                        "abstract": f"[来源: 百度] {abstract}"
                    })
            except Exception:
                continue

        return results

    def _search_with_engine(self, query: str, max_results: int, engine: dict) -> list[dict]:
        """Search using a specific engine.

        Args:
            query: Search query string
            max_results: Maximum number of results
            engine: Engine configuration dictionary

        Returns:
            List of search results
        """
        import requests
        from bs4 import BeautifulSoup
        from urllib.parse import quote

        url = engine["url_template"].format(
            query=quote(query),
            max_results=max_results * 2
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

                # Add source indicator
                if "stackoverflow.com" in raw_url:
                    source = "Stack Overflow"
                elif "github.com" in raw_url:
                    source = "GitHub"
                else:
                    source = "技术搜索"

                if title and raw_url:
                    results.append({
                        "title": title,
                        "url": raw_url,
                        "abstract": f"{source} | {abstract}"
                    })
            except Exception:
                continue

        return results
