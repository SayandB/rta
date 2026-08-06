"""Code safety validation for LLM-generated PySpark snippets."""

from __future__ import annotations

import ast
from typing import Any


class SecurityException(RuntimeError):
    """Raised when generated code violates the sandbox constraints."""


class CodeValidator:
    """Validate that generated PySpark code stays within a constrained namespace."""

    ALLOWED_NAMES: tuple[str, ...] = ("df", "F")
    DISALLOWED_NODES: tuple[type[ast.AST], ...] = (
        ast.Import,
        ast.ImportFrom,
        ast.Global,
        ast.Nonlocal,
        ast.Call,
    )

    def validate(self, code: str) -> None:
        """Parse and validate the supplied Python code."""
        if not code or not code.strip():
            raise SecurityException("Generated code is empty")

        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            raise SecurityException("Generated code is not valid Python") from exc

        self._validate_tree(tree)

    def _validate_tree(self, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            self._ensure_no_forbidden_nodes(node)
            self._ensure_safe_names(node)
            self._ensure_no_destructive_writes(node)

    def _ensure_no_forbidden_nodes(self, node: ast.AST) -> None:
        if isinstance(node, self.DISALLOWED_NODES):
            raise SecurityException(f"Forbidden code construct detected: {type(node).__name__}")

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"eval", "exec", "compile"}:
                raise SecurityException(
                    f"Forbidden function call detected: {node.func.attr}"
                )

    def _ensure_safe_names(self, node: ast.AST) -> None:
        if isinstance(node, ast.Name):
            if node.id not in self.ALLOWED_NAMES and node.id != "None":
                raise SecurityException(f"Forbidden symbol detected: {node.id}")

    def _ensure_no_destructive_writes(self, node: ast.AST) -> None:
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.attr in {"write", "saveAsTable", "dbutils"}:
                raise SecurityException(f"Dangerous DataFrame operation detected: {node.attr}")

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"write", "saveAsTable"}:
                raise SecurityException(
                    f"Destructive write operation is not permitted: {node.func.attr}"
                )
