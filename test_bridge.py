import asyncio
from src.mcp_bridge import MCPBridge


async def main():
    async with MCPBridge() as bridge:
        tools = await bridge.list_tools()

        print("\nConnected MCP tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")


if __name__ == "__main__":
    asyncio.run(main())