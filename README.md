# DataKernel-OS

DataKernel-OS is an AI-native operating system kernel for distributed enterprise lakehouses. It maps storage and execution concerns to AWS S3 and Databricks while orchestrating autonomous Spark agents for data engineering workloads.

## Why this project exists

Rta is designed to make lakehouse operations feel like interacting with a distributed operating system rather than a collection of isolated tools. You can describe an intent in plain English, and the platform routes that intent into PySpark logic, orchestration, and execution flows.

## Key capabilities

- AI-assisted translation of natural language requests into PySpark logic
- Secure connectivity to S3 and Databricks through typed kernel abstractions
- An interactive terminal shell for experimenting with intents and generated jobs
- A modular structure for growing into richer agent-based orchestration workflows

## Repository layout

- [infra/terraform](infra/terraform): foundational infrastructure for S3 and Databricks
- [src/datakernel_os/core](src/datakernel_os/core): kernel abstractions and secure connectivity helpers
- [src/datakernel_os/agents](src/datakernel_os/agents): Spark execution agents and workload templates
- [src/datakernel_os/core/orchestrator.py](src/datakernel_os/core/orchestrator.py): natural-language to PySpark translation layer
- [src/datakernel_os/cli.py](src/datakernel_os/cli.py): interactive shell experience
- [tests](tests): regression and integration coverage for the platform foundation

## Quick start

### 1. Prerequisites

Make sure you have:

- Python 3.10 or newer
- Access to an AWS account with S3 access
- A Databricks workspace and personal access token
- An OmniRoute-compatible local gateway if you want LLM-based translation

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the sample environment file and update it:

```bash
cp .env.example .env
```

Then set the required values:

- AWS_REGION
- S3_BUCKET
- DATABRICKS_HOST
- DATABRICKS_TOKEN
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- OMNIROUTE_API_KEY

### 4. Run the shell

Start the interactive shell:

```bash
python -m datakernel_os.cli
```

Example prompts:

```text
summarize the uploaded dataset
create a PySpark job that counts rows by category
show me a simple data transformation for the input files
```

The shell will attempt to generate PySpark code from your request and display it for inspection.

## Example usage

### Translate a request into PySpark

The orchestrator can be used programmatically:

```python
import asyncio
from datakernel_os.core.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator()
result = asyncio.run(orchestrator.translate_intent_to_spark("count rows by region"))
print(result)
```

### Run the test suite

```bash
pytest -q
```

## How to contribute

Contributions are welcome. A good contribution path is:

1. Fork the repository.
2. Create a feature branch with a descriptive name such as `feature/add-new-agent`.
3. Make your changes and add or update tests.
4. Run the tests locally.
5. Open a pull request with a clear summary of the change.

Please keep changes focused, documented, and easy to review. If you are introducing new functionality, include examples or notes in the README where helpful.

## Development notes

This repository currently establishes the foundation for the platform and is intended to evolve into a full distributed kernel runtime. Future work will focus on richer agent coordination, self-healing workflows, and deeper integration with cloud-native data platforms.
