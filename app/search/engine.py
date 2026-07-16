from __future__ import annotations

import heapq
import html
import math
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import quote

from app.search.structures import LRUCache, Trie
from app.services.db import get_connection

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9']+")
SYNONYMS = {
    'budget':   ['forecast', 'revenue', 'cost', 'spending', 'finance'],
    'hr':       ['policy', 'recruitment', 'payroll', 'human resources', 'staff'],
    'server':   ['deployment', 'migration', 'infra', 'infrastructure', 'cloud'],
    'launch':   ['campaign', 'marketing', 'growth', 'release'],
    'report':   ['analysis', 'summary', 'overview', 'review'],
    'plan':     ['roadmap', 'strategy', 'proposal', 'schedule'],
    'incident': ['issue', 'problem', 'outage', 'alert', 'ticket'],
    'policy':   ['rule', 'guideline', 'procedure', 'compliance'],
}


@dataclass
class SearchDebug:
    query_matches: int
    relevance_score: float
    profile_boost: float
    freshness_boost: float
    history_boost: float


class RetrievalEngine:
    def __init__(self) -> None:
        self.documents: Dict[int, dict] = {}
        self.inverted_index: Dict[str, Set[int]] = defaultdict(set)
        self.term_freqs: Dict[int, Counter] = {}
        self.doc_freqs: Counter = Counter()
        self.trie = Trie()
        self.cache = LRUCache(capacity=128)
        self._built = False

    def tokenize(self, text: str) -> List[str]:
        return TOKEN_PATTERN.findall(text.lower())

    def build_index(self) -> None:
        conn = get_connection()
        docs = conn.execute('SELECT * FROM documents ORDER BY modified_at DESC').fetchall()
        conn.close()
        self.documents.clear()
        self.inverted_index.clear()
        self.term_freqs.clear()
        self.doc_freqs.clear()
        self.trie = Trie()
        for row in docs:
            doc = dict(row)
            doc_id = doc['id']
            combined = f"{doc['title']} {doc['content']} {doc['tags']} {doc['department']} {doc['file_type']}"
            tokens = self.tokenize(combined)
            tf = Counter(tokens)
            self.documents[doc_id] = doc
            self.term_freqs[doc_id] = tf
            for token in tf:
                self.inverted_index[token].add(doc_id)
                self.doc_freqs[token] += 1
                self.trie.insert(token)
        self.cache = LRUCache(capacity=128)
        self._built = True

    def _ensure(self) -> None:
        if not self._built:
            self.build_index()

    def autocomplete(self, prefix: str) -> List[str]:
        self._ensure()
        return self.trie.suggest(prefix.lower())

    def expand_terms(self, query_terms: List[str]) -> List[str]:
        expanded = list(query_terms)
        for term in query_terms:
            expanded.extend(SYNONYMS.get(term, []))
        seen: list = []
        for t in expanded:
            if t not in seen:
                seen.append(t)
        return seen

    def search(self, query: str, user_id: int, filters: dict | None = None) -> List[dict]:
        self._ensure()
        filters = filters or {}
        cache_key = f"{query}|{user_id}|{sorted(filters.items())}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.record_search(query, user_id, filters, len(cached))
            return cached

        original_terms = self.tokenize(query)
        if not original_terms:
            return []
        query_terms = self.expand_terms(original_terms)

        posting_lists = [self.inverted_index.get(t, set()) for t in query_terms if t in self.inverted_index]
        candidate_docs: Set[int] = set.union(*posting_lists) if posting_lists else set()

        if filters.get('department') and filters['department'] != 'All':
            candidate_docs = {d for d in candidate_docs if self.documents[d]['department'] == filters['department']}
        if filters.get('file_type') and filters['file_type'] != 'All':
            candidate_docs = {d for d in candidate_docs if self.documents[d]['file_type'] == filters['file_type'].lower()}

        user = self._fetch_user_context(user_id)
        heap = []
        for doc_id in candidate_docs:
            doc = self.documents[doc_id]
            keyword = self._bm25_score(original_terms, doc_id)
            context  = self._context_score(doc, user, original_terms)
            recency  = self._recency_score(doc['modified_at'])
            access   = self._access_score(user_id, doc_id)
            final = keyword + context + recency + access
            if final <= 0:
                continue
            debug = SearchDebug(
                query_matches=sum(self.term_freqs[doc_id].get(t, 0) for t in original_terms),
                relevance_score=round(keyword, 2),
                profile_boost=round(context, 2),
                freshness_boost=round(recency, 2),
                history_boost=round(access, 2),
            )
            heapq.heappush(heap, (-final, doc_id, debug))

        results = []
        while heap and len(results) < 20:
            neg_score, doc_id, debug = heapq.heappop(heap)
            doc = dict(self.documents[doc_id])
            doc['score'] = round(-neg_score, 3)
            doc['snippet'] = self._snippet(doc['content'], original_terms)
            doc['debug'] = debug
            doc['size_label'] = self._size_label(doc.get('size_bytes', 0))
            doc['explanation'] = self._explanation(debug, doc, user)
            doc['open_uri'] = self._file_uri(doc['path'])
            results.append(doc)

        self.cache.put(cache_key, results)
        self.record_search(query, user_id, filters, len(results))
        return results

    # ── RAG: AI-synthesised answer from top results ──────────────────────────
    def generate_ai_answer(self, query: str, results: List[dict]) -> Optional[str]:
        """
        Pass the top retrieved documents to Claude and generate a concise,
        cited answer. Requires ANTHROPIC_API_KEY in the environment.
        Returns None silently if the key is missing or if results are empty.
        """
        api_key = os.getenv('ANTHROPIC_API_KEY', '').strip()
        if not api_key or not results:
            return None

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            # Build compact context from top 4 documents (≤ 1800 chars each)
            context_parts = []
            for i, doc in enumerate(results[:4], 1):
                chunk = doc['content'][:1800].replace('\n', ' ').strip()
                context_parts.append(f"[{i}] {doc['title']} ({doc['department']})\n{chunk}")
            context = '\n\n---\n\n'.join(context_parts)

            prompt = f"""You are a workplace document assistant. Using ONLY the documents provided below, answer the user's query in 2-4 clear sentences. Cite sources using [1], [2], [3] notation.
If the documents do not contain a direct answer, briefly state what related information is available.
Do not make up facts. Be concise and professional.

DOCUMENTS:
{context}

QUERY: {query}

ANSWER:"""

            response = client.messages.create(
                model='claude-sonnet-4-6',
                max_tokens=400,
                messages=[{'role': 'user', 'content': prompt}],
            )
            return response.content[0].text.strip()

        except Exception:
            return None

    def get_document(self, doc_id: int) -> dict | None:
        self._ensure()
        doc = self.documents.get(doc_id)
        if not doc:
            return None
        enriched = dict(doc)
        enriched['size_label'] = self._size_label(enriched.get('size_bytes', 0))
        enriched['open_uri'] = self._file_uri(enriched['path'])
        return enriched

    def _bm25_score(self, query_terms: List[str], doc_id: int) -> float:
        total_docs = max(len(self.documents), 1)
        avgdl = sum(sum(tf.values()) for tf in self.term_freqs.values()) / total_docs
        tf = self.term_freqs[doc_id]
        dl = sum(tf.values())
        k1, b = 1.5, 0.75
        score = 0.0
        for term in query_terms:
            freq = tf.get(term, 0)
            if not freq:
                continue
            df  = self.doc_freqs.get(term, 0)
            idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1)
            num = freq * (k1 + 1)
            den = freq + k1 * (1 - b + b * (dl / max(avgdl, 1)))
            score += idf * (num / den)
        return score

    def _context_score(self, doc: dict, user: dict, query_terms: List[str]) -> float:
        score = 0.0
        if doc['department'].lower() == user['department'].lower():
            score += 2.8
        if user.get('team') and user['team'].lower() in doc['content'].lower():
            score += 1.2
        if user.get('preferred_file_type') == doc['file_type']:
            score += 0.8
        tags = {t.strip().lower() for t in doc['tags'].split(',')}
        if tags.intersection(set(query_terms)):
            score += 1.5
        return score

    def _recency_score(self, modified_at: str) -> float:
        age = max((datetime.now() - datetime.fromisoformat(modified_at)).days, 0)
        return max(0.0, 2.5 - (age * 0.03))

    def _access_score(self, user_id: int, doc_id: int) -> float:
        conn = get_connection()
        row = conn.execute(
            'SELECT COUNT(*) AS total FROM access_logs WHERE user_id=? AND document_id=?',
            (user_id, doc_id)
        ).fetchone()
        conn.close()
        return min((row['total'] if row else 0) * 0.7, 2.1)

    def _fetch_user_context(self, user_id: int) -> dict:
        conn = get_connection()
        row = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else {'department': 'General', 'team': '', 'preferred_file_type': ''}

    def _snippet(self, text: str, query_terms: List[str], size: int = 260) -> str:
        lower = text.lower()
        pos = 0
        for term in query_terms:
            idx = lower.find(term.lower())
            if idx != -1:
                pos = max(0, idx - 70)
                break
        snippet = text[pos:pos + size].replace('\n', ' ').strip()
        snippet = html.escape(snippet)
        for term in sorted(set(query_terms), key=len, reverse=True):
            pattern = re.compile(rf'({re.escape(term)})', re.IGNORECASE)
            snippet = pattern.sub(r'<mark>\1</mark>', snippet)
        return snippet + ('…' if len(text) > pos + size else '')

    def _size_label(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f'{size_bytes} B'
        if size_bytes < 1024 * 1024:
            return f'{size_bytes / 1024:.1f} KB'
        return f'{size_bytes / (1024 * 1024):.1f} MB'

    def _explanation(self, debug: SearchDebug, doc: dict, user: dict) -> str:
        reasons = []
        if debug.query_matches:
            reasons.append('strong keyword match')
        if debug.profile_boost:
            reasons.append(f"matches {user['department']} profile")
        if debug.freshness_boost:
            reasons.append('recently modified')
        if debug.history_boost:
            reasons.append('in your access history')
        return ' · '.join(reasons[:3]) or f"Relevant {doc['file_type'].upper()} document"

    def record_click(self, user_id: int, doc_id: int) -> None:
        conn = get_connection()
        conn.execute(
            'INSERT INTO access_logs (user_id, document_id, action) VALUES (?, ?, ?)',
            (user_id, doc_id, 'open')
        )
        conn.commit()
        conn.close()

    def record_search(self, query: str, user_id: int, filters: dict, result_count: int) -> None:
        conn = get_connection()
        conn.execute(
            'INSERT INTO search_logs (user_id, query, department_filter, file_type_filter, result_count) VALUES (?, ?, ?, ?, ?)',
            (user_id, query.strip(), filters.get('department', 'All'), filters.get('file_type', 'All'), result_count),
        )
        conn.commit()
        conn.close()

    def dashboard_stats(self) -> dict:
        self._ensure()
        conn = get_connection()
        total_users    = conn.execute('SELECT COUNT(*) AS c FROM users').fetchone()['c']
        total_access   = conn.execute('SELECT COUNT(*) AS c FROM access_logs').fetchone()['c']
        total_searches = conn.execute('SELECT COUNT(*) AS c FROM search_logs').fetchone()['c']
        departments    = conn.execute('SELECT department, COUNT(*) AS c FROM documents GROUP BY department ORDER BY c DESC').fetchall()
        file_types     = conn.execute('SELECT file_type, COUNT(*) AS c FROM documents GROUP BY file_type ORDER BY c DESC').fetchall()
        latest         = conn.execute('SELECT * FROM ingestion_runs ORDER BY id DESC LIMIT 1').fetchone()
        latest_docs    = conn.execute('SELECT title, file_type, department, modified_at FROM documents ORDER BY modified_at DESC LIMIT 6').fetchall()
        top_opened     = conn.execute(
            '''SELECT d.id, d.title, d.department, d.file_type, COUNT(*) AS opens
               FROM access_logs a JOIN documents d ON d.id = a.document_id
               GROUP BY d.id, d.title, d.department, d.file_type ORDER BY opens DESC LIMIT 5'''
        ).fetchall()
        recent_searches = conn.execute(
            '''SELECT s.query, s.result_count, s.created_at, u.name, u.department
               FROM search_logs s JOIN users u ON u.id = s.user_id
               ORDER BY s.id DESC LIMIT 8'''
        ).fetchall()
        scan_history = conn.execute(
            'SELECT id, scanned_count, inserted_count, updated_count, created_at FROM ingestion_runs ORDER BY id DESC LIMIT 6'
        ).fetchall()
        conn.close()

        max_dept = max([r['c'] for r in departments], default=1)
        max_type = max([r['c'] for r in file_types], default=1)
        max_scan = max([r['scanned_count'] for r in scan_history], default=1)

        return {
            'documents':    len(self.documents),
            'users':        total_users,
            'access_logs':  total_access,
            'searches':     total_searches,
            'departments': [
                {'department': r['department'], 'count': r['c'],
                 'width': max(8, int((r['c'] / max_dept) * 100))}
                for r in departments
            ],
            'file_types': [
                {'file_type': r['file_type'], 'count': r['c'],
                 'width': max(8, int((r['c'] / max_type) * 100))}
                for r in file_types
            ],
            'latest_docs':   [dict(r) for r in latest_docs],
            'latest_run':    dict(latest) if latest else None,
            'top_opened':    [dict(r) for r in top_opened],
            'recent_searches': [dict(r) for r in recent_searches],
            'scan_history': [
                {
                    'label':    datetime.fromisoformat(r['created_at']).strftime('%b %d'),
                    'count':    r['scanned_count'],
                    'inserted': r['inserted_count'],
                    'updated':  r['updated_count'],
                    'width':    max(8, int((r['scanned_count'] / max_scan) * 100)),
                }
                for r in reversed([dict(r) for r in scan_history])
            ],
        }

    def _file_uri(self, file_path: str) -> str:
        try:
            path = Path(file_path)
            return path.resolve().as_uri()
        except Exception:
            normalized = file_path.replace('\\', '/')
            if re.match(r'^[A-Za-z]:/', normalized):
                return 'file:///' + quote(normalized)
            return 'file://' + quote(normalized)
