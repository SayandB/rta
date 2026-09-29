# Branch policy and safety rules

## Branch model

- main: production-ready and protected branch
- dev: integration branch for the next release train
- feature/*: short-lived branches for isolated work items
- hotfix/*: emergency fixes that merge directly to main after review where necessary

## Safety rules

1. All changes must be created on a feature branch or hotfix branch.
2. Pull requests must target either dev or main.
3. PRs targeting main require review from at least one maintainer and one AI review signal.
4. Required status checks must pass before merge: `lint`, `task-linkage`, `test (3.10)`, `test (3.11)`, and `ai-review`.
5. Every PR must reference a task or issue in the PR body.
6. Documentation updates are required for changes affecting rules, workflows, or user-facing behavior.
7. No secrets, tokens, or cloud credentials may be committed to the repository.
8. Protected branches must reject force pushes and direct pushes to `main` and `dev`.

## Required review comments

Every PR should include a short comment that sets out:
- what task is being completed
- why the change is needed
- what risks or dependencies exist
- what validation was run
- whether the change follows the GOF design and optimization guardrails in the project documentation

## Merge flow

1. Work starts on a feature branch.
2. The feature branch is validated by CI.
3. The PR is opened against dev for review.
4. The AI review workflow posts a review summary and maintains a traceable evidence trail.
5. After dev validation, a PR is created from dev to main.
6. Merge is performed only after the review checklist, required status checks, and branch ruleset pass.

## GitHub ruleset configuration

Repository administrators should configure a ruleset for `main` and `dev` following the GitHub documented best practices and enable the required status checks listed above. See [docs/project/github_ruleset_policy.md](github_ruleset_policy.md).
