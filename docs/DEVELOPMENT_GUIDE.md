# Development Guide

## Table of Contents

- [Development Guide](#development-guide)
  - [Table of Contents](#table-of-contents)
  - [1. Project Architecture](#1-project-architecture)
  - [2. Basic Usage](#2-basic-usage)
    - [2.0 Streaming Output Mode](#20-streaming-output-mode)
    - [2.1 Interactive Commands](#21-interactive-commands)
    - [2.2 Integrated MCP Tools](#22-integrated-mcp-tools)
      - [Memory - Knowledge Graph Memory System](#memory---knowledge-graph-memory-system)
      - [MiniMax Search - Web Search and Browse](#minimax-search---web-search-and-browse)
  - [3. Extended Abilities](#3-extended-abilities)
    - [3.1 Adding Custom Tools](#31-adding-custom-tools)
      - [Steps](#steps)
      - [Example](#example)
    - [3.2 Adding MCP Tools](#32-adding-mcp-tools)
    - [3.3 Customizing Note Storage](#33-customizing-note-storage)
    - [3.4 Initialize Claude Skills (Recommended)](#34-initialize-claude-skills-recommended)
    - [3.5 Adding a New Skill](#35-adding-a-new-skill)
    - [3.6 Customizing System Prompt](#36-customizing-system-prompt)
      - [What You Can Customize](#what-you-can-customize)
  - [4. Troubleshooting](#4-troubleshooting)
    - [4.1 Common Issues](#41-common-issues)
      - [API Key Configuration Error](#api-key-configuration-error)
      - [Dependency Installation Failure](#dependency-installation-failure)
      - [MCP Tool Loading Failure](#mcp-tool-loading-failure)
    - [4.2 Debugging Tips](#42-debugging-tips)
      - [Enable Verbose Logging](#enable-verbose-logging)
      - [Using the Python Debugger](#using-the-python-debugger)
      - [Inspecting Tool Calls](#inspecting-tool-calls)

---

## 1. Project Architecture

```
mini-agent/
├── mini_agent/              # Core source code
│   ├── agent.py             # Main agent loop
│   ├── llm.py               # LLM client
│   ├── cli.py               # Command-line interface
│   ├── config.py            # Configuration loading
│   ├── tools/               # Tool implementations (file, bash, MCP, skills, etc.)
│   └── skills/              # Claude Skills (submodule)
├── tests/                   # Test code
├── docs/                    # Documentation
├── workspace/               # Working directory
└── pyproject.toml           # Project configuration
```

## 2. Basic Usage

### 2.0 Streaming Output Mode

Mini Agent supports **real-time streaming output** that displays AI responses as they are generated. This provides a faster, more interactive experience especially for long responses.

#### Command Line Options

| Flag | Description |
|------|-------------|
| `--stream` or `-s` | Enable streaming output mode |
| `--task` or `-t` | Execute a task non-interactively |

#### Usage Examples

```bash
# Interactive mode with streaming (real-time feedback)
mini-agent --stream
mini-agent -s

# Non-interactive task execution with streaming
mini-agent --stream --task "Create a Python script"
mini-agent -s -t "Create a Python script"

# Default mode (non-streaming, waits for complete response)
mini-agent
mini-agent --task "Create a Python script"
```

#### How Streaming Works

When streaming is enabled:

1. **Real-time token display**: AI response tokens appear immediately as they are generated
2. **Thinking process**: The model's reasoning/thinking is displayed in real-time (if enabled by the model)
3. **Tool calls**: Tool execution results are displayed after the streaming completes
4. **Same functionality**: All features work identically to non-streaming mode

#### Implementation Details

The streaming feature is implemented across several files:

| File | Role |
|------|------|
| `mini_agent/cli.py` | Parses `--stream` flag and passes to Agent |
| `mini_agent/llm/base.py` | Abstract `generate_stream()` method in base LLM client |
| `mini_agent/llm/openai_client.py` | OpenAI-compatible streaming implementation |
| `mini_agent/llm/anthropic_client.py` | Anthropic SDK streaming implementation |
| `mini_agent/agent.py` | `_stream_response()` method for streaming output |

#### Programmatic Usage

You can also use streaming programmatically in your own code:

```python
from mini_agent.agent import Agent

# Create agent with streaming enabled
agent = Agent(
    llm_client=llm_client,
    system_prompt=system_prompt,
    tools=tools,
    stream=True  # Enable streaming
)

# Or pass stream parameter to run()
await agent.run(stream=True)
```

### 2.1 Interactive Commands

When running the agent in interactive mode (`mini-agent`), the following commands are available:

| Command                | Description                                                 |
| ---------------------- | ----------------------------------------------------------- |
| `/exit`, `/quit`, `/q` | Exit the agent and display session statistics               |
| `/help`                | Display help information and available commands             |
| `/clear`               | Clear message history and start a new session               |
| `/history`             | Show the current session message count                      |
| `/stats`               | Display session statistics (steps, tool calls, tokens used) |

### 2.2 Integrated MCP Tools

This project comes with pre-configured MCP (Model Context Protocol) tools that extend the agent's capabilities:

#### Memory - Knowledge Graph Memory System

**Function**: Provides long-term memory storage and retrieval based on graph database

**Status**: Enabled by default (`disabled: false`)

**Configuration**: No API Key required, works out of the box

**Capabilities**:
- Store and retrieve information across sessions
- Build knowledge graphs from conversations
- Semantic search through stored memories

---

#### MiniMax Search - Web Search and Browse

**Function**: Provides three powerful tools:
- `search` - Web search capability
- `parallel_search` - Execute multiple searches simultaneously
- `browse` - Intelligent web browsing and content extraction

**Status**: Disabled by default, needs configuration to enable

**Configuration Example**

```json
{
  "mcpServers": {
    "minimax_search": {
      "disabled": false,
      "env": {
        "JINA_API_KEY": "your-jina-api-key",
        "SERPER_API_KEY": "your-serper-api-key",
        "MINIMAX_TOKEN": "your-minimax-token"
      }
    }
  }
}
```

## 3. Extended Abilities

### 3.1 Adding Custom Tools

#### Steps

1.  Create a new tool file under `mini_agent/tools/`.
2.  Inherit from the `Tool` base class.
3.  Implement the required properties and methods.
4.  Register the tool during Agent initialization.

#### Example

```python
# mini_agent/tools/my_tool.py
from mini_agent.tools.base import Tool, ToolResult
from typing import Dict, Any

class MyTool(Tool):
    @property
    def name(self) -> str:
        """A unique name for the tool."""
        return "my_tool"
    
    @property
    def description(self) -> str:
        """A description for the LLM to understand the tool's purpose."""
        return "My custom tool for doing something useful"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """Parameter schema in JSON Schema format."""
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "First parameter"
                },
                "param2": {
                    "type": "integer",
                    "description": "Second parameter",
                    "default": 10
                }
            },
            "required": ["param1"]
        }
    
    async def execute(self, param1: str, param2: int = 10) -> ToolResult:
        """
        The main logic of the tool.
        
        Args:
            param1: The first parameter.
            param2: The second parameter, with a default value.
        
        Returns:
            A ToolResult object.
        """
        try:
            # Implement your logic here
            result = f"Processed {param1} with param2={param2}"
            
            return ToolResult(
                success=True,
                content=result
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Error: {str(e)}"
            )

# In cli.py or agent initialization code
from mini_agent.tools.my_tool import MyTool

# Add the new tool when creating the Agent
tools = [
    ReadTool(workspace_dir),
    WriteTool(workspace_dir),
    MyTool(),  # Add your custom tool
]

agent = Agent(
    llm=llm,
    tools=tools,
    max_steps=50
)
```

### 3.2 Adding Search Tools

The project includes a **search tools framework** in `mini_agent/tools/search/` that provides multiple specialized search tools with multi-engine fallback support.

#### Available Search Tools

| Tool | Purpose | Engine Chain |
|------|---------|--------------|
| `GeneralSearchTool` | General web search | Bing → 360 → Sogou → DuckDuckGo → **Baidu** |
| `AcademicSearchTool` | Academic papers & research | Semantic Scholar → arXiv → **Baidu** |
| `NewsSearchTool` | News articles | Bing → Google News RSS → DuckDuckGo → **Baidu** |
| `EcommerceSearchTool` | Product search | Bing(Taobao) → Bing(JD) → Sogou → **Baidu** |
| `SocialSearchTool` | Social media content | Bing(Weibo) → Bing(WeChat) → Sogou → **Baidu** |
| `TechSearchTool` | Tech Q&A & code | Bing(StackOverflow) → Bing(GitHub) → Sogou → **Baidu** |

> **Note:** Baidu search serves as the **final fallback** for all search tools, ensuring maximum coverage even when other engines fail.

#### BaseSearchTool Features

All search tools inherit from `BaseSearchTool` which provides:
- **Async HTTP requests** with thread pool
- **Browser User-Agent伪装** to avoid bot detection
- **Retry decorator** (3 attempts with exponential backoff)
- **Rate limiting** to prevent request flooding
- **HTML parsing** with BeautifulSoup
- **Multi-engine fallback** - automatic failover when primary engine fails

#### Creating a New Search Tool

```python
from .base_search_tool import BaseSearchTool

class MySearchTool(BaseSearchTool):
    """Custom search tool with multi-engine support."""

    ENGINES = [
        {
            "name": "PrimaryEngine",
            "url_template": "https://example.com/search?q={query}",
            "result_selector": ".result-item",
            "title_selector": "h3 a",
            "abstract_selector": ".description",
        },
        {
            "name": "BackupEngine",
            "url_template": "https://backup.com/search?q={query}",
            "result_selector": ".item",
            "title_selector": ".title a",
            "abstract_selector": ".summary",
        },
    ]

    @property
    def name(self) -> str:
        return "MySearch"

    @property
    def description(self) -> str:
        return "搜索我的自定义内容"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "max_results": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        }

    async def _execute_search(self, query: str, max_results: int, **kwargs) -> list[dict]:
        """Execute search with engine fallback."""
        for engine in self.ENGINES:
            try:
                results = await self._search_with_engine(query, max_results, engine)
                if results:
                    return results
            except Exception:
                continue
        return []
```

#### Registering Search Tools

Add to `cli.py` `add_workspace_tools()` function:

```python
from mini_agent.tools.search import MySearchTool
tools.append(MySearchTool())
```

### 3.3 Adding MCP Tools

Edit `mcp.json` to add a new MCP Server:

```json
{
  "mcpServers": {
    "my_custom_mcp": {
      "description": "My custom MCP server",
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@my-org/my-mcp-server"],
      "env": {
        "API_KEY": "your-api-key"
      },
      "disabled": false,
      "notes": {
        "description": "This is a custom MCP server.",
        "api_key_url": "https://example.com/api-keys"
      }
    }
  }
}
```

### 3.4 Customizing Note Storage

To replace the storage backend for the `SessionNoteTool`:

```python
# Current implementation: JSON file
class SessionNoteTool:
    def __init__(self, memory_file: str = "./workspace/.agent_memory.json"):
        self.memory_file = Path(memory_file)
    
    async def _save_notes(self, notes: List[Dict]):
        with open(self.memory_file, 'w') as f:
            json.dump(notes, f, indent=2, ensure_ascii=False)

# Example extension: PostgreSQL
class PostgresNoteTool(Tool):
    def __init__(self, db_url: str):
        self.db = PostgresDB(db_url)
    
    async def _save_notes(self, notes: List[Dict]):
        await self.db.execute(
            "INSERT INTO notes (content, category, timestamp) VALUES ($1, $2, $3)",
            notes
        )

# Example extension: Vector Database
class MilvusNoteTool(Tool):
    def __init__(self, milvus_host: str):
        self.vector_db = MilvusClient(host=milvus_host)
    
    async def _save_notes(self, notes: List[Dict]):
        # Generate embeddings
        embeddings = await self.get_embeddings([n["content"] for n in notes])
        
        # Store in the vector database
        await self.vector_db.insert(
            collection="agent_notes",
            data=notes,
            embeddings=embeddings
        )
```

### 3.5 Initialize Claude Skills (Recommended) 

This project integrates Claude's official skills repository via git submodule. Initialize it after first clone:

```bash
# Initialize submodule
git submodule update --init --recursive
```

Skills provide 20+ professional capabilities, making the Agent work like a professional:

- 📄 **Document Processing**: Create and edit PDF, DOCX, XLSX, PPTX
- 🎨 **Design Creation**: Generate artwork, posters, GIF animations
- 🧪 **Development & Testing**: Web automation testing (Playwright), MCP server development
- 🏢 **Enterprise Applications**: Internal communication, brand guidelines, theme customization

✨ **This is one of the core highlights of this project.** For details, see the "Configure Skills" section below.

**More information:**

- [Claude Skills Official Documentation](https://docs.claude.com/zh-CN/docs/agents-and-tools/agent-skills)
- [Anthropic Blog: Equipping agents for the real world](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

### 3.6 Adding a New Skill

Create a custom Skill:

```bash
# Create a new skill directory under skills/
mkdir skills/my-custom-skill
cd skills/my-custom-skill

# Create the SKILL.md file
cat > SKILL.md << 'EOF'
---
name: my-custom-skill
description: My custom skill for handling specific tasks.
---

# Overview

This skill provides the following capabilities:
- Capability 1
- Capability 2

# Usage

1. Step one...
2. Step two...

# Best Practices

- Practice 1
- Practice 2

# FAQ

Q: Question 1
A: Answer 1
```

The new Skill will be automatically loaded and recognized by the Agent.

### 3.7 Customizing System Prompt

The system prompt (`system_prompt.md`) defines the Agent's behavior, capabilities, and working guidelines. You can customize it to tailor the Agent for specific use cases.

#### What You Can Customize

1. **Core Capabilities**: Add or modify tool descriptions
2. **Working Guidelines**: Define custom workflows and best practices
3. **Domain-Specific Knowledge**: Add expertise in specific areas
4. **Communication Style**: Adjust how the Agent interacts with users
5. **Task Priorities**: Set preferences for how tasks should be approached

After modifying `system_prompt.md`, be sure to restart the Agent to apply changes

## 4. Troubleshooting

### 4.1 Common Issues

#### API Key Configuration Error

```bash
# Error message
Error: Invalid API key

# Solution
1. Check that the API key in `config.yaml` is correct.
2. Ensure there are no extra spaces or quotes.
3. Verify that the API key has not expired.
```

#### Dependency Installation Failure

```bash
# Error message
uv sync failed

# Solution
1. Update uv to the latest version: `uv self update`
2. Clear the cache: `uv cache clean`
3. Try syncing again: `uv sync`
```

#### MCP Tool Loading Failure

```bash
# Error message
Failed to load MCP server

# Solution
1. Check the configuration in `mcp.json` is correct.
2. Ensure Node.js is installed (required for most MCP tools).
3. Verify that any required API keys are configured.
4. View detailed logs: `pytest tests/test_mcp.py -v -s`
```

### 4.2 Debugging Tips

#### Enable Verbose Logging

```python
# At the beginning of cli.py or a test file
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### Using the Python Debugger

```python
# Set a breakpoint in your code
import pdb; pdb.set_trace()

# Or use ipdb for a better experience
import ipdb; ipdb.set_trace()
```

#### Inspecting Tool Calls

```python
# Add logging in the Agent to see tool interactions
logger.debug(f"Tool call: {tool_call.name}")
logger.debug(f"Tool arguments: {tool_call.arguments}")
logger.debug(f"Tool result: {result.content[:200]}")
```
