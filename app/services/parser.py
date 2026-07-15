from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable

from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {'.txt', '.md', '.csv', '.json', '.py', '.docx', '.pdf'}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        return ''
    if suffix in {'.txt', '.md', '.py'}:
        return path.read_text(encoding='utf-8', errors='ignore')
    if suffix == '.json':
        return json.dumps(json.loads(path.read_text(encoding='utf-8', errors='ignore')), indent=2)
    if suffix == '.csv':
        rows = []
        with path.open('r', encoding='utf-8', errors='ignore', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(' | '.join(row))
        return '\n'.join(rows)
    if suffix == '.docx':
        doc = Document(path)
        return '\n'.join(p.text for p in doc.paragraphs)
    if suffix == '.pdf':
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or '')
        return '\n'.join(pages)
    return ''


def iter_supported_files(root: Path) -> Iterable[Path]:
    for path in root.rglob('*'):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path
