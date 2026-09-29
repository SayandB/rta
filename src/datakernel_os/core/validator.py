"""Code safety validation for LLM-generated PySpark snippets."""

from __future__ import annotations

import ast
from typing import ClassVar


class SecurityException(RuntimeError):
    """Raised when generated code violates the sandbox constraints."""


class CodeValidator:
    """Validate that generated PySpark code stays inside a constrained namespace."""

    FORBIDDEN_CALLS: ClassVar[frozenset[str]] = frozenset(
        {
            "eval",
            "exec",
            "compile",
            "open",
            "__import__",
            "getattr",
            "setattr",
            "delattr",
        }
    )
    FORBIDDEN_ATTRIBUTES: ClassVar[frozenset[str]] = frozenset(
        {"write", "save", "saveAsTable", "dbutils", "os", "sys", "subprocess"}
    )
    ALLOWED_NAMES: ClassVar[frozenset[str]] = frozenset(
        {
            "df",
            "F",
            "col",
            "lit",
            "spark",
            "objective",
            "output_path",
            "len",
            "range",
            "list",
            "dict",
            "str",
            "int",
            "float",
            "bool",
            "print",
            "None",
            "True",
            "False",
        }
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
            self._ensure_no_imports(node)
            self._ensure_no_forbidden_calls(node)
            self._ensure_no_forbidden_attributes(node)
            self._ensure_safe_names(node)

    def _ensure_no_imports(self, node: ast.AST) -> None:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
            raise SecurityException(
                f"Forbidden code construct detected: {type(node).__name__}"
            )

    def _ensure_no_forbidden_calls(self, node: ast.AST) -> None:
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in self.FORBIDDEN_CALLS:
                raise SecurityException(
                    f"Forbidden function call detected: {node.func.id}"
                )

            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in self.FORBIDDEN_CALLS
            ):
                raise SecurityException(
                    f"Forbidden function call detected: {node.func.attr}"
                )

    def _ensure_no_forbidden_attributes(self, node: ast.AST) -> None:
        if isinstance(node, ast.Attribute) and node.attr in self.FORBIDDEN_ATTRIBUTES:
            raise SecurityException(f"Dangerous attribute access detected: {node.attr}")

        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in self.FORBIDDEN_ATTRIBUTES
        ):
            raise SecurityException(
                f"Destructive operation is not permitted: {node.func.attr}"
            )

    def _ensure_safe_names(self, node: ast.AST) -> None:
        if isinstance(node, ast.Name) and node.id not in self.ALLOWED_NAMES:
            raise SecurityException(f"Forbidden symbol detected: {node.id}")
