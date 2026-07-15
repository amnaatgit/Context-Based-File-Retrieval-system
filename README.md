# Context-Aware Office File Retrieval Pro

A more advanced version of the project with a better UI, real folder ingestion, stronger retrieval logic, and clearer DSA/DBMS storytelling for a semester project, portfolio, or LinkedIn post.

## What is improved

- Real file ingestion from a local folder
- Better search ranking with BM25-style scoring
- Context-aware re-ranking by user department, team, file preference, recency, and access history
- Autocomplete using a trie
- Faster repeat searches using an LRU cache
- Filter by department and file type
- Dashboard metrics and score explainability
- Cleaner, more aesthetic frontend

## DSA used

1. **Hash Map / Dictionary** for inverted index and metadata lookup
2. **Set operations** for candidate retrieval
3. **Trie** for autocomplete
4. **Heap / Priority Queue** for top-k results
5. **LRU Cache** for repeated searches
6. **Counter / Frequency tables** for BM25-style ranking

## DBMS used

- **SQLite**
- Tables: `users`, `documents`, `access_logs`, `ingestion_runs`

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe scripts\ingest_demo_files.py
.\.venv\Scripts\python.exe scripts\run.py
```

Open `http://127.0.0.1:8000`

## Demo queries

- `budget`
- `client review`
- `recruitment`
- `leave policy`
- `migration`
- `server deployment`
