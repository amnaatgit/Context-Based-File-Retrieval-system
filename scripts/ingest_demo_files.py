from pathlib import Path

from app.services.ingest import ingest_workspace

if __name__ == '__main__':
    workspace = Path(__file__).resolve().parents[1] / 'workspace_docs'
    result = ingest_workspace(str(workspace))
    print(f'Ingested workspace: {result}')
