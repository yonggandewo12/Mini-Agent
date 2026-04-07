#!/usr/bin/env python3
"""Test that Baidu search tool is available in CLI"""

import subprocess
import sys

def test_cli_search():
    """Test that Baidu search is enabled in CLI"""
    # Run mini-agent with a test task that should use search
    cmd = [
        sys.executable, "-m", "mini_agent",
        "--task", "搜索胡歌的基本信息，简要回答",
        "--workspace", "/tmp"
    ]

    print(f"Running command: {' '.join(cmd)}")
    print("\nTesting CLI with search functionality...\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)

        print(f"\nReturn code: {result.returncode}")

        # Check if Baidu search tool is loaded
        if "✅ Loaded Baidu search tool" in result.stdout:
            print("\n✅ Baidu search tool is successfully loaded in CLI!")
        else:
            print("\n❌ Baidu search tool NOT found in CLI initialization")
            return False

        # Check if search was used
        if "search" in result.stdout.lower() or "百度" in result.stdout or "胡歌" in result.stdout:
            print("✅ Search functionality appears to be working")
        else:
            print("⚠️  Search may not have been triggered in this test")

        return True

    except subprocess.TimeoutExpired:
        print("\n❌ Test timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"\n❌ Error running test: {e}")
        return False

if __name__ == "__main__":
    success = test_cli_search()
    sys.exit(0 if success else 1)
