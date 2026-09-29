# Merge Checklist

Use this checklist before merging a pull request into main.

## Required checks
- [ ] All CI checks are passing, including `lint`, `task-linkage`, `test (3.10)`, `test (3.11)`, and `ai-review`.
- [ ] Tests are added or updated for behavior changes.
- [ ] Documentation is updated when user-facing behavior changes.
- [ ] No secrets or credentials are committed.
- [ ] The change is reviewed by at least one maintainer and the AI review summary is present.
- [ ] The design remains aligned with the GOF guidelines and avoids unnecessary complexity.

## Review expectations
- [ ] The PR description clearly explains the change and its impact.
- [ ] The scope of the change is limited and easy to review.
- [ ] Breaking changes are called out explicitly.

## Merge readiness
- [ ] The branch is up to date with main.
- [ ] The merge commit message is clear and descriptive.
