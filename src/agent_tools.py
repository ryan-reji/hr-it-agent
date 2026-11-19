
from google.genai import types


def convert_mcp_tools(mcp_tools):
    """
    Convert MCP tool definitions into Gemini function declarations.
    """
    declarations = []

    for tool in mcp_tools:
        declaration = types.FunctionDeclaration(
            name=tool.name,
            description=tool.description or f"Call {tool.name}",
            parameters_json_schema=tool.inputSchema
        )

        declarations.append(declaration)

    return types.Tool(function_declarations=declarations)
