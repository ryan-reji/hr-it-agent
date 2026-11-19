
-- Create the read-only role if it does not exist.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'hr_readonly'
    ) THEN
        CREATE ROLE hr_readonly LOGIN;
    END IF;
END
$$;

-- Set local development credentials.
ALTER ROLE hr_readonly
WITH LOGIN PASSWORD 'hr_readonly_password';

-- Database and schema permissions.
GRANT CONNECT ON DATABASE hr_it_helpdesk TO hr_readonly;
GRANT USAGE ON SCHEMA public TO hr_readonly;

-- Remove any previous table-level permissions.
REVOKE ALL PRIVILEGES
ON employees, leave_balances, it_tickets
FROM hr_readonly;

-- Employee profile: only non-sensitive columns.
GRANT SELECT (
    employee_id,
    full_name,
    department,
    designation,
    role,
    joining_date,
    employment_status
)
ON employees TO hr_readonly;

-- Leave information.
GRANT SELECT (
    employee_id,
    leave_type,
    annual_entitlement,
    used_days,
    remaining_days,
    year
)
ON leave_balances TO hr_readonly;

-- IT ticket information.
GRANT SELECT (
    ticket_id,
    employee_id,
    title,
    description,
    category,
    priority,
    status,
    created_at,
    updated_at
)
ON it_tickets TO hr_readonly;
