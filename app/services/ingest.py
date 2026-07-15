from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict

from app.services.db import get_connection
from app.services.parser import extract_text, file_hash, iter_supported_files

DEPARTMENT_HINTS: Dict[str, str] = {
    'finance': 'Finance',
    'budget': 'Finance',
    'revenue': 'Finance',
    'hr': 'HR',
    'recruit': 'HR',
    'policy': 'HR',
    'it': 'IT',
    'server': 'IT',
    'deploy': 'IT',
    'marketing': 'Marketing',
    'campaign': 'Marketing',
    'launch': 'Marketing',
}


def infer_department(text: str, path: Path) -> str:
    sample = f"{path.as_posix().lower()} {text[:600].lower()}"
    for hint, dept in DEPARTMENT_HINTS.items():
        if hint in sample:
            return dept
    return 'General'


def infer_tags(path: Path, content: str) -> str:
    raw = f"{path.stem.lower()} {content[:600].lower()}"
    tags = []
    for token in ['budget', 'forecast', 'policy', 'recruitment', 'server', 'migration', 'launch', 'client', 'review', 'security', 'payroll']:
        if token in raw:
            tags.append(token)
    return ', '.join(sorted(set(tags)) or ['office'])


def ingest_workspace(workspace: str) -> dict:
    root = Path(workspace).resolve()
    if not root.exists():
        raise FileNotFoundError(f'Workspace not found: {root}')

    conn = get_connection()
    scanned = inserted = updated = 0

    for path in iter_supported_files(root):
        scanned += 1
        content = extract_text(path).strip()
        if not content:
            continue
        digest = file_hash(path)
        modified_at = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec='seconds')
        department = infer_department(content, path)
        tags = infer_tags(path, content)
        title = path.stem.replace('_', ' ').replace('-', ' ').title()
        existing = conn.execute('SELECT id, content_hash FROM documents WHERE path = ?', (str(path),)).fetchone()
        row = (
            title,
            str(path),
            path.suffix.lower().lstrip('.'),
            department,
            tags,
            'Local Workspace',
            content[:15000],
            path.stat().st_size,
            modified_at,
            datetime.now().isoformat(timespec='seconds'),
            digest,
        )
        if existing is None:
            conn.execute(
                """INSERT INTO documents
                   (title, path, file_type, department, tags, author, content, size_bytes, modified_at, indexed_at, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                row,
            )
            inserted += 1
        elif existing['content_hash'] != digest:
            conn.execute(
                """UPDATE documents SET
                   title=?, file_type=?, department=?, tags=?, author=?, content=?, size_bytes=?, modified_at=?, indexed_at=?, content_hash=?
                   WHERE path=?""",
                (
                    title,
                    path.suffix.lower().lstrip('.'),
                    department,
                    tags,
                    'Local Workspace',
                    content[:15000],
                    path.stat().st_size,
                    modified_at,
                    datetime.now().isoformat(timespec='seconds'),
                    digest,
                    str(path),
                ),
            )
            updated += 1

    conn.execute(
        'INSERT INTO ingestion_runs (workspace_path, scanned_count, inserted_count, updated_count) VALUES (?, ?, ?, ?)',
        (str(root), scanned, inserted, updated),
    )
    conn.commit()
    conn.close()
    return {'workspace': str(root), 'scanned': scanned, 'inserted': inserted, 'updated': updated}
