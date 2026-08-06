# DataKernel-OS

DataKernel-OS is an AI-native operating system kernel for distributed enterprise lakehouses. It maps storage and execution concerns to AWS S3 and Databricks while orchestrating autonomous Spark agents for data engineering workloads.

## Repository layout

- infra/terraform: foundational infrastructure for S3 and Databricks
- src/datakernel_os/core: kernel abstractions and secure connectivity helpers
- src/datakernel_os/agents: Spark execution agents and workload templates
- src/datakernel_os/core/orchestrator.py: natural-language to PySpark translation layer
- src/datakernel_os/cli.py: interactive shell experience
- tests: regression and integration coverage for the platform foundation

## Quick start

1. Install Python dependencies: `pip install -r requirements.txt`
2. Review the Terraform configuration in infra/terraform/main.tf
3. Configure the following environment variables before running agent workflows:
   - AWS_REGION
   - S3_BUCKET
   - DATABRICKS_HOST
   - DATABRICKS_TOKEN
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - OMNIROUTE_API_KEY

## Running the shell

Start the interactive shell with:

```bash
python -m datakernel_os.cli
```

Type natural language requests such as "summarize the uploaded dataset" and the shell will attempt to generate and display PySpark code.

## Testing

Run the test suite with:

```bash
pytest -q
```

## Notes

This repository currently establishes the initial foundation for the platform and is intended to evolve into a full distributed kernel runtime.
