"""Test cases for tools."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from mini_agent.tools import BashTool, EditTool, ReadTool, WriteTool


@pytest.mark.asyncio
async def test_read_tool():
    """Test read file tool."""
    print("\n=== Testing ReadTool ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a temp file within the temp directory
        temp_file = Path(tmpdir) / "test.txt"
        temp_file.write_text("Hello, World!")

        # Use workspace_dir pointing to the temp directory
        tool = ReadTool(workspace_dir=tmpdir)
        result = await tool.execute(path=temp_file.name)

        assert result.success, f"Read failed: {result.error}"
        # ReadTool now returns content with line numbers in format: "LINE_NUMBER|LINE_CONTENT"
        assert "Hello, World!" in result.content, f"Content mismatch: {result.content}"
        assert "|Hello, World!" in result.content, f"Expected line number format: {result.content}"
        print("✅ ReadTool test passed")


@pytest.mark.asyncio
async def test_write_tool():
    """Test write file tool."""
    print("\n=== Testing WriteTool ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"

        # Use workspace_dir pointing to the temp directory
        tool = WriteTool(workspace_dir=tmpdir)
        result = await tool.execute(path=str(file_path), content="Test content")

        assert result.success, f"Write failed: {result.error}"
        assert file_path.exists(), "File was not created"
        assert file_path.read_text() == "Test content", "Content mismatch"
        print("✅ WriteTool test passed")


@pytest.mark.asyncio
async def test_edit_tool():
    """Test edit file tool."""
    print("\n=== Testing EditTool ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a temp file within the temp directory
        temp_file = Path(tmpdir) / "test.txt"
        temp_file.write_text("Hello, World!")

        # Use workspace_dir pointing to the temp directory
        tool = EditTool(workspace_dir=tmpdir)
        result = await tool.execute(
            path=str(temp_file), old_str="World", new_str="Agent"
        )

        assert result.success, f"Edit failed: {result.error}"
        content = temp_file.read_text()
        assert content == "Hello, Agent!", f"Content mismatch: {content}"
        print("✅ EditTool test passed")


@pytest.mark.asyncio
async def test_bash_tool():
    """Test bash command tool."""
    print("\n=== Testing BashTool ===")

    tool = BashTool()

    # Test successful command
    result = await tool.execute(command="echo 'Hello from bash'")
    assert result.success, f"Bash failed: {result.error}"
    assert "Hello from bash" in result.content, f"Output mismatch: {result.content}"
    print("✅ BashTool test passed")

    # Test failed command
    result = await tool.execute(command="exit 1")
    assert not result.success, "Command should have failed"
    print("✅ BashTool error handling test passed")


@pytest.mark.asyncio
async def test_path_traversal_protection():
    """Test that path traversal attacks are blocked."""
    print("\n=== Testing Path Traversal Protection ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "workspace"
        workspace.mkdir()

        # Create a file inside workspace
        safe_file = workspace / "safe.txt"
        safe_file.write_text("Safe content")

        # Create a file outside workspace
        outside_file = Path(tmpdir) / "outside.txt"
        outside_file.write_text("Outside content")

        tool = ReadTool(workspace_dir=str(workspace))

        # Should succeed - file is inside workspace
        result = await tool.execute(path=str(safe_file))
        assert result.success, f"Safe file access failed: {result.error}"
        print("✅ Safe file access passed")

        # Should fail - path traversal attempt with ../
        result = await tool.execute(path=str(workspace / ".." / "outside.txt"))
        assert not result.success, "Path traversal should be blocked"
        assert "Access denied" in result.error
        print("✅ Path traversal blocked")


@pytest.mark.asyncio
async def test_bash_command_validation():
    """Test that dangerous bash commands are blocked."""
    print("\n=== Testing Bash Command Validation ===")

    tool = BashTool()

    # These commands should be blocked
    dangerous_commands = [
        ("$(echo injected)", "command substitution"),
        ("`whoami`", "backtick command substitution"),
        ("echo test; rm -rf /", "command chaining with rm"),
        ("echo test | rm /", "pipe to rm"),
    ]

    for cmd, description in dangerous_commands:
        result = await tool.execute(command=cmd)
        assert not result.success, f"{description} should be blocked"
        assert "Potentially dangerous pattern detected" in result.error
        print(f"✅ {description} blocked")

    # These commands should succeed
    safe_commands = [
        "echo 'Hello World'",
        "ls -la",
        "pwd",
    ]

    for cmd in safe_commands:
        result = await tool.execute(command=cmd)
        assert result.success, f"Safe command failed: {cmd} - {result.error}"
        print(f"✅ Safe command allowed: {cmd}")


async def main():
    """Run all tool tests."""
    print("=" * 80)
    print("Running Tool Tests")
    print("=" * 80)

    await test_read_tool()
    await test_write_tool()
    await test_edit_tool()
    await test_bash_tool()
    await test_path_traversal_protection()
    await test_bash_command_validation()

    print("\n" + "=" * 80)
    print("All tool tests passed! ✅")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
