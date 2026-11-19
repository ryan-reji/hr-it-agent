-- Add seed data here.

INSERT INTO employees (
    employee_id, full_name, email, phone,
    department, designation, role, salary, joining_date
)
VALUES
('E101', 'Aarav Mehta', 'aarav.mehta@example.com',
 '9876501001', 'Engineering', 'Software Engineer',
 'employee', 850000, '2023-06-12'),

('E102', 'Priya Sharma', 'priya.sharma@example.com',
 '9876501002', 'Finance', 'Financial Analyst',
 'employee', 920000, '2022-08-15'),

('E103', 'Rahul Nair', 'rahul.nair@example.com',
 '9876501003', 'Engineering', 'Engineering Manager',
 'manager', 1500000, '2021-03-10'),

('E104', 'Sneha Kapoor', 'sneha.kapoor@example.com',
 '9876501004', 'Human Resources', 'HR Specialist',
 'hr', 1100000, '2022-01-20'),

('E105', 'Arjun Desai', 'arjun.desai@example.com',
 '9876501005', 'IT Support', 'IT Support Engineer',
 'employee', 780000, '2024-02-05'),

('E106', 'Neha Iyer', 'neha.iyer@example.com',
 '9876501006', 'Marketing', 'Marketing Executive',
 'employee', 820000, '2023-09-18')

ON CONFLICT (employee_id) DO NOTHING;


INSERT INTO leave_balances (
    employee_id, leave_type, annual_entitlement,
    used_days, year
)
VALUES
-- E101
('E101', 'annual', 24, 8, 2026),
('E101', 'sick', 12, 2, 2026),

-- E102
('E102', 'annual', 24, 14, 2026),
('E102', 'sick', 12, 3, 2026),

-- E103
('E103', 'annual', 24, 5, 2026),
('E103', 'sick', 12, 1, 2026),

-- E104
('E104', 'annual', 24, 10, 2026),
('E104', 'sick', 12, 4, 2026),

-- E105
('E105', 'annual', 24, 6, 2026),
('E105', 'sick', 12, 0, 2026),

-- E106
('E106', 'annual', 24, 12, 2026),
('E106', 'sick', 12, 2, 2026)

ON CONFLICT (employee_id, leave_type, year) DO NOTHING;


INSERT INTO it_tickets (
    employee_id, title, description,
    category, priority, status
)
VALUES
('E101', 'VPN connection failure',
 'Unable to connect to the corporate VPN from home.',
 'network', 'high', 'in_progress'),

('E101', 'IDE installation request',
 'Requesting installation of approved development tools.',
 'software', 'low', 'open'),

('E102', 'Email synchronization issue',
 'Outlook is not synchronizing recent emails.',
 'email', 'medium', 'open'),

('E103', 'Laptop performance issue',
 'Laptop performance has degraded during development work.',
 'hardware', 'medium', 'resolved'),

('E104', 'HR portal access',
 'Unable to access the internal HR portal.',
 'access', 'high', 'in_progress'),

('E105', 'Printer connectivity',
 'Office printer is not appearing on the network.',
 'hardware', 'low', 'closed'),

('E106', 'Password reset request',
 'Unable to log into the marketing dashboard.',
 'access', 'medium', 'open')

ON CONFLICT DO NOTHING;
