from __future__ import annotations

from app.services.db import get_connection

# Demo users across every department represented in workspace_docs.
# Each tuple is: (name, role, department, team, preferred_file_type)
USERS = [
    ('Sara Khan', 'Financial Analyst', 'Finance', 'Revenue Ops', 'pdf'),
    ('Ali Raza', 'HR Manager', 'HR', 'People Success', 'docx'),
    ('Usman Tariq', 'Platform Engineer', 'IT', 'Infrastructure', 'md'),
    ('Mariam Noor', 'Marketing Lead', 'Marketing', 'Growth', 'pptx'),
    ('Bilal Ahmed', 'Enterprise Sales Director', 'Sales', 'Enterprise', 'md'),
    ('Hina Farooq', 'Compliance Officer', 'Legal', 'Compliance', 'pdf'),
    ('Zain Malik', 'Data Engineer', 'IT', 'Infrastructure', 'json'),
    ('Ayesha Siddiqui', 'Recruiter', 'HR', 'People Success', 'csv'),
]


def seed_users() -> None:
    conn = get_connection()
    conn.executemany(
        'INSERT INTO users (name, role, department, team, preferred_file_type) VALUES (?, ?, ?, ?, ?)',
        USERS,
    )
    conn.commit()
    conn.close()
