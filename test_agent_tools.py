
import asyncio
from src.mcp_bridge import MCPBridge
from src.agent_tools import convert_mcp_tools


async def main():
    async with MCPBridge() as bridge:
        mcp_tools = await bridge.list_tools()
        gemini_tools = convert_mcp_tools(mcp_tools)

        print("Gemini tool adapter created successfully!")
        for declaration in gemini_tools.function_declarations:
            print("-", declaration.name)


if __name__ == "__main__":
    asyncio.run(main())
