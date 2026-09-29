"""Schema inspection helpers that query Databricks Unity Catalog metadata."""

from __future__ import annotations

import os
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import DatabricksError

from datakernel_os.core.kernel import KernelConnectionError


class SchemaInspector:
    """Inspect Databricks table schemas for orchestration context."""

    def __init__(self, workspace_client: WorkspaceClient | None = None) -> None:
        self.workspace_client = workspace_client

    def get_table_schema(
        self, catalog: str, schema: str, table: str
    ) -> list[dict[str, Any]]:
        """Retrieve column metadata for a Unity Catalog table."""
        if not self.workspace_client:
            token = os.getenv("DATABRICKS_TOKEN")
            if not token:
                raise KernelConnectionError("Databricks token is not configured")
            self.workspace_client = WorkspaceClient(
                host=os.getenv("DATABRICKS_HOST", ""),
                token=token,
            )

        try:
            columns = self.workspace_client.tables.get(column_name="*")
        except DatabricksError as exc:
            raise KernelConnectionError(
                f"Unable to inspect schema for {catalog}.{schema}.{table}"
            ) from exc

        return [
            {
                "name": getattr(column, "name", ""),
                "type_name": getattr(column, "type_name", ""),
                "comment": getattr(column, "comment", ""),
            }
            for column in getattr(columns, "columns", [])
        ]
