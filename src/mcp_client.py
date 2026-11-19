
import os
import sys
import json
import asyncio

from pathlib import Path
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(ROOT_DIR / ".env")

SERVER_PARAMETERS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "src.mcp_server"],
    env=os.environ.copy()
)


# --------------------------------------------------
# RESULT HANDLING
# --------------------------------------------------

def parse_tool_result(result):

    if result.isError:
        raise RuntimeError("MCP tool execution failed.")

    # Prefer structured results when available.
    if result.structuredContent is not None:
        return result.structuredContent

    output = []

    for item in result.content:

        if hasattr(item, "text"):

            try:
                output.append(json.loads(item.text))

            except json.JSONDecodeError:
                output.append(item.text)

    if len(output) == 1:
        return output[0]

    return output


# --------------------------------------------------
# MCP CONNECTION AND TOOL EXECUTION
# --------------------------------------------------

async def run_mcp_client():

    print("\nHR & IT HELPDESK - MCP CLIENT")
    print("=" * 40)

    async with stdio_client(
        SERVER_PARAMETERS,
        errlog=sys.stderr
    ) as (
        read_stream,
        write_stream
    ):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            # Initialize connection.
            await session.initialize()

            print("\nConnected to MCP server.")

            # Discover available tools.
            tools_response = await session.list_tools()

            print("\nAvailable MCP tools:")

            for tool in tools_response.tools:
                print(f"- {tool.name}: {tool.description}")

            # Interactive testing.
            while True:

                print("\nChoose a tool:")
                print("1. Get leave balance")
                print("2. Get employee profile")
                print("3. List IT tickets")
                print("4. Exit")

                choice = input("\nChoice: ").strip()

                if choice == "4":
                    print("Closing MCP client.")
                    break

                employee_id = input(
                    "Employee ID: "
                ).strip().upper()

                if choice == "1":

                    leave_type = input(
                        "Leave type (annual/sick/blank for all): "
                    ).strip().lower()

                    arguments = {
                        "employee_id": employee_id
                    }

                    if leave_type:
                        arguments["leave_type"] = leave_type

                    tool_name = "get_leave_balance"

                elif choice == "2":

                    arguments = {
                        "employee_id": employee_id
                    }

                    tool_name = "get_employee_profile"

                elif choice == "3":

                    arguments = {
                        "employee_id": employee_id
                    }

                    tool_name = "list_it_tickets"

                else:
                    print("Invalid choice.")
                    continue

                try:

                    result = await session.call_tool(
                        tool_name,
                        arguments
                    )

                    parsed = parse_tool_result(result)

                    print("\nMCP RESPONSE")
                    print("-" * 40)

                    print(
                        json.dumps(
                            parsed,
                            indent=4,
                            default=str
                        )
                    )

                except Exception as error:

                    print(
                        "\nMCP execution failed:",
                        str(error)
                    )


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":

    try:
        asyncio.run(run_mcp_client())

    except KeyboardInterrupt:
        print("\nClient stopped.")
