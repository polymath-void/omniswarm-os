"""
DocGen Graph Compiler & Search Index Generator
=============================================================================
Compiles raw AST symbols into a relational knowledge graph (Nodes + Edges)
and generates an inverted full-text search index for the client-side SPA.
=============================================================================
"""

import os
import time
from typing import Dict, List, Any, Set
from docgen.extractor import extract_file_symbols
from docgen.merkle import MerkleASTCache

IGNORED_DIRS = {
    ".git", "node_modules", "dist", "build", "__pycache__",
    ".pytest_cache", ".agents", ".opencode", ".venv", "venv",
    "site-packages", ".idea", ".vscode"
}

VALID_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx"}

class DocGenCompiler:
    def __init__(self, root_dir: str, cache_file: str = ".docgen_cache.json"):
        self.root_dir = os.path.abspath(root_dir)
        self.cache = MerkleASTCache(cache_file=os.path.join(self.root_dir, cache_file))

    def discover_files(self) -> List[str]:
        """Finds all parsable source files in the target directory."""
        found = []
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in VALID_EXTENSIONS:
                    found.append(os.path.join(root, file))
        return found

    def compile(self) -> Dict[str, Any]:
        """Executes full incremental compilation of the codebase documentation."""
        start_time = time.time()
        files = self.discover_files()
        existing_rel_files = set()

        all_file_data = []
        stats = {
            "total_files": len(files),
            "total_loc": 0,
            "total_classes": 0,
            "total_functions": 0,
            "avg_complexity": 0.0,
            "complexities": []
        }

        # 1. Parse or load from Merkle cache
        for fpath in files:
            rel_path = os.path.relpath(fpath, self.root_dir).replace("\\", "/")
            existing_rel_files.add(rel_path)
            mtime = os.path.getmtime(fpath)

            if self.cache.is_cached(rel_path, mtime):
                data = self.cache.get_cached_symbols(rel_path)
            else:
                data = extract_file_symbols(fpath, self.root_dir)
                self.cache.update(rel_path, mtime, data)

            if data:
                all_file_data.append(data)
                stats["total_loc"] += data.get("loc", 0)
                stats["total_classes"] += len(data.get("classes", []))
                stats["total_functions"] += len(data.get("functions", []))
                for c in data.get("classes", []):
                    stats["total_functions"] += len(c.get("methods", []))
                    for m in c.get("methods", []):
                        stats["complexities"].append(m.get("complexity", 1))
                for fn in data.get("functions", []):
                    stats["complexities"].append(fn.get("complexity", 1))

        # Save updated cache
        self.cache.prune_stale(existing_rel_files)
        self.cache.save()

        if stats["complexities"]:
            stats["avg_complexity"] = round(sum(stats["complexities"]) / len(stats["complexities"]), 2)
        del stats["complexities"]

        # 2. Build Unified Symbol Dictionary
        symbols: Dict[str, Any] = {}
        # Quick lookup for symbol resolution: name -> [full_names]
        name_to_ids: Dict[str, List[str]] = {}

        for f in all_file_data:
            # File node
            f_id = f"module:{f['file']}"
            symbols[f_id] = {
                "id": f_id,
                "name": f["file"],
                "type": "module",
                "file": f["file"],
                "docstring": f.get("docstring", ""),
                "loc": f.get("loc", 0),
                "imports": f.get("imports", [])
            }

            for c in f.get("classes", []):
                cid = c["full_name"]
                symbols[cid] = c
                name_to_ids.setdefault(c["name"], []).append(cid)
                for m in c.get("methods", []):
                    mid = m["full_name"]
                    symbols[mid] = m
                    name_to_ids.setdefault(m["name"], []).append(mid)

            for fn in f.get("functions", []):
                fn_id = fn["full_name"]
                symbols[fn_id] = fn
                name_to_ids.setdefault(fn["name"], []).append(fn_id)

        # 3. Resolve Call Graph & Build Graph (Nodes + Edges)
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        for sid, sym in symbols.items():
            nodes.append({
                "id": sid,
                "name": sym["name"],
                "type": sym["type"],
                "file": sym["file"],
                "line": sym.get("line", 1)
            })

            # Containment edges
            if sym["type"] in ["class", "function"]:
                edges.append({
                    "source": f"module:{sym['file']}",
                    "target": sid,
                    "relation": "contains"
                })
            elif sym["type"] == "method" and sym.get("parent_class"):
                edges.append({
                    "source": f"{sym['file']}:{sym['parent_class']}",
                    "target": sid,
                    "relation": "contains"
                })

            # Inheritance edges
            if sym["type"] == "class":
                for base in sym.get("bases", []):
                    if base in name_to_ids:
                        for target_id in name_to_ids[base]:
                            edges.append({
                                "source": sid,
                                "target": target_id,
                                "relation": "inherits"
                            })

            # Call edges
            calls = sym.get("calls", [])
            sym["callers"] = []  # populate reverse callers
            for called_name in calls:
                if called_name in name_to_ids:
                    for target_id in name_to_ids[called_name]:
                        edges.append({
                            "source": sid,
                            "target": target_id,
                            "relation": "calls"
                        })

        # Reverse caller population
        for edge in edges:
            if edge["relation"] == "calls":
                target = edge["target"]
                source = edge["source"]
                if target in symbols:
                    if "callers" not in symbols[target]:
                        symbols[target]["callers"] = []
                    if source not in symbols[target]["callers"]:
                        symbols[target]["callers"].append(source)

        # 4. Generate Inverted Search Index
        search_index = []
        for sid, sym in symbols.items():
            search_index.append({
                "id": sid,
                "name": sym["name"],
                "type": sym["type"],
                "file": sym["file"],
                "line": sym.get("line", 1),
                "doc": sym.get("docstring", "")[:120],
                "sig": sym.get("signature", "")
            })

        project_name = os.path.basename(self.root_dir)
        elapsed = round(time.time() - start_time, 3)

        manifest = {
            "project": {
                "name": project_name,
                "root": self.root_dir,
                "compiled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "build_duration_sec": elapsed,
                "stats": stats
            },
            "symbols": symbols,
            "graph": {
                "nodes": nodes,
                "edges": edges
            },
            "search_index": search_index
        }

        return manifest
