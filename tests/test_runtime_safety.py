"""Regression tests for the runtime safety and execution loop."""

from __future__ import annotations

import pytest

from datakernel_os.agents.spark_agent import clean_code_block
from datakernel_os.core.kernel import DataKernelOSKernel, KernelConfig
from datakernel_os.core.validator import CodeValidator, SecurityException


def test_clean_code_block_removes_markdown_fences() -> None:
    assert clean_code_block("```python\nprint('hi')\n```") == "print('hi')"


def test_validator_allows_standard_pyspark_transformations() -> None:
    validator = CodeValidator()
    code = "df.select(F.col('id')).filter(F.col('amount') > 0)"

    validator.validate(code)


def test_validator_blocks_destructive_writes() -> None:
    validator = CodeValidator()

    with pytest.raises(SecurityException):
        validator.validate("df.write.mode('overwrite').parquet('output')")


def test_kernel_properties_initialise_lazily(monkeypatch: pytest.MonkeyPatch) -> None:
    config = KernelConfig(
        aws_region="us-east-1",
        s3_bucket="demo-bucket",
        databricks_host="https://example.databricks.com",
    )
    kernel = DataKernelOSKernel(config)

    monkeypatch.setattr(kernel, "_initialize_s3_client", lambda: {"s3": True})
    monkeypatch.setattr(kernel, "_initialize_workspace_client", lambda: {"workspace": True})

    assert kernel.s3_client == {"s3": True}
    assert kernel.workspace_client == {"workspace": True}
