"""Core kernel abstractions for DataKernel-OS."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

from dotenv import load_dotenv

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import DatabricksError

load_dotenv()


class KernelConnectionError(RuntimeError):
    """Raised when the kernel cannot reach S3 or Databricks."""


@dataclass(slots=True)
class KernelConfig:
    """Configuration for the kernel runtime."""

    aws_region: str
    s3_bucket: str
    databricks_host: str
    databricks_token: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None


class DataKernelOSKernel:
    """Base kernel for connecting to Lakehouse storage and Spark compute."""

    def __init__(self, config: KernelConfig) -> None:
        self.config = config
        # Keep the lazily initialized client handles in private attributes so the
        # public properties can be read safely after construction.
        self._s3_client: Optional[Any] = None
        self._workspace_client: Optional[WorkspaceClient] = None

    @property
    def s3_client(self) -> Any:
        if self._s3_client is None:
            self._s3_client = self._initialize_s3_client()
        return self._s3_client

    @property
    def workspace_client(self) -> WorkspaceClient:
        if self._workspace_client is None:
            self._workspace_client = self._initialize_workspace_client()
        return self._workspace_client

    def _initialize_s3_client(self) -> Any:
        try:
            session_kwargs: dict[str, Any] = {"region_name": self.config.aws_region}
            if self.config.aws_access_key_id and self.config.aws_secret_access_key:
                session_kwargs.update(
                    {
                        "aws_access_key_id": self.config.aws_access_key_id,
                        "aws_secret_access_key": self.config.aws_secret_access_key,
                    }
                )

            session = boto3.session.Session(**session_kwargs)
            client = session.client("s3")
            client.head_bucket(Bucket=self.config.s3_bucket)
            return client
        except (BotoCoreError, ClientError, ValueError) as exc:
            raise KernelConnectionError(
                f"Unable to connect to S3 bucket '{self.config.s3_bucket}'"
            ) from exc

    def _initialize_workspace_client(self) -> WorkspaceClient:
        try:
            token = self.config.databricks_token or os.getenv("DATABRICKS_TOKEN")
            if not token:
                raise KernelConnectionError("Databricks token is not configured")

            client = WorkspaceClient(host=self.config.databricks_host, token=token)
            client.config.host = self.config.databricks_host
            client.config.token = token
            return client
        except (DatabricksError, ValueError) as exc:
            raise KernelConnectionError(
                f"Unable to connect to Databricks workspace '{self.config.databricks_host}'"
            ) from exc

    def ping(self) -> bool:
        """Validate connectivity to the configured storage and compute planes."""
        try:
            self.s3_client.head_bucket(Bucket=self.config.s3_bucket)
            self.workspace_client.config.host
            return True
        except (KernelConnectionError, BotoCoreError, ClientError, DatabricksError) as exc:
            raise KernelConnectionError("Kernel connectivity check failed") from exc
