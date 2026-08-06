"""Spark execution agent template for DataKernel-OS."""

from __future__ import annotations

import os
from typing import Any, Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from datakernel_os.core.kernel import DataKernelOSKernel, KernelConfig, KernelConnectionError


class SparkExecutionAgent:
    """Submit distributed PySpark workloads against a Databricks cluster."""

    # The agent intentionally keeps its execution pathway simple so it can be extended
    # into richer planning and optimization loops later.

    def __init__(self, kernel: DataKernelOSKernel) -> None:
        self.kernel = kernel

    def build_dataframe(self, input_path: str, table_name: str) -> DataFrame:
        """Create a DataFrame from a lakehouse or object-store path."""
        try:
            spark = self._build_spark_session()
            return spark.read.option("header", True).csv(input_path)
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
            spark = self._build_spark_session()
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
