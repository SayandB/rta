# GitHub ruleset policy

These repository settings should be enforced in GitHub under Repository settings -> Rules -> Rulesets.

## Recommended ruleset

Create a ruleset for `main` and `dev` with the following requirements:

- Require a pull request before merging
- Require approvals: 1 reviewer minimum for feature branches; 2 for direct changes to `main`
- Require status checks to pass before merge
- Require branches to be up to date before merge
- Require conversation resolution before merge
- Restrict force pushes
- Prevent deletions of protected branches

## Required status checks

Use the following exact check names in the ruleset requirement list:

- `lint`
- `task-linkage`
- `test (3.10)`
- `test (3.11)`
- `ai-review`

The AI review job uses GitHub's Copilot inference action. Add an Actions repository secret named `COPILOT_PAT` containing a token authorized for Copilot CLI inference; the workflow intentionally fails closed when the secret is absent or the model returns no review.

## Merge policy

- Feature branches merge into `dev` only.
- `dev` merges into `main` only after all status checks are green and review is complete.
- PRs must include a task or issue reference using `Fixes #`, `Closes #`, or `Task:`.
- Any PR touching runtime safety, orchestration, or data execution must include security review plus validation evidence.

The AI review is advisory and does not replace maintainer approval. Reviewers remain responsible for validating findings and resolving conversations.

## Why this follows GitHub best practices

This pattern follows the current GitHub ruleset guidance for protected branches: enforce a review path, require passes from CI, prevent direct pushes, and ensure all merge decisions are backed by traceable signals instead of ad hoc approvals.
