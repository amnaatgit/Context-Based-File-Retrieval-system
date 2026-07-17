from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.search.engine import RetrievalEngine
from app.services.db import get_connection
from app.services.ingest import ingest_workspace

router = APIRouter()
templates = Jinja2Templates(directory='app/templates')
engine = RetrievalEngine()

UPLOAD_DIR = Path('/tmp/workspace_docs/uploads')
try:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass


def load_meta():
    conn = get_connection()
    users       = conn.execute('SELECT id, name, role, department FROM users ORDER BY id').fetchall()
    departments = [r['department'] for r in conn.execute('SELECT DISTINCT department FROM documents ORDER BY department').fetchall()]
    file_types  = [r['file_type']  for r in conn.execute('SELECT DISTINCT file_type FROM documents ORDER BY file_type').fetchall()]
    conn.close()
    return users, departments, file_types


def get_recent(user_id: int, limit: int = 6):
    conn = get_connection()
    rows = conn.execute(
        '''SELECT DISTINCT d.id, d.title, d.department, d.file_type, a.created_at
           FROM access_logs a JOIN documents d ON d.id = a.document_id
           WHERE a.user_id = ? ORDER BY a.created_at DESC LIMIT ?''',
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_bookmarks(user_id: int):
    conn = get_connection()
    rows = conn.execute(
        '''SELECT d.id, d.title, d.department, d.file_type
           FROM bookmarks b JOIN documents d ON d.id = b.document_id
           WHERE b.user_id = ? ORDER BY b.id DESC''',
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_bookmarked_ids(user_id: int):
    conn = get_connection()
    rows = conn.execute('SELECT document_id FROM bookmarks WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return {r['document_id'] for r in rows}


def get_tag_cloud():
    conn = get_connection()
    rows = conn.execute('SELECT tags FROM documents').fetchall()
    conn.close()
    counts: dict = {}
    for row in rows:
        for tag in row['tags'].split(','):
            t = tag.strip()
            if t:
                counts[t] = counts.get(t, 0) + 1
    return sorted(counts.items(), key=lambda x: -x[1])[:20]


def base_ctx(request: Request, user_id: int = 1) -> dict:
    users, departments, file_types = load_meta()
    return {
        'request':             request,
        'users':               users,
        'departments':         departments,
        'file_types':          file_types,
        'selected_user':       user_id,
        'selected_department': 'All',
        'selected_file_type':  'All',
        'query':               '',
        'results':             [],
        'suggestions':         [],
        'stats':               engine.dashboard_stats(),
        'message':             None,
        'message_type':        'info',
        'workspace_value':     'workspace_docs',
        'ai_answer':           None,
        'active_tab':          'search',
        'recent_docs':         get_recent(user_id),
        'bookmarks':           get_bookmarks(user_id),
        'bookmarked_ids':      get_bookmarked_ids(user_id),
        'tag_cloud':           get_tag_cloud(),
    }


# ── Home ──────────────────────────────────────────────────────────────────────
@router.get('/', response_class=HTMLResponse)
def home(request: Request, user_id: int = 1):
    engine.build_index()
    ctx = base_ctx(request, user_id)
    return templates.TemplateResponse('index.html', ctx)


# ── Search ────────────────────────────────────────────────────────────────────
@router.post('/search', response_class=HTMLResponse)
def search(
    request:    Request,
    query:      str = Form(...),
    user_id:    int = Form(1),
    department: str = Form('All'),
    file_type:  str = Form('All'),
):
    ctx     = base_ctx(request, user_id)
    filters = {'department': department, 'file_type': file_type}
    results = engine.search(query, user_id, filters)
    ai_answer = engine.generate_ai_answer(query, results)

    # mark bookmarked results
    bids = get_bookmarked_ids(user_id)
    for r in results:
        r['bookmarked'] = r['id'] in bids

    ctx.update({
        'results':             results,
        'query':               query,
        'selected_user':       user_id,
        'selected_department': department,
        'selected_file_type':  file_type,
        'suggestions':         engine.autocomplete(query.split()[0]) if query.strip() else [],
        'ai_answer':           ai_answer,
        'message':             f'{len(results)} result(s) for "{query}"',
        'message_type':        'success' if results else 'info',
        'active_tab':          'search',
    })
    return templates.TemplateResponse('index.html', ctx)


# ── Browse ────────────────────────────────────────────────────────────────────
@router.get('/browse', response_class=HTMLResponse)
def browse(request: Request, department: str = 'All', file_type: str = 'All', user_id: int = 1):
    engine.build_index()
    ctx = base_ctx(request, user_id)
    ctx['active_tab'] = 'browse'
    conn = get_connection()
    q = 'SELECT id,title,department,file_type,tags,size_bytes,modified_at FROM documents'
    params, clauses = [], []
    if department != 'All': clauses.append('department=?'); params.append(department)
    if file_type  != 'All': clauses.append('file_type=?');  params.append(file_type)
    if clauses: q += ' WHERE ' + ' AND '.join(clauses)
    q += ' ORDER BY modified_at DESC'
    docs = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    bids = get_bookmarked_ids(user_id)
    for d in docs:
        d['size_label'] = engine._size_label(d.get('size_bytes', 0))
        d['bookmarked'] = d['id'] in bids
    ctx.update({'browse_docs': docs, 'selected_department': department, 'selected_file_type': file_type})
    return templates.TemplateResponse('index.html', ctx)


# ── Analytics ─────────────────────────────────────────────────────────────────
@router.get('/analytics', response_class=HTMLResponse)
def analytics(request: Request, user_id: int = 1):
    engine.build_index()
    ctx = base_ctx(request, user_id)
    ctx['active_tab'] = 'analytics'
    return templates.TemplateResponse('index.html', ctx)


# ── Bookmarks ─────────────────────────────────────────────────────────────────
@router.get('/bookmarks', response_class=HTMLResponse)
def bookmarks_page(request: Request, user_id: int = 1):
    engine.build_index()
    ctx = base_ctx(request, user_id)
    ctx['active_tab'] = 'bookmarks'
    return templates.TemplateResponse('index.html', ctx)


# ── Upload ────────────────────────────────────────────────────────────────────
@router.post('/upload', response_class=HTMLResponse)
async def upload(request: Request, files: list[UploadFile] = File(...)):
    ctx = base_ctx(request)
    ctx['active_tab'] = 'upload'
    saved, errors = [], []
    for file in files:
        if not file.filename: continue
        dest = UPLOAD_DIR / file.filename
        try:
            with open(dest, 'wb') as f: shutil.copyfileobj(file.file, f)
            saved.append(file.filename)
        except Exception as e: errors.append(f'{file.filename}: {e}')
    if saved:
        r = ingest_workspace(str(UPLOAD_DIR)); engine.build_index()
        ctx['message'] = f'✓ {len(saved)} file(s) uploaded and indexed. {r["inserted"]} new, {r["updated"]} updated.'
        ctx['message_type'] = 'success'
    if errors:
        ctx['message'] = (ctx.get('message') or '') + ' ' + '; '.join(errors)
        ctx['message_type'] = 'error'
    return templates.TemplateResponse('index.html', ctx)


# ── Ingest folder ─────────────────────────────────────────────────────────────
@router.post('/ingest', response_class=HTMLResponse)
def ingest(request: Request, workspace: str = Form(...)):
    ctx = base_ctx(request); ctx['active_tab'] = 'upload'
    try:
        o = ingest_workspace(workspace); engine.build_index()
        ctx['workspace_value'] = workspace
        ctx['message'] = f'Scan complete — {o["scanned"]} scanned, {o["inserted"]} added, {o["updated"]} updated.'
        ctx['message_type'] = 'success'
    except FileNotFoundError as e:
        ctx['workspace_value'] = workspace
        ctx['message'] = str(e); ctx['message_type'] = 'error'
    return templates.TemplateResponse('index.html', ctx)


# ── Document detail ───────────────────────────────────────────────────────────
@router.get('/documents/{doc_id}', response_class=HTMLResponse)
def document_detail(request: Request, doc_id: int, user_id: int = 1):
    engine.build_index()
    doc = engine.get_document(doc_id)
    if not doc: return RedirectResponse('/', status_code=303)
    engine.record_click(user_id, doc_id)
    bids = get_bookmarked_ids(user_id)
    doc['bookmarked'] = doc_id in bids
    related = engine.related_documents(doc_id, limit=4)
    return templates.TemplateResponse('document.html', {
        'request': request, 'doc': doc, 'user_id': user_id,
        'related': related, 'bookmarked': doc_id in bids
    })


# ── Bookmark toggle (JSON) ────────────────────────────────────────────────────
@router.post('/api/bookmark')
def toggle_bookmark(user_id: int = Form(...), doc_id: int = Form(...)):
    conn = get_connection()
    exists = conn.execute('SELECT id FROM bookmarks WHERE user_id=? AND document_id=?', (user_id, doc_id)).fetchone()
    if exists:
        conn.execute('DELETE FROM bookmarks WHERE user_id=? AND document_id=?', (user_id, doc_id))
        state = False
    else:
        conn.execute('INSERT INTO bookmarks (user_id, document_id) VALUES (?,?)', (user_id, doc_id))
        state = True
    conn.commit(); conn.close()
    return JSONResponse({'bookmarked': state})


# ── JSON API ──────────────────────────────────────────────────────────────────
@router.get('/api/search')
def api_search(q: str, user_id: int = 1, department: str = 'All', file_type: str = 'All'):
    results = engine.search(q, user_id, {'department': department, 'file_type': file_type})
    return JSONResponse({'query': q, 'count': len(results), 'results': [
        {'id': r['id'], 'title': r['title'], 'department': r['department'],
         'file_type': r['file_type'], 'score': r['score'],
         'snippet': r['snippet'], 'explanation': r['explanation']}
        for r in results
    ]})

@router.get('/api/suggest')
def api_suggest(q: str):
    words = q.strip().split()
    sug = engine.autocomplete(words[-1]) if words else []
    return JSONResponse({'suggestions': sug})
