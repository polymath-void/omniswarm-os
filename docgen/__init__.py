"""
Dynamic DocGen Engine
Living AST & Interactive Architectural Documentation Platform
"""

from docgen.extractor import extract_file_symbols
from docgen.merkle import MerkleASTCache
from docgen.compiler import DocGenCompiler

__version__ = "1.0.0"
__all__ = ["extract_file_symbols", "MerkleASTCache", "DocGenCompiler"]
