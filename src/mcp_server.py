
import os
from pathlib import Path
from typing import Optional

import sys
import traceback

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv("MCP_DATABASE_URL")
CURRENT_USER_ID = os.getenv("CURRENT_USER_ID", "").strip().upper()

if not DATABASE_URL:
    raise ValueError("MCP_DATABASE_URL is missing.")

if not CURRENT_USER_ID:
    raise ValueError("CURRENT_USER_ID is missing.")


# --------------------------------------------------
# MCP SERVER
# --------------------------------------------------

mcp = FastMCP("HR-IT-Helpdesk")


def get_connection():
    """Connect using the dedicated read-only account."""

    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
        connect_timeout=5
    )


# --------------------------------------------------
# ACCESS CONTROL
# --------------------------------------------------

def check_employee_access(conn, target_employee_id):
    """
    Verify the authenticated employee's database role.

    Employees: Access only their own records.
    Managers: Access employee records.
    HR: Access employee records.

    The caller identity comes from server configuration,
    never from arguments supplied by the LLM.
    """

    target_employee_id = target_employee_id.strip().upper()

    with conn.cursor() as cursor:

        cursor.execute(
            """
            SELECT employee_id, role
            FROM employees
            WHERE employee_id = %s
            """,
            (CURRENT_USER_ID,)
        )

        current_user = cursor.fetchone()

        if not current_user:
            return "Authenticated employee does not exist."

        cursor.execute(
            """
            SELECT employee_id
            FROM employees
            WHERE employee_id = %s
            """,
            (target_employee_id,)
        )

        target = cursor.fetchone()

        if not target:
            return "Requested employee does not exist."

        role = current_user["role"]

        if role not in ("manager", "hr"):
            if target_employee_id != CURRENT_USER_ID:
                return "Access denied. You can only access your own records."

    return None


# --------------------------------------------------
# TOOL 1: LEAVE BALANCE
# --------------------------------------------------

@mcp.tool()
def get_leave_balance(
    employee_id: str,
    leave_type: Optional[str] = None
) -> dict:
    """
    Retrieve annual and sick leave balances.

    Args:
        employee_id: Employee identifier such as E101.
        leave_type: Optional annual or sick filter.
    """

    if not employee_id or not employee_id.strip():
        return {"error": "Employee ID is required."}

    if leave_type and leave_type not in ("annual", "sick"):
        return {"error": "Leave type must be annual or sick."}

    query = """
        SELECT
            employee_id,
            leave_type,
            annual_entitlement,
            used_days::float AS used_days,
            remaining_days::float AS remaining_days,
            year
        FROM leave_balances
        WHERE employee_id = %s
    """

    params = [employee_id.strip().upper()]

    if leave_type:
        query += " AND leave_type = %s"
        params.append(leave_type)

    query += " ORDER BY year DESC, leave_type"

    try:
        with get_connection() as conn:

            access_error = check_employee_access(
                conn, employee_id
            )

            if access_error:
                return {"error": access_error}

            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

        if not rows:
            return {
                "employee_id": employee_id,
                "message": "No leave records found."
            }

        return {
            "employee_id": employee_id.strip().upper(),
            "balances": [dict(row) for row in rows]
        }

    except psycopg.Error as e:
        print(f"LEAVE BALANCE DATABASE ERROR: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {"error": "Unable to retrieve leave records."}


# --------------------------------------------------
# TOOL 2: EMPLOYEE PROFILE
# --------------------------------------------------

@mcp.tool()
def get_employee_profile(employee_id: str) -> dict:
    """
    Retrieve non-sensitive employee profile information.

    Salary, email and phone are excluded at database
    permission level as well as application level.
    """

    if not employee_id or not employee_id.strip():
        return {"error": "Employee ID is required."}

    query = """
        SELECT
            employee_id,
            full_name,
            department,
            designation,
            role,
            joining_date::text AS joining_date,
            employment_status
        FROM employees
        WHERE employee_id = %s
    """

    try:
        with get_connection() as conn:

            access_error = check_employee_access(
                conn, employee_id
            )

            if access_error:
                return {"error": access_error}

            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (employee_id.strip().upper(),)
                )

                row = cursor.fetchone()

        if not row:
            return {"error": "Employee not found."}

        return dict(row)

    except psycopg.Error:
        return {"error": "Unable to retrieve employee profile."}


# --------------------------------------------------
# TOOL 3: IT TICKETS
# --------------------------------------------------

@mcp.tool()
def list_it_tickets(employee_id: str) -> dict:
    """
    Retrieve IT support tickets belonging to an employee.
    """

    if not employee_id or not employee_id.strip():
        return {"error": "Employee ID is required."}

    query = """
        SELECT
            ticket_id,
            title,
            description,
            category,
            priority,
            status,
            created_at::text AS created_at,
            updated_at::text AS updated_at
        FROM it_tickets
        WHERE employee_id = %s
        ORDER BY created_at DESC
    """

    try:
        with get_connection() as conn:

            access_error = check_employee_access(
                conn, employee_id
            )

            if access_error:
                return {"error": access_error}

            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (employee_id.strip().upper(),)
                )

                rows = cursor.fetchall()

        return {
            "employee_id": employee_id.strip().upper(),
            "ticket_count": len(rows),
            "tickets": [dict(row) for row in rows]
        }

    except psycopg.Error:
        return {"error": "Unable to retrieve IT tickets."}


# --------------------------------------------------
# START MCP SERVER
# --------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
