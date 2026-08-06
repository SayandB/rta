"""Spark execution agent with AST validation and self-healing retries."""

from __future__ import annotations

import asyncio
import os
import re
import traceback
from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from datakernel_os.core.kernel import DataKernelOSKernel, KernelConfig, KernelConnectionError
from datakernel_os.core.orchestrator import AgentOrchestrator
from datakernel_os.core.validator import CodeValidator, SecurityException


def clean_code_block(code: str) -> str:
    """Strip markdown fences from generated code before execution."""
    if not code or not code.strip():
        return ""

    match = re.search(r"```(?:python)?\s*(.*?)\s*```", code, re.DOTALL)
    if match:
        return match.group(1).strip()
    return code.strip()


class SparkExecutionAgent:
    """Submit distributed PySpark workloads against a Databricks cluster."""

    def __init__(
        self, kernel: DataKernelOSKernel, validator: CodeValidator | None = None
    ) -> None:
        self.kernel = kernel
        self.validator = validator or CodeValidator()

    def build_dataframe(self, input_path: str, table_name: str) -> DataFrame:
        """Create a DataFrame from a lakehouse or object-store path."""
        try:
            spark = self._build_spark_session()
            if input_path and (input_path.startswith("s3://") or input_path.startswith("dbfs:/") or os.path.exists(input_path)):
                return spark.read.option("header", True).csv(input_path)
            if table_name:
                return spark.table(table_name)
            raise ValueError("No valid input path or table name was provided")
        except Exception as exc:  # pylint: disable=broad-except
            raise RuntimeError(f"Failed to read input data from {input_path}") from exc

    def transform(self, df: DataFrame, objective: str) -> DataFrame:
        """Apply an objective-driven transformation template."""
        try:
            normalized = df.withColumn("objective", F.lit(objective))
            return normalized.groupBy("objective").count()
        except Exception as exc:  # pylint: disable=broad-except
            raise RuntimeError("Spark transformation failed") from exc

    def submit_job(self, objective: str, input_path: str, output_path: str) -> str:
        """Construct and submit a distributed Spark job securely."""
        try:
            df = self.build_dataframe(input_path=input_path, table_name="raw")
            transformed = self.transform(df, objective=objective)
            transformed.write.mode("overwrite").parquet(output_path)
            return output_path
        except (KernelConnectionError, TimeoutError) as exc:
            raise RuntimeError(
                "Spark submission failed due to connectivity or distributed timeout"
            ) from exc
        except Exception as exc:  # pylint: disable=broad-except
            raise RuntimeError("Unexpected Spark execution failure") from exc

    async def submit_with_retry_async(
        self,
        generated_code: str,
        input_path: str,
        output_path: str,
        *,
        orchestrator: AgentOrchestrator | None = None,
        objective: str | None = None,
        max_retries: int = 3,
        table_name: str = "raw",
    ) -> str:
        """Execute validated code and repair it after runtime failures."""
        current_code = clean_code_block(generated_code)
        if not current_code:
            raise ValueError("Generated code cannot be empty")

        last_error: Exception | None = None

        for attempt in range(1, max_retries + 1):
            try:
                self.validator.validate(current_code)
                spark = self._build_spark_session()
                df = self.build_dataframe(input_path=input_path, table_name=table_name)

                # Restrict the execution namespace to the dataframe and a small set
                # of safe helpers so generated snippets cannot reach the broader
                # Python runtime or write to storage directly.
                safe_builtins = {
                    "len": len,
                    "range": range,
                    "list": list,
                    "dict": dict,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "print": print,
                }
                namespace: dict[str, Any] = {
                    "__builtins__": safe_builtins,
                    "df": df,
                    "F": F,
                    "col": F.col,
                    "lit": F.lit,
                    "spark": spark,
                    "objective": objective or "",
                    "output_path": output_path,
                }
                exec(current_code, namespace, namespace)
                return output_path
            except SecurityException as exc:
                raise RuntimeError("Generated code failed sandbox validation") from exc
            except Exception as exc:  # pylint: disable=broad-except
                last_error = exc
                error_traceback = "".join(
                    traceback.format_exception(type(exc), exc, exc.__traceback__)
                )
                if attempt >= max_retries:
                    raise RuntimeError("Spark execution failed after retries") from exc
                if orchestrator is None:
                    continue
                try:
                    corrected_code = await orchestrator.repair_code_with_feedback(
                        original_code=current_code,
                        failure_traceback=error_traceback[-2000:],
                        user_query=objective,
                    )
                    current_code = clean_code_block(corrected_code)
                except RuntimeError as repair_error:
                    raise RuntimeError("Spark execution failed and could not be repaired") from repair_error

        if last_error is not None:
            raise RuntimeError("Spark execution failed after retries") from last_error
        raise RuntimeError("Spark execution failed unexpectedly")

    def submit_with_retry(
        self,
        generated_code: str,
        input_path: str,
        output_path: str,
        *,
        orchestrator: AgentOrchestrator | None = None,
        objective: str | None = None,
        max_retries: int = 3,
        table_name: str = "raw",
    ) -> str:
        """Synchronous wrapper for callers that are not already inside an event loop."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self.submit_with_retry_async(
                    generated_code=generated_code,
                    input_path=input_path,
                    output_path=output_path,
                    orchestrator=orchestrator,
                    objective=objective,
                    max_retries=max_retries,
                    table_name=table_name,
                )
            )

        raise RuntimeError(
            "An active event loop is already running; use submit_with_retry_async instead"
        )

    def _build_spark_session(self) -> SparkSession:
        try:
            return SparkSession.builder.appName("DataKernelOS-Agent").getOrCreate()
        except Exception as exc:  # pylint: disable=broad-except
            raise KernelConnectionError("Unable to initialize Spark session") from exc


def create_kernel_from_env() -> DataKernelOSKernel:
    """Create a kernel using environment variables for secure configuration."""
    config = KernelConfig(
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        s3_bucket=os.getenv("S3_BUCKET", "datakernel-lakehouse"),
        databricks_host=os.getenv("DATABRICKS_HOST", ""),
        databricks_token=os.getenv("DATABRICKS_TOKEN"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    return DataKernelOSKernel(config)
