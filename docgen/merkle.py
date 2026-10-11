"""
DocGen Merkle & Content-Addressed AST Cache
=============================================================================
Provides incremental change detection and cache invalidation via
cryptographic hashing (BLAKE2b / SHA-256) and mtime tracking.
Prevents redundant AST walks on large codebases.
=============================================================================
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional

class MerkleASTCache:
    def __init__(self, cache_file: str = ".docgen_cache.json"):
        self.cache_file = cache_file
        self.entries: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.entries = json.load(f)
            except Exception:
                self.entries = {}
        else:
            self.entries = {}

    def save(self):
        try:
            tmp = f"{self.cache_file}.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, indent=2)
            os.replace(tmp, self.cache_file)
        except Exception:
            pass

    @staticmethod
    def compute_file_hash(path: str) -> str:
        hasher = hashlib.blake2b(digest_size=16)
        try:
            with open(path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    def is_cached(self, file_path: str, mtime: float) -> bool:
        if file_path not in self.entries:
            return False
        entry = self.entries[file_path]
        if entry.get("mtime") == mtime:
            return True
        # If mtime differs, check hash
        current_hash = self.compute_file_hash(file_path)
        return entry.get("hash") == current_hash

    def get_cached_symbols(self, file_path: str) -> Optional[Dict[str, Any]]:
        if file_path in self.entries:
            return self.entries[file_path].get("data")
        return None

    def update(self, file_path: str, mtime: float, data: Dict[str, Any]):
        file_hash = self.compute_file_hash(file_path)
        self.entries[file_path] = {
            "mtime": mtime,
            "hash": file_hash,
            "data": data
        }

    def prune_stale(self, existing_files: set):
        to_delete = [p for p in self.entries if p not in existing_files]
        for p in to_delete:
            del self.entries[p]
