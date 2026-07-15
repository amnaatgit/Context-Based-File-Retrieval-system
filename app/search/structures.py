from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class TrieNode:
    children: Dict[str, 'TrieNode'] = field(default_factory=dict)
    is_word: bool = False


class Trie:
    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        node.is_word = True

    def suggest(self, prefix: str, limit: int = 8) -> List[str]:
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        out: List[str] = []

        def dfs(cur: TrieNode, path: str) -> None:
            if len(out) >= limit:
                return
            if cur.is_word:
                out.append(path)
            for key in sorted(cur.children):
                dfs(cur.children[key], path + key)

        dfs(node, prefix)
        return out


class LRUCache:
    def __init__(self, capacity: int = 32) -> None:
        self.capacity = capacity
        self.data: OrderedDict[str, list] = OrderedDict()

    def get(self, key: str):
        if key not in self.data:
            return None
        self.data.move_to_end(key)
        return self.data[key]

    def put(self, key: str, value) -> None:
        self.data[key] = value
        self.data.move_to_end(key)
        if len(self.data) > self.capacity:
            self.data.popitem(last=False)
