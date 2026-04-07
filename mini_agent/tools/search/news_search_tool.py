"""News search tool."""

from typing import Any

from .base_search_tool import BaseSearchTool


class NewsSearchTool(BaseSearchTool):
    """News and current events search tool.

    Suitable for finding recent news articles and media coverage.
    Engine fallback chain: Bing Web Search (reliable) -> Google News RSS -> DuckDuckGo News
    """

    @property
    def name(self) -> str:
        """Tool name."""
        return "NewsSearch"

    @property
    def description(self) -> str:
        """Tool description."""
        return "搜索新闻文章和时事报道，适用于获取最新资讯。"

    @property
    def parameters(self) -> dict[str, Any]:
        """Tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "要搜索的新闻关键词",
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
        """Execute news search with engine fallback."""
        # Try Bing Web Search first (most reliable in restricted environments)
        try:
            return await self._search_bing_web(query, max_results)
        except Exception:
            pass

        # Try Google News RSS
        try:
            return await self._search_google_news_rss(query, max_results)
        except Exception:
            pass

        # Try DuckDuckGo News
        try:
            return await self._search_duckduckgo_news(query, max_results)
        except Exception:
            pass

        # Final fallback: Baidu news search
        try:
            return await self._search_baidu_news(query, max_results)
        except Exception:
            pass

        return []

    async def _search_baidu_news(self, query: str, max_results: int) -> list[dict]:
        """Search using Baidu News as final fallback."""
        import urllib.parse
        import requests
        from bs4 import BeautifulSoup

        encoded_query = urllib.parse.quote(f"新闻 {query}")
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
                        "abstract": f"[来源: 百度新闻] {abstract}"
                    })
            except Exception:
                continue

        return results

    async def _search_bing_web(self, query: str, max_results: int) -> list[dict]:
        """Search using Bing Web Search (reliable fallback for news)."""
        import urllib.parse
        import requests
        from bs4 import BeautifulSoup

        encoded_query = urllib.parse.quote(query)
        # Use Bing web search with news-focused query
        search_url = f"https://www.bing.com/search?q={encoded_query}&mkt=en-US"

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        response = requests.get(search_url, headers=headers, timeout=self._timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        # Bing web search result structure
        for item in soup.select(".b_algo")[:max_results]:
            title_elem = item.select_one("h2 a")
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")

            abstract_elem = item.select_one(".b_paractl")
            abstract = abstract_elem.get_text(strip=True) if abstract_elem else "无摘要"

            # Try to get source from the URL domain
            if url:
                from urllib.parse import urlparse
                try:
                    domain = urlparse(url).netloc
                    if domain:
                        abstract = f"[来源: {domain}] {abstract}"
                except Exception:
                    pass

            if title:
                results.append({"title": title, "url": url, "abstract": abstract})

        return results

    async def _search_google_news_rss(self, query: str, max_results: int) -> list[dict]:
        """Search using Google News RSS feed."""
        import urllib.parse
        import requests
        from xml.etree import ElementTree as ET

        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"

        headers = {
            "Accept": "application/rss+xml, application/xml, text/xml",
            "User-Agent": "Mini-Agent/1.0 (news-search-tool)"
        }

        response = requests.get(rss_url, headers=headers, timeout=self._timeout)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        results = []

        for item in root.findall(".//item")[:max_results]:
            title_elem = item.find("title")
            title = title_elem.text.replace("<![CDATA[", "").replace("]]>", "").strip() if title_elem is not None else ""

            link_elem = item.find("link")
            url = link_elem.text.strip() if link_elem is not None and link_elem.text else ""

            desc_elem = item.find("description")
            desc_text = ""
            if desc_elem is not None and desc_elem.text:
                from bs4 import BeautifulSoup
                desc_text = BeautifulSoup(desc_elem.text, "html.parser").get_text()
                desc_text = desc_text.replace("<![CDATA[", "").replace("]]>", "").strip()

            pubdate_elem = item.find("pubDate")
            pubdate = pubdate_elem.text if pubdate_elem is not None and pubdate_elem.text else ""

            if title:
                abstract = f"[发布日期: {pubdate}] {desc_text}" if pubdate else desc_text
                abstract = abstract if abstract else "无摘要"
                results.append({"title": title, "url": url, "abstract": abstract})

        return results

    async def _search_duckduckgo_news(self, query: str, max_results: int) -> list[dict]:
        """Search using DuckDuckGo News HTML."""
        import urllib.parse
        import requests
        from bs4 import BeautifulSoup

        encoded_query = urllib.parse.quote(query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}+site%3Anews"

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        response = requests.get(search_url, headers=headers, timeout=self._timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for item in soup.select(".result")[:max_results]:
            title_elem = item.select_one(".result__a")
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")

            abstract_elem = item.select_one(".result__snippet")
            abstract = abstract_elem.get_text(strip=True) if abstract_elem else "无摘要"

            source_elem = item.select_one(".result__source")
            if source_elem:
                source = source_elem.get_text(strip=True)
                abstract = f"[来源: {source}] {abstract}"

            if title:
                results.append({"title": title, "url": url, "abstract": abstract})

        return results
