#!/usr/bin/env python3
"""Test Baidu search functionality"""

import asyncio
from mini_agent.tools.search.baidu_search_tool import BaiduSearchTool

async def test_search():
    """Test searching for 胡歌 information"""
    search_tool = BaiduSearchTool()

    print("正在搜索胡歌的信息...")
    result = await search_tool.execute(query="胡歌 个人资料 最新信息", max_results=5)

    if result.success:
        print("\n✅ 搜索成功！\n")
        print(result.content)
    else:
        print(f"\n❌ 搜索失败: {result.error}")

    return result.success

if __name__ == "__main__":
    asyncio.run(test_search())
