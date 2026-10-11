#!/usr/bin/env python3
"""
Test Suite for Dynamic DocGen Engine
Validates AST extractor, Merkle cache, graph compiler, and search indexing.
"""

import os
import sys
import tempfile
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from docgen.extractor import extract_file_symbols, calculate_python_complexity
from docgen.merkle import MerkleASTCache
from docgen.compiler import DocGenCompiler

class TestDynamicDocGen(unittest.TestCase):

    def setUp(self):
        self.test_code = '''"""Sample Module Docstring."""

import os
import sys

class EngineCore:
    """The core engine class."""
    def __init__(self, mode: str = "prod"):
        self.mode = mode

    async def execute(self, payload: dict) -> bool:
        """Executes a payload with branching logic."""
        if self.mode == "dev":
            print("Dev mode")
            return True
        elif self.mode == "prod":
            for item in payload.get("items", []):
                if item == "skip":
                    continue
                print(item)
            return True
        return False

def standalone_helper(x: int, y: int) -> int:
    """Helper function."""
    return x + y
'''
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False)
        self.temp_file.write(self.test_code)
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_ast_extractor(self):
        data = extract_file_symbols(self.temp_file.name, os.path.dirname(self.temp_file.name))
        self.assertEqual(data["docstring"], "Sample Module Docstring.")
        self.assertEqual(len(data["classes"]), 1)
        self.assertEqual(data["classes"][0]["name"], "EngineCore")
        self.assertEqual(len(data["classes"][0]["methods"]), 2)

        exec_method = [m for m in data["classes"][0]["methods"] if m["name"] == "execute"][0]
        self.assertTrue(exec_method["is_async"])
        self.assertGreaterEqual(exec_method["complexity"], 3)
        self.assertEqual(exec_method["returns"], "bool")

        self.assertEqual(len(data["functions"]), 1)
        self.assertEqual(data["functions"][0]["name"], "standalone_helper")
        self.assertEqual(data["functions"][0]["returns"], "int")

    def test_merkle_cache(self):
        cache_path = os.path.join(tempfile.gettempdir(), ".test_docgen_cache.json")
        if os.path.exists(cache_path):
            os.remove(cache_path)

        cache = MerkleASTCache(cache_file=cache_path)
        mtime = os.path.getmtime(self.temp_file.name)
        data = {"dummy": "data"}

        self.assertFalse(cache.is_cached("test.py", mtime))
        cache.update("test.py", mtime, data)
        cache.save()

        # Reload
        cache2 = MerkleASTCache(cache_file=cache_path)
        self.assertTrue(cache2.is_cached("test.py", mtime))
        self.assertEqual(cache2.get_cached_symbols("test.py"), data)

        if os.path.exists(cache_path):
            os.remove(cache_path)

    def test_compiler_end_to_end(self):
        compiler = DocGenCompiler(root_dir=SCRIPT_DIR)
        manifest = compiler.compile()

        self.assertIn("project", manifest)
        self.assertIn("symbols", manifest)
        self.assertIn("graph", manifest)
        self.assertIn("search_index", manifest)

        stats = manifest["project"]["stats"]
        self.assertGreater(stats["total_files"], 0)
        self.assertGreater(stats["total_loc"], 0)
        self.assertGreater(len(manifest["graph"]["nodes"]), 0)
        self.assertGreater(len(manifest["graph"]["edges"]), 0)

if __name__ == "__main__":
    unittest.main()
