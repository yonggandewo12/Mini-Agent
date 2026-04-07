"""Academic search tool."""

from typing import Any

from .base_search_tool import BaseSearchTool


class AcademicSearchTool(BaseSearchTool):
    """Academic and research paper search tool.

    Suitable for scholarly articles, papers, and research materials.
    Engine: Semantic Scholar API (reliable and free)
    """

    @property
    def name(self) -> str:
        """Tool name."""
        return "AcademicSearch"

    @property
    def description(self) -> str:
        """Tool description."""
        return "搜索学术论文、研究报告和学术文献。"

    @property
    def parameters(self) -> dict[str, Any]:
        """Tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "要搜索的学术关键词",
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
        """Execute academic search using Semantic Scholar API with Baidu fallback."""
        try:
            return await self._search_semantic_scholar(query, max_results)
        except Exception:
            # Fallback: try arXiv if Semantic Scholar fails
            try:
                return await self._search_arxiv(query, max_results)
            except Exception:
                pass

        # Final fallback: use Baidu search with academic keywords
        try:
            return await self._search_baidu(query, max_results)
        except Exception:
            pass

        return []

    async def _search_semantic_scholar(self, query: str, max_results: int) -> list[dict]:
        """Search using Semantic Scholar API."""
        import urllib.parse
        import requests

        encoded_query = urllib.parse.quote(query)
        api_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_query}&limit={max_results}&fields=title,url,abstract,authors,year"

        headers = {
            "Accept": "application/json",
            "User-Agent": "Mini-Agent/1.0 (academic-search-tool)"
        }

        response = requests.get(api_url, headers=headers, timeout=self._timeout)
        response.raise_for_status()

        data = response.json()
        results = []

        for paper in data.get("data", []):
            title = paper.get("title", "")
            url = paper.get("url", "")
            abstract = paper.get("abstract") or "无摘要"
            authors = paper.get("authors", [])
            year = paper.get("year", "")

            # Format author list
            author_names = [a.get("name", "") for a in authors[:3]] if authors else []
            author_str = ", ".join(author_names) if author_names else "未知作者"

            # Add year and authors to abstract
            extra_info = f"[年份: {year}] [作者: {author_str}]" if year else f"[作者: {author_str}]"
            full_abstract = f"{extra_info} {abstract}" if abstract != "无摘要" else abstract

            if title:
                results.append({"title": title, "url": url, "abstract": full_abstract})

        return results

    async def _search_arxiv(self, query: str, max_results: int) -> list[dict]:
        """Search using arXiv API as fallback."""
        import urllib.parse
        import requests

        encoded_query = urllib.parse.quote(query)
        # Use arXiv's Atom API
        api_url = f"http://export.arxiv.org/api/query?search_query=ti:{encoded_query}+OR+all:{encoded_query}&max_results={max_results}"

        headers = {
            "Accept": "application/atom+xml",
            "User-Agent": "Mini-Agent/1.0 (academic-search-tool)"
        }

        response = requests.get(api_url, headers=headers, timeout=self._timeout)
        response.raise_for_status()

        # Parse Atom XML response
        from xml.etree import ElementTree as ET
        root = ET.fromstring(response.text)

        # Define namespaces
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom"
        }

        results = []
        for entry in root.findall("atom:entry", ns)[:max_results]:
            title = entry.find("atom:title", ns)
            title_text = title.text.replace("\n", " ").strip() if title is not None else ""

            link = entry.find("atom:link[@title='pdf']", ns)
            url = link.get("href", "") if link is not None else ""

            summary = entry.find("atom:summary", ns)
            abstract = summary.text.replace("\n", " ").strip()[:500] + "..." if summary is not None else "无摘要"

            published = entry.find("atom:published", ns)
            year = published.text[:4] if published is not None else ""

            if title_text:
                extra_info = f"[年份: {year}] [来源: arXiv]" if year else "[来源: arXiv]"
                results.append({
                    "title": title_text,
                    "url": url,
                    "abstract": f"{extra_info} {abstract}"
                })

        return results

    async def _search_baidu(self, query: str, max_results: int) -> list[dict]:
        """Search using Baidu as final fallback."""
        import urllib.parse
        import requests
        from bs4 import BeautifulSoup

        encoded_query = urllib.parse.quote(f"学术 {query}")
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
