## Summary

<!-- What changed and why (1–3 sentences). -->

## Type of change

- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change (API, config, or deployment)
- [ ] Refactor / chore (no user-visible behaviour change)
- [ ] Documentation only

## Related issues

<!-- Link with "Fixes #123" or "Relates to #123" when applicable. -->

## Test plan

- [ ] `uv run pytest -q` (backend changes)
- [ ] `uv run ruff check backend conf tests` and `uv run mypy backend conf` (backend changes)
- [ ] `npm run lint`, `npx tsc -b --pretty false`, and `npm run test` (frontend changes)
- [ ] Manual smoke test (describe URLs or steps):

## Checklist

- [ ] Behaviour changes include or update unit tests (success and failure paths where relevant)
- [ ] Provider URLs stay in `conf/api_urls.py`; no secrets or PII in logs or commits
- [ ] OpenAPI contract paths remain valid when API routes change
- [ ] README or operator docs updated if setup, env vars, or behaviour changed
- [ ] Docker Compose smoke path still works for deployment-impacting changes

## Screenshots / recordings

<!-- For UI changes only; otherwise remove this section. -->
