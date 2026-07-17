# Context-Aware Office File Retrieval Pro

A context-aware document search engine for an office workspace. It ingests real files from department folders, ranks them with a BM25-style scorer, and then re-ranks results based on **who** is searching — their department, team, file-type preference, recency needs, and past access history. It is built to showcase practical Data Structures & Algorithms (DSA) and Database (DBMS) concepts for a semester project, portfolio, or demo.

**Live demo:** https://context-based-file-retrieval-system.vercel.app

---

## What makes it "context-aware"

A normal search engine returns the same results for everyone. This system adjusts ranking to the person searching:

- A **Finance** user searching `budget` sees finance documents boosted.
- A user who prefers **PDF** files sees PDFs ranked slightly higher.
- **Recently modified** documents get a freshness boost.
- Documents the user (or their team) **opened before** are boosted from access history.

The result is that the same query can return a different, more relevant order for each user.

---

## Demo data (start here)

The repository ships with a ready-to-use demo workspace so you can see exactly how retrieval behaves without adding your own files. This is the fastest way to understand the system.

### Demo documents

Sample documents live in `workspace_docs/`, organized by department. They are written to look like real office files (budgets, policies, playbooks, proposals) so search results feel realistic:

| Department | Example documents |
| --- | --- |
| Finance | Annual financial statement, Q1 budget report, expense policy, client review budget notes |
| HR | Leave policy, performance review guide, onboarding checklist, recruitment pipeline |
| IT | API documentation, cloud infrastructure overview, server migration plan, incident playbook, security policy |
| Marketing | Q2 campaign brief, social media strategy, brand guidelines |
| Sales | Enterprise sales playbook, client proposal (TechConnect) |
| Legal | Data privacy policy |
| General | Company handbook |

Supported file types: `.txt`, `.md`, `.csv`, `.json`, `.py`, `.docx`, `.pdf`.

### Demo users

Seed users represent every department so you can test context-aware ranking (defined in `app/services/seed.py`):

| Name | Role | Department | Prefers |
| --- | --- | --- | --- |
| Sara Khan | Financial Analyst | Finance | pdf |
| Ali Raza | HR Manager | HR | docx |
| Usman Tariq | Platform Engineer | IT | md |
| Mariam Noor | Marketing Lead | Marketing | pptx |
| Bilal Ahmed | Enterprise Sales Director | Sales | md |
| Hina Farooq | Compliance Officer | Legal | pdf |
| Zain Malik | Data Engineer | IT | json |
| Ayesha Siddiqui | Recruiter | HR | csv |

### Try these demo queries

Run the same query as different users and watch the order change:

- `budget` — strongest for Sara Khan (Finance)
- `leave policy` — strongest for Ali Raza / Ayesha Siddiqui (HR)
- `server migration` — strongest for Usman Tariq / Zain Malik (IT)
- `campaign` — strongest for Mariam Noor (Marketing)
- `client proposal` — strongest for Bilal Ahmed (Sales)
- `data privacy` — strongest for Hina Farooq (Legal)
- `recruitment`, `incident`, `security`, `onboarding`

---

## How it works

1. **Ingestion** reads every supported file under `workspace_docs/`, extracts text, infers a department and tags, computes a content hash, and stores each document in the database.
2. **Indexing** builds an inverted index (word -> documents) in memory for fast lookup, plus a trie for autocomplete.
3. **Retrieval** tokenizes the query, expands it with synonyms, finds candidate documents via set operations, and scores them with a BM25-style ranking.
4. **Context re-ranking** adjusts each candidate's score using the current user's department, team, preferred file type, document recency, and access history.
5. **Top-K** results are selected with a heap and returned with a short explanation of why each document ranked where it did.
6. **Logging** records each search and document open in the database to power analytics and future context.

---

## Features

- Real file ingestion from a local folder
- BM25-style relevance scoring with synonym expansion
- Context-aware re-ranking (department, team, file preference, recency, access history)
- Autocomplete powered by a trie
- Faster repeat searches with an LRU cache
- Filters for department and file type
- Score explainability (why a document ranked where it did)
- Export search results to CSV with one click
- Related documents suggestions based on shared tags, department, and file type
- Dashboard metrics: total documents, searches, top queries, most-opened files
- Clean, responsive web UI

---

## Tech: DSA and DBMS

**Data structures / algorithms**
- Hash map / dictionary — inverted index and metadata lookup
- Set operations — candidate retrieval
- Trie — autocomplete
- Heap / priority queue — top-K results
- LRU cache — repeated searches
- Counter / frequency tables — BM25-style ranking

**Database**
- PostgreSQL in production (SQLite-compatible schema for local use)
- Tables: `users`, `documents`, `access_logs`, `search_logs`, `bookmarks`, `ingestion_runs`

---

## Project structure

```
app/
  main.py              FastAPI app entry point
  routes/web.py        Web and API routes
  search/engine.py     Retrieval + context re-ranking
  search/structures.py Trie and LRU cache
  services/db.py       Database connection
  services/ingest.py   Folder ingestion
  services/parser.py   Text extraction per file type
  services/seed.py     Demo users
  models/              SQL schema (SQLite + PostgreSQL)
  templates/           HTML templates
  static/css/          Styles
scripts/
  init_db.py           Create tables and seed users
  ingest_demo_files.py Ingest the demo workspace
  run.py               Start the local server
workspace_docs/        Demo documents by department
```

---

## Setup (local)

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe scripts\ingest_demo_files.py
.\.venv\Scripts\python.exe scripts\run.py
```

```bash
# macOS / Linux
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/init_db.py
.venv/bin/python scripts/ingest_demo_files.py
.venv/bin/python scripts/run.py
```

Then open http://127.0.0.1:8000

The database connection is read from the `DATABASE_URL` (or `POSTGRES_URL`) environment variable. See `.env.example` for the expected format.

---

## Adding your own documents

Drop files into any `workspace_docs/<department>/` folder (or create a new department folder), then re-run `scripts/ingest_demo_files.py`. The ingester will index new files, update changed ones (detected via content hash), and skip unchanged files.
# Context-Aware Office File Retrieval Pro

A context-aware document search engine for an office workspace. It ingests real files from department folders, ranks them with a BM25-style scorer, and then re-ranks results based on **who** is searching â their department, team, file-type preference, recency needs, and past access history. It is built to showcase practical Data Structures & Algorithms (DSA) and Database (DBMS) concepts for a semester project, portfolio, or demo.

**Live demo:** https://context-based-file-retrieval-system.vercel.app

---

## What makes it "context-aware"

A normal search engine returns the same results for everyone. This system adjusts ranking to the person searching:

- A **Finance** user searching `budget` sees finance documents boosted.
- A user who prefers **PDF** files sees PDFs ranked slightly higher.
- **Recently modified** documents get a freshness boost.
- Documents the user (or their team) **opened before** are boosted from access history.

The result is that the same query can return a different, more relevant order for each user.

---

## Demo data (start here)

The repository ships with a ready-to-use demo workspace so you can see exactly how retrieval behaves without adding your own files. This is the fastest way to understand the system.

### Demo documents

Sample documents live in `workspace_docs/`, organized by department. They are written to look like real office files (budgets, policies, playbooks, proposals) so search results feel realistic:

| Department | Example documents |
| --- | --- |
| Finance | Annual financial statement, Q1 budget report, expense policy, client review budget notes |
| HR | Leave policy, performance review guide, onboarding checklist, recruitment pipeline |
| IT | API documentation, cloud infrastructure overview, server migration plan, incident playbook, security policy |
| Marketing | Q2 campaign brief, social media strategy, brand guidelines |
| Sales | Enterprise sales playbook, client proposal (TechConnect) |
| Legal | Data privacy policy |
| General | Company handbook |

Supported file types: `.txt`, `.md`, `.csv`, `.json`, `.py`, `.docx`, `.pdf`.

### Demo users

Seed users represent every department so you can test context-aware ranking (defined in `app/services/seed.py`):

| Name | Role | Department | Prefers |
| --- | --- | --- | --- |
| Sara Khan | Financial Analyst | Finance | pdf |
| Ali Raza | HR Manager | HR | docx |
| Usman Tariq | Platform Engineer | IT | md |
| Mariam Noor | Marketing Lead | Marketing | pptx |
| Bilal Ahmed | Enterprise Sales Director | Sales | md |
| Hina Farooq | Compliance Officer | Legal | pdf |
| Zain Malik | Data Engineer | IT | json |
| Ayesha Siddiqui | Recruiter | HR | csv |

### Try these demo queries

Run the same query as different users and watch the order change:

- `budget` â strongest for Sara Khan (Finance)
- `leave policy` â strongest for Ali Raza / Ayesha Siddiqui (HR)
- `server migration` â strongest for Usman Tariq / Zain Malik (IT)
- `campaign` â strongest for Mariam Noor (Marketing)
- `client proposal` â strongest for Bilal Ahmed (Sales)
- `data privacy` â strongest for Hina Farooq (Legal)
- `recruitment`, `incident`, `security`, `onboarding`

---

## How it works

1. **Ingestion** reads every supported file under `workspace_docs/`, extracts text, infers a department and tags, computes a content hash, and stores each document in the database.
2. **Indexing** builds an inverted index (word -> documents) in memory for fast lookup, plus a trie for autocomplete.
3. **Retrieval** tokenizes the query, expands it with synonyms, finds candidate documents via set operations, and scores them with a BM25-style ranking.
4. **Context re-ranking** adjusts each candidate's score using the current user's department, team, preferred file type, document recency, and access history.
5. **Top-K** results are selected with a heap and returned with a short explanation of why each document ranked where it did.
6. **Logging** records each search and document open in the database to power analytics and future context.

---

## Features

- Real file ingestion from a local folder
- BM25-style relevance scoring with synonym expansion
- Context-aware re-ranking (department, team, file preference, recency, access history)
- Autocomplete powered by a trie
- Faster repeat searches with an LRU cache
- Filters for department and file type
- Score explainability (why a document ranked where it did)
- Export search results to CSV with one click
- Related documents suggestions based on shared tags, department, and file type
- Dashboard metrics: total documents, searches, top queries, most-opened files
- Clean, responsive web UI

---

## Tech: DSA and DBMS

**Data structures / algorithms**
- Hash map / dictionary â inverted index and metadata lookup
- Set operations â candidate retrieval
- Trie â autocomplete
- Heap / priority queue â top-K results
- LRU cache â repeated searches
- Counter / frequency tables â BM25-style ranking

**Database**
- PostgreSQL in production (SQLite-compatible schema for local use)
- Tables: `users`, `documents`, `access_logs`, `search_logs`, `bookmarks`, `ingestion_runs`

---

## Project structure

```
app/
  main.py              FastAPI app entry point
  routes/web.py        Web and API routes
  search/engine.py     Retrieval + context re-ranking
  search/structures.py Trie and LRU cache
  services/db.py       Database connection
  services/ingest.py   Folder ingestion
  services/parser.py   Text extraction per file type
  services/seed.py     Demo users
  models/              SQL schema (SQLite + PostgreSQL)
  templates/           HTML templates
  static/css/          Styles
scripts/
  init_db.py           Create tables and seed users
  ingest_demo_files.py Ingest the demo workspace
  run.py               Start the local server
workspace_docs/        Demo documents by department
```

---

## Setup (local)

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe scripts\ingest_demo_files.py
.\.venv\Scripts\python.exe scripts\run.py
```

```bash
# macOS / Linux
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/init_db.py
.venv/bin/python scripts/ingest_demo_files.py
.venv/bin/python scripts/run.py
```

Then open http://127.0.0.1:8000

The database connection is read from the `DATABASE_URL` (or `POSTGRES_URL`) environment variable. See `.env.example` for the expected format.

---

## Adding your own documents

Drop files into any `workspace_docs/<department>/` folder (or create a new department folder), then re-run `scripts/ingest_demo_files.py`. The ingester will index new files, update changed ones (detected via content hash), and skip unchanged files.
