# Contributing to InsightForge

Thanks for helping improve InsightForge. Contributions should be focused, testable, and safe for a local-first application that handles user workbooks.

## Before opening an issue

- Search existing issues and discussions for duplicates.
- Use the security policy instead of a public issue for vulnerabilities.
- Remove workbook contents, credentials, tokens, and other private data from logs and screenshots.

## Development setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m insightforge
```

Development state belongs under ignored local paths such as `data/`, `.flet/`, `.tmp/`, and `.env`. Never commit generated databases, uploaded workbooks, signing certificates, or runtime secrets.

## Pull requests

1. Create a focused branch from `main`.
2. Add or update tests for behavioral changes.
3. Run the required verification commands.
4. Explain the user impact, implementation, verification, and remaining risks in the pull request.
5. Keep unrelated formatting or refactoring out of the change.

```powershell
python -m ruff check .
python -m pytest -q --basetemp .tmp\pytest-contributing
python -m pip wheel --no-deps --no-build-isolation . --wheel-dir .tmp\wheel
```

All required GitHub checks must pass before merge. Maintainers may request changes when a contribution weakens local-data isolation, authentication, packaging integrity, or accessibility.

## Release changes

Update `project.version` in `pyproject.toml` for a release. Stable releases are created only from matching `vMAJOR.MINOR.PATCH` tags. Do not move a tag after a GitHub Release has been published.

## License

By contributing, you agree that your contribution is licensed under the repository's MIT License.
