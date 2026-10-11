"""
DocGen AST & Symbol Extractor
=============================================================================
Zero-dependency, high-speed Python & JS/TS symbol and call-graph extractor.
Analyzes syntax trees to extract modules, classes, methods, functions,
signatures, type hints, docstrings, decorators, cyclomatic complexity,
and outgoing invocation references.
=============================================================================
"""

import ast
import re
import os
from typing import Dict, List, Any, Optional

def calculate_python_complexity(node: ast.AST) -> int:
    """Calculates McCabe Cyclomatic Complexity for an AST node."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor,
                              ast.ExceptHandler, ast.With, ast.AsyncWith,
                              ast.Assert)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            complexity += len(child.generators)
    return complexity

def format_ast_type_annotation(node: Optional[ast.AST]) -> str:
    """Formats an AST expression node into a readable type string."""
    if node is None:
        return "Any"
    try:
        return ast.unparse(node)
    except Exception:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return "Any"

def extract_calls(node: ast.AST) -> List[str]:
    """Finds all function or method call identifiers in an AST subtree."""
    calls = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                calls.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                calls.append(child.func.attr)
    return list(dict.fromkeys(calls))

class PythonASTExtractor:
    """Extracts deep symbol hierarchies from Python source code."""

    def __init__(self, file_path: str, source_code: str, rel_path: str):
        self.file_path = file_path
        self.source_code = source_code
        self.rel_path = rel_path
        self.lines = source_code.splitlines()

    def extract(self) -> Dict[str, Any]:
        try:
            tree = ast.parse(self.source_code, filename=self.file_path)
        except SyntaxError as e:
            return {
                "file": self.rel_path,
                "error": f"SyntaxError: {e.msg} at line {e.lineno}",
                "classes": [],
                "functions": [],
                "imports": [],
                "docstring": "",
                "loc": len(self.lines)
            }

        module_doc = ast.get_docstring(tree) or ""
        imports = []
        classes = []
        functions = []

        # Top-level AST walk
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "module": alias.name,
                        "alias": alias.asname or alias.name,
                        "line": node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    imports.append({
                        "module": f"{mod}.{alias.name}" if mod else alias.name,
                        "alias": alias.asname or alias.name,
                        "line": node.lineno
                    })
            elif isinstance(node, ast.ClassDef):
                classes.append(self._parse_class(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._parse_function(node))

        return {
            "file": self.rel_path,
            "docstring": module_doc.strip(),
            "loc": len(self.lines),
            "imports": imports,
            "classes": classes,
            "functions": functions
        }

    def _parse_class(self, node: ast.ClassDef) -> Dict[str, Any]:
        bases = [format_ast_type_annotation(b) for b in node.bases]
        decorators = [format_ast_type_annotation(d) for d in node.decorator_list]
        docstring = ast.get_docstring(node) or ""
        methods = []

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._parse_function(item, parent_class=node.name))

        start_line = node.lineno
        end_line = getattr(node, 'end_lineno', start_line)
        source_snippet = "\n".join(self.lines[start_line - 1:end_line])

        return {
            "name": node.name,
            "full_name": f"{self.rel_path}:{node.name}",
            "type": "class",
            "file": self.rel_path,
            "line": start_line,
            "end_line": end_line,
            "bases": bases,
            "decorators": decorators,
            "docstring": docstring.strip(),
            "methods": methods,
            "source": source_snippet
        }

    def _parse_function(self, node: Any, parent_class: Optional[str] = None) -> Dict[str, Any]:
        is_async = isinstance(node, ast.AsyncFunctionDef)
        decorators = [format_ast_type_annotation(d) for d in node.decorator_list]
        docstring = ast.get_docstring(node) or ""
        complexity = calculate_python_complexity(node)
        calls = extract_calls(node)

        # Parse parameters
        args = []
        for arg in node.args.args:
            arg_type = format_ast_type_annotation(arg.annotation) if arg.annotation else "Any"
            args.append({
                "name": arg.arg,
                "type": arg_type
            })

        # Return type
        return_type = format_ast_type_annotation(node.returns) if node.returns else "None"
        
        # Build signature string
        params_str = ", ".join(f"{a['name']}: {a['type']}" if a['type'] != 'Any' else a['name'] for a in args)
        prefix = "async def " if is_async else "def "
        signature = f"{prefix}{node.name}({params_str}) -> {return_type}"

        start_line = node.lineno
        end_line = getattr(node, 'end_lineno', start_line)
        source_snippet = "\n".join(self.lines[start_line - 1:end_line])

        sym_id = f"{self.rel_path}:{parent_class}.{node.name}" if parent_class else f"{self.rel_path}:{node.name}"

        return {
            "name": node.name,
            "full_name": sym_id,
            "parent_class": parent_class,
            "type": "method" if parent_class else "function",
            "file": self.rel_path,
            "line": start_line,
            "end_line": end_line,
            "is_async": is_async,
            "signature": signature,
            "args": args,
            "returns": return_type,
            "decorators": decorators,
            "complexity": complexity,
            "docstring": docstring.strip(),
            "calls": calls,
            "source": source_snippet
        }


class JSTSExtractor:
    """Regex & heuristic symbol parser for JavaScript and TypeScript source files."""

    def __init__(self, file_path: str, source_code: str, rel_path: str):
        self.file_path = file_path
        self.source_code = source_code
        self.rel_path = rel_path
        self.lines = source_code.splitlines()

    def extract(self) -> Dict[str, Any]:
        classes = []
        functions = []
        imports = []

        # Import regex
        import_pattern = re.compile(r'import\s+(?:\{([^}]+)\}|\*\s+as\s+(\w+)|(\w+))\s+from\s+[\'"]([^\'"]+)[\'"]')
        for match in import_pattern.finditer(self.source_code):
            named, namespace, default_id, mod = match.groups()
            imports.append({
                "module": mod,
                "symbols": [s.strip() for s in (named or namespace or default_id or "").split(",") if s.strip()]
            })

        # Class regex
        class_pattern = re.compile(r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{', re.MULTILINE)
        for match in class_pattern.finditer(self.source_code):
            cname, base = match.groups()
            line_no = self.source_code[:match.start()].count("\n") + 1
            classes.append({
                "name": cname,
                "full_name": f"{self.rel_path}:{cname}",
                "type": "class",
                "file": self.rel_path,
                "line": line_no,
                "bases": [base] if base else [],
                "decorators": [],
                "docstring": "",
                "methods": [],
                "source": match.group(0)
            })

        # Function regex
        func_pattern = re.compile(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', re.MULTILINE)
        for match in func_pattern.finditer(self.source_code):
            fname, params = match.groups()
            line_no = self.source_code[:match.start()].count("\n") + 1
            args = [{"name": p.strip(), "type": "any"} for p in params.split(",") if p.strip()]
            functions.append({
                "name": fname,
                "full_name": f"{self.rel_path}:{fname}",
                "type": "function",
                "file": self.rel_path,
                "line": line_no,
                "is_async": "async" in match.group(0),
                "signature": f"function {fname}({params})",
                "args": args,
                "returns": "any",
                "complexity": 1,
                "docstring": "",
                "calls": [],
                "source": match.group(0)
            })

        return {
            "file": self.rel_path,
            "docstring": "",
            "loc": len(self.lines),
            "imports": imports,
            "classes": classes,
            "functions": functions
        }


def extract_file_symbols(abs_path: str, root_dir: str) -> Dict[str, Any]:
    """Analyzes a source file and returns its structural symbol metadata."""
    rel_path = os.path.relpath(abs_path, root_dir).replace("\\", "/")
    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()
    except Exception as e:
        return {"file": rel_path, "error": str(e), "classes": [], "functions": [], "imports": []}

    if abs_path.endswith(".py"):
        extractor = PythonASTExtractor(abs_path, code, rel_path)
        return extractor.extract()
    elif abs_path.endswith((".js", ".jsx", ".ts", ".tsx")):
        extractor = JSTSExtractor(abs_path, code, rel_path)
        return extractor.extract()
    else:
        return {"file": rel_path, "classes": [], "functions": [], "imports": []}
