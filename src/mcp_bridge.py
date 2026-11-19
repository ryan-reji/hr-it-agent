
import os
import sys
from pathlib import Path
import asyncio

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env", override=True)

SERVER_PARAMETERS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "src.mcp_server"],
    env=os.environ.copy(),
    cwd=str(ROOT_DIR),
)


class MCPBridge:
    def __init__(self):
        self._stdio_context = None
        self._session_context = None
        self.session = None

    async def __aenter__(self):
        self._stdio_context = stdio_client(SERVER_PARAMETERS)
        read_stream, write_stream = await self._stdio_context.__aenter__()

        self._session_context = ClientSession(read_stream, write_stream)
        self.session = await self._session_context.__aenter__()

        await self.session.initialize()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._session_context:
            await self._session_context.__aexit__(
                exc_type, exc_value, traceback
            )

        if self._stdio_context:
            await self._stdio_context.__aexit__(
                exc_type, exc_value, traceback
            )

    async def list_tools(self):
        result = await self.session.list_tools()
        return result.tools

    async def call_tool(self, name, arguments):
        result = await self.session.call_tool(
            name,
            arguments=arguments
        )

        output = []

        for item in result.content:
            if hasattr(item, "text"):
                output.append(item.text)

        return {
            "content": output,
            "is_error": result.isError
        }
