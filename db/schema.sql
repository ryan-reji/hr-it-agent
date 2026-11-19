-- Add database schema here.

CREATE TABLE IF NOT EXISTS employees (
    employee_id VARCHAR(10) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(20),
    department VARCHAR(80) NOT NULL,
    designation VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'employee'
        CHECK (role IN ('employee', 'manager', 'hr')),
    salary NUMERIC(12, 2),
    joining_date DATE NOT NULL,
    employment_status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (employment_status IN ('active', 'inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leave_balances (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(10) NOT NULL
        REFERENCES employees(employee_id) ON DELETE CASCADE,
    leave_type VARCHAR(30) NOT NULL,
    annual_entitlement INTEGER NOT NULL CHECK (annual_entitlement >= 0),
    used_days NUMERIC(5, 1) NOT NULL DEFAULT 0
        CHECK (used_days >= 0),
    remaining_days NUMERIC(5, 1)
        GENERATED ALWAYS AS (annual_entitlement - used_days) STORED,
    year INTEGER NOT NULL,
    UNIQUE (employee_id, leave_type, year),
    CHECK (used_days <= annual_entitlement)
);

CREATE TABLE IF NOT EXISTS it_tickets (
    ticket_id SERIAL PRIMARY KEY,
    employee_id VARCHAR(10) NOT NULL
        REFERENCES employees(employee_id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium'
        CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(30) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_leave_employee
    ON leave_balances(employee_id);

CREATE INDEX IF NOT EXISTS idx_tickets_employee
    ON it_tickets(employee_id);

CREATE INDEX IF NOT EXISTS idx_tickets_status
    ON it_tickets(status);
