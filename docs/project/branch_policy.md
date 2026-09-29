# Branch policy and safety rules

## Branch model

- main: production-ready and protected branch
- dev: integration branch for the next release train
- feature/*: short-lived branches for isolated work items
- hotfix/*: emergency fixes that merge directly to main after review where necessary

## Safety rules

1. All changes must be created on a feature branch or hotfix branch.
2. Pull requests must target either dev or main.
3. PRs targeting main require review from at least one maintainer.
4. CI must pass before merge.
5. Every PR must reference a task or issue in the PR body.
6. Documentation updates are required for changes affecting rules, workflows, or user-facing behavior.
7. No secrets, tokens, or cloud credentials may be committed to the repository.

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
5. Merge is performed only after the review checklist and CI checks pass.
