# Branch policy and safety rules

## Branch model

- main: production-ready and protected branch
- dev: integration branch for the next release train
- feature/*: short-lived branches for isolated work items
- hotfix/*: emergency fixes that merge directly to main after review where necessary

## Safety rules

1. All changes must be created on a feature branch or hotfix branch.
2. Pull requests must target either dev or main.
3. PRs targeting main and dev require one approval from someone other than the latest pusher.
4. The `Protect main and dev` ruleset requires `lint`, `task-linkage`, `test (3.10)`, `test (3.11)`, and `ai-review` to pass on an up-to-date branch.
5. Every PR must reference a task or issue in the PR body.
6. Documentation updates are required for changes affecting rules, workflows, or user-facing behavior.
7. No secrets, tokens, or cloud credentials may be committed to the repository.
8. Force pushes and deletion are blocked for main and dev.

## Required review comments

Every PR should include a short comment that sets out:
- what task is being completed
- why the change is needed
- what risks or dependencies exist
- what validation was run

## Merge flow

1. Work starts on a feature branch.
2. The feature branch is validated by CI.
3. The PR is opened against dev for review.
4. After dev validation, a PR is created from dev to main.
5. Merge is allowed only after the ruleset checks, maintainer approval, and review-thread resolution pass.
