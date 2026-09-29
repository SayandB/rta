# Bounded backlog runner

The backlog runner executes one pending task per invocation and persists each state transition to `backlog.json`.

## Verification contract

- Tasks declare verification as an array of argument arrays, never shell strings.
- Commands must exactly match the runner's allowlist: Ruff checks/format validation and approved pytest invocations.
- Each command has a timeout; output is truncated before being persisted.
- Status is atomically written as `running`, then `completed` or `blocked`.
- At most three remediation retries are permitted. A remediation handler must be explicitly supplied by trusted application code; no model-generated patch is applied by default.
- The runner never commits, pushes, merges, or changes branches. Human review and GitHub branch rules remain the release gate.

## Run

Install the development requirements, then invoke:

```bash
PYTHONPATH=src python -m datakernel_os.autonomy.backlog --backlog backlog.json
```

Run it once per task to preserve an auditable, bounded execution loop. The exit code is non-zero if verification is blocked.

## Adding tasks

Add a unique task id, concise description, exact allowlisted verification command arrays, and `pending` status. Do not put credentials, arbitrary shell commands, or model-authored executable patches in the backlog.
