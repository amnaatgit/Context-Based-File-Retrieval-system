DROP TABLE IF EXISTS bookmarks;
DROP TABLE IF EXISTS search_logs;
DROP TABLE IF EXISTS access_logs;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS ingestion_runs;

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  role TEXT NOT NULL,
  department TEXT NOT NULL,
  team TEXT,
  preferred_file_type TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
  );

CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  path TEXT NOT NULL UNIQUE,
  file_type TEXT NOT NULL,
  department TEXT NOT NULL,
  tags TEXT NOT NULL,
  author TEXT NOT NULL,
  content TEXT NOT NULL,
  size_bytes INTEGER DEFAULT 0,
  modified_at TEXT NOT NULL,
  indexed_at TEXT NOT NULL,
  content_hash TEXT NOT NULL
  );

CREATE TABLE access_logs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL,
  document_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (document_id) REFERENCES documents(id)
  );

CREATE TABLE search_logs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL,
  query TEXT NOT NULL,
  department_filter TEXT,
  file_type_filter TEXT,
  result_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
  );

CREATE TABLE ingestion_runs (
  id SERIAL PRIMARY KEY,
  workspace_path TEXT NOT NULL,
  scanned_count INTEGER NOT NULL,
  inserted_count INTEGER NOT NULL,
  updated_count INTEGER NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
  );

CREATE TABLE bookmarks (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL,
  document_id INTEGER NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, document_id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (document_id) REFERENCES documents(id)
  );
