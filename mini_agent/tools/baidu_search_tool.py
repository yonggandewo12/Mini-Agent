"""Baidu search tool for Chinese network environment."""
from typing import Any
import asyncio
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from .base import Tool, ToolResult


class BaiduSearchTool(Tool):
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

    async def execute(self, query: str, max_results: int = 5, **kwargs) -> ToolResult:
        """Execute the search query."""
        try:
            # Run search in thread pool to avoid blocking event loop
            results = await asyncio.to_thread(self._search_sync, query, max_results)

            if not results:
                return ToolResult(
                    success=True,
                    content="未找到相关搜索结果。",
                )

            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(
                    f"{i}. {result.get('title', '无标题')}\n"
                    f"   URL: {result.get('url', '无链接')}\n"
                    f"   摘要: {result.get('abstract', '无摘要')}\n"
                )

            return ToolResult(
                success=True,
                content="搜索结果:\n\n" + "\n".join(formatted_results),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"搜索失败: {str(e)}",
            )

    def _search_sync(self, query: str, max_results: int) -> list[dict]:
        """Synchronous Baidu search implementation."""
        # 百度搜索URL
        url = f"https://www.baidu.com/s?wd={quote(query)}&rn={max_results * 2}"  # 请求多一点结果，过滤无效的

        # 模拟浏览器请求头，避免被反爬
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }

        # 发送请求
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # 解析HTML
        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        # 查找搜索结果项
        result_items = soup.select(".result.c-container, .result-op.c-container")

        for item in result_items[:max_results]:
            try:
                # 提取标题
                title_elem = item.select_one("h3 a")
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)

                # 提取链接（百度跳转链接，实际链接需要处理，这里直接返回）
                raw_url = title_elem.get("href", "")

                # 提取摘要
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
