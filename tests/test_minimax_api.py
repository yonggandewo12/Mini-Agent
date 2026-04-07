#!/usr/bin/env python3
"""Test script to verify MiniMax Token Plan API configuration works correctly"""

import asyncio
from mini_agent.config import Config
from mini_agent.llm import LLMClient
from mini_agent.schema import Message

async def test_api_call():
    """Test a simple API call to verify authentication works"""
    try:
        # Load configuration
        config = Config.load()
        print(f"Loaded configuration:")
        print(f"  Provider: {config.llm.provider}")
        print(f"  API Base: {config.llm.api_base}")
        print(f"  Model: {config.llm.model}")
        print(f"  API Key: {config.llm.api_key[:10]}... (masked)")

        # Create LLM client
        client = LLMClient(
            api_key=config.llm.api_key,
            provider=config.llm.provider,
            api_base=config.llm.api_base,
            model=config.llm.model,
        )
        print(f"\nFull API Base used: {client.api_base}")

        # Test simple message
        messages = [
            Message(role="user", content="Hello! Please respond with a simple 'Hello World!' message.")
        ]

        print("\nSending test request to MiniMax API...")
        response = await client.generate(messages)

        print(f"\n✅ Response received successfully!")
        print(f"  Content: {response.content}")
        print(f"  Finish reason: {response.finish_reason}")
        if response.usage:
            print(f"  Token usage: {response.usage.total_tokens} total tokens")

        print("\n🎉 401 authentication error fixed! The API key is now working correctly with MiniMax Token Plan.")
        return True

    except Exception as e:
        print(f"\n❌ Error occurred: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_api_call())
