from __future__ import annotations

from app.services.db import get_connection

USERS = [
    ('Sara Khan', 'Financial Analyst', 'Finance', 'Revenue Ops', 'pdf'),
    ('Ali Raza', 'HR Manager', 'HR', 'People Success', 'docx'),
    ('Usman Tariq', 'Platform Engineer', 'IT', 'Infrastructure', 'md'),
    ('Mariam Noor', 'Marketing Lead', 'Marketing', 'Growth', 'pptx'),
]


def seed_users() -> None:
    conn = get_connection()
    conn.executemany(
        'INSERT INTO users (name, role, department, team, preferred_file_type) VALUES (?, ?, ?, ?, ?)',
        USERS,
    )
    conn.commit()
    conn.close()
