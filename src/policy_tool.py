
from google.genai import types

from src.retrieval import retrieve_policy_context, format_sources


def search_company_policies(question: str) -> dict:
    """
    Search company policy documents using semantic retrieval.
    """
    results = retrieve_policy_context(question)

    if not results:
        return {
            "found": False,
            "message": "No relevant policy information was found.",
            "sources": []
        }

    context = "\n\n".join(
        f"Source: {item['filename']} | "
        f"Section: {item['section']}\n"
        f"{item['text']}"
        for item in results
    )

    return {
        "found": True,
        "context": context,
        "sources": format_sources(results)
    }


def get_policy_tool_declaration():
    return types.FunctionDeclaration(
        name="search_company_policies",
        description=(
            "Search company HR and IT policy documents. "
            "Use this for questions about leave, remote work, "
            "security, passwords, devices, and company rules."
        ),
        parameters_json_schema={
            "type": "OBJECT",
            "properties": {
                "question": {
                    "type": "STRING",
                    "description": "The policy question to search for."
                }
            },
            "required": ["question"]
        }
    )
