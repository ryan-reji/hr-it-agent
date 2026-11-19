
from src.policy_tool import search_company_policies

result = search_company_policies(
    "How many annual leave days does an employee receive?"
)

print("Found:", result["found"])
print("Context:", result.get("context", "None"))
print("Sources:", result["sources"])
