"""测试联网搜索功能"""
import asyncio
from pathlib import Path
from mini_agent import LLMClient
from mini_agent.agent import Agent
from mini_agent.config import Config
from mini_agent.tools import ReadTool, WriteTool, EditTool, BashTool, BaiduSearchTool

async def test_web_search():
    """测试联网搜索功能"""
    print("=" * 80)
    print("🚀 测试联网搜索功能")
    print("=" * 80)
    
    # 加载配置
    config_path = Path("mini_agent/config/config.yaml")
    config = Config.from_yaml(config_path)
    print(f"✅ 配置加载成功")
    print(f"   - API Base: {config.llm.api_base}")
    print(f"   - Model: {config.llm.model}")
    print(f"   - MCP Enabled: {config.tools.enable_mcp}")
    
    # 初始化 LLM 客户端
    llm_client = LLMClient(
        api_key=config.llm.api_key,
        api_base=config.llm.api_base,
        model=config.llm.model,
    )
    print("✅ LLM 客户端初始化成功")
    
    # 初始化工具
    tools = [
        ReadTool(workspace_dir="./workspace"),
        WriteTool(workspace_dir="./workspace"),
        EditTool(workspace_dir="./workspace"),
        BashTool(),
        BaiduSearchTool(),
    ]
    print("✅ 基础工具加载成功")
    
    # 创建 Agent
    agent = Agent(
        llm_client=llm_client,
        system_prompt="你是一个智能助手，可以帮助用户搜索互联网上的最新信息。",
        tools=tools,
        max_steps=10,
        workspace_dir="./workspace",
    )
    print("✅ Agent 创建成功\n")
    
    # 测试搜索任务
    task = "请搜索最新的科技新闻，告诉我3条最重要的科技新闻标题和简要内容"
    print(f"📝 测试任务: {task}\n")
    print("-" * 80)
    
    agent.add_user_message(task)
    
    try:
        result = await agent.run()
        print("\n" + "=" * 80)
        print("✅ 搜索完成！")
        print("=" * 80)
        print(result)
        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    success = await test_web_search()
    print("\n" + "=" * 80)
    if success:
        print("🎉 联网搜索功能测试成功！")
    else:
        print("⚠️  联网搜索功能测试失败")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
