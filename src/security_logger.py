
import json
from datetime import datetime, timezone
from pathlib import Path

from src.guardrails import redact_pii


ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT_DIR / "logs"
LOG_FILE = LOG_DIR / "blocked_requests.jsonl"


def log_blocked_request(
    employee_id: str,
    request: str,
    category: str,
    reason: str
):
    """Append a security event to a JSONL file."""

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "employee_id": employee_id,
        "category": category,
        "reason": redact_pii(reason),
        "request": redact_pii(request)
    }

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")
