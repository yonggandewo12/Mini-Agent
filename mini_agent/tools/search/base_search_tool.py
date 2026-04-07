"""Base search tool with common functionality."""

import asyncio
import time
from abc import abstractmethod
from functools import wraps
from typing import Any

import requests
from bs4 import BeautifulSoup

from ..base import Tool, ToolResult


def retry(max_attempts: int = 3, delay: float = 1.0):
    """Retry decorator for handling transient failures.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (attempt + 1))
            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class RateLimiter:
    """Simple rate limiter for API requests.

    Ensures minimum time interval between requests.
    """

    def __init__(self, min_interval: float = 1.0):
        """Initialize rate limiter.

        Args:
            min_interval: Minimum seconds between requests
        """
        self._min_interval = min_interval
        self._last_request_time = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait if necessary to satisfy rate limit."""
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_request_time = time.time()


class BaseSearchTool(Tool):
    """Abstract base class for search tools.

    Provides common functionality:
    - Async HTTP requests with thread pool
    - Browser-like headers for anti-bot detection
    - Retry decorator for resilience
    - Rate limiting
    - HTML parsing with BeautifulSoup
    - Standardized result formatting
    """

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    }

    def __init__(self, rate_limit: float = 1.0, timeout: int = 10):
        """Initialize base search tool.

        Args:
            rate_limit: Minimum seconds between requests (default: 1.0)
            timeout: Request timeout in seconds (default: 10)
        """
        self._rate_limiter = RateLimiter(min_interval=rate_limit)
        self._timeout = timeout

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """Tool parameters schema."""
        pass

    @abstractmethod
    async def _execute_search(self, query: str, max_results: int, **kwargs) -> list[dict]:
        """Execute the actual search. Must be implemented by subclasses.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            **kwargs: Additional search-specific parameters

        Returns:
            List of result dictionaries with 'title', 'url', 'abstract' keys
        """
        pass

    async def execute(self, query: str, max_results: int = 5, **kwargs) -> ToolResult:  # type: ignore
        """Execute the search query with common error handling.

        Args:
            query: Search query string
            max_results: Maximum number of results (default: 5)
            **kwargs: Additional search-specific parameters

        Returns:
            ToolResult with success status and formatted content or error
        """
        try:
            await self._rate_limiter.acquire()
            results = await self._execute_search(query, max_results, **kwargs)

            if not results:
                return ToolResult(success=True, content="未找到相关搜索结果。")

            formatted_results = self._format_results(results)
            return ToolResult(success=True, content=formatted_results)

        except Exception as e:
            return ToolResult(success=False, error=f"搜索失败: {str(e)}")

    def _format_results(self, results: list[dict]) -> str:
        """Format search results into a readable string.

        Args:
            results: List of result dictionaries

        Returns:
            Formatted string with numbered results
        """
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(
                f"{i}. {result.get('title', '无标题')}\n"
                f"   URL: {result.get('url', '无链接')}\n"
                f"   摘要: {result.get('abstract', '无摘要')}\n"
            )
        return "搜索结果:\n\n" + "\n".join(formatted)

    def _fetch_html(self, url: str, headers: dict | None = None) -> BeautifulSoup:
        """Fetch and parse HTML from a URL.

        Args:
            url: URL to fetch
            headers: Optional custom headers (merged with DEFAULT_HEADERS)

        Returns:
            BeautifulSoup object for parsing
        """
        request_headers = self.DEFAULT_HEADERS.copy()
        if headers:
            request_headers.update(headers)

        response = requests.get(url, headers=request_headers, timeout=self._timeout)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    @retry(max_attempts=3, delay=1.0)
    def _fetch_html_with_retry(self, url: str, headers: dict | None = None) -> BeautifulSoup:
        """Fetch HTML with automatic retry on failure.

        Args:
            url: URL to fetch
            headers: Optional custom headers

        Returns:
            BeautifulSoup object for parsing
        """
        return self._fetch_html(url, headers)

    def _parse_search_result_item(self, item: BeautifulSoup, selectors: dict) -> dict | None:
        """Parse a single search result item using CSS selectors.

        Args:
            item: BeautifulSoup element representing a result item
            selectors: Dict with 'title', 'url', 'abstract' CSS selectors

        Returns:
            Parsed result dict or None if parsing fails
        """
        try:
            title_elem = item.select_one(selectors.get("title", "h3 a"))
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            raw_url = title_elem.get("href", "")

            abstract_elem = item.select_one(selectors.get("abstract", ".c-abstract"))
            abstract = abstract_elem.get_text(strip=True) if abstract_elem else "无摘要"

            if title and raw_url:
                return {"title": title, "url": raw_url, "abstract": abstract}

            return None
        except Exception:
            return None
