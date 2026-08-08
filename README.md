# InsightForge

InsightForge is a Python-first Excel analytics workspace with a shared Flet UI for Windows desktop and browser deployments. It provides secure local-first authentication, workbook profiling, visual analysis, saved dashboards, and exportable insights.

Proudly vibe-coded by [Harshit Garg](https://harshit-garg.com/)—an experiment in turning product instinct, rapid iteration, and AI-assisted development into a real, installable desktop app.

## Publisher

- **Author:** Harshit Garg
- **Publisher:** Harshit Garg Inc.
- **Email:** harshit.garg@harshit-garg.com
- **Phone:** +1 301-525-7100
- **Website and updates:** [harshit-garg.com](https://harshit-garg.com/)
- **Copyright:** Copyright (c) 2026 Harshit Garg. All rights reserved.

These public publisher details are embedded in the Windows executable metadata, installer properties, and the Apps & Features uninstall record.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m insightforge
```

The desktop command starts a local FastAPI service on `127.0.0.1:8765` and opens the Flet application. Development runs use SQLite under `data/` and print password-reset links to the console instead of sending email.

Packaged Windows installations use Flet's writable per-user application-data directory for the database, uploaded workbooks, exports, and a generated local signing secret. Application data therefore survives installer upgrades and is never written beneath the installation directory.

To run only the API:

```powershell
python -m insightforge.api.server
```

To open the shared UI against an already-running API:

```powershell
$env:INSIGHTFORGE_API_URL = "http://127.0.0.1:8765"
flet run insightforge/ui/app.py
```

## Product surface

- Login, signup, logout, refresh, and one-time password reset flows.
- Excel upload with sheet selection, preview, schema inference, quality score, missing-value and duplicate analysis.
- Searchable dataset library and reusable analysis workspaces.
- KPI cards, trend and anomaly insight cards, and configurable Plotly visualizations.
- Dashboard cards that can be reordered, hidden, and saved per user.
- CSV/XLSX exports and a local development mail adapter.

## Architecture

The Flet client is deliberately thin: it renders state and calls the typed HTTP API. The API owns authentication, storage, parsing, analytics, and authorization. Desktop mode launches the API locally; browser mode points at a deployed API through `INSIGHTFORGE_API_URL`.

## Verification

```powershell
python -m pytest -q
python -m compileall insightforge tests
```

## Windows installer

InsightForge uses a two-stage Windows distribution pipeline:

1. Flet builds a self-contained 64-bit Windows application with bundled Python.
2. Inno Setup 7 creates a per-user installer with Start Menu integration, optional desktop shortcut, upgrade/uninstall support, LZMA2 compression, and optional Authenticode signing.

Prerequisites:

- Visual Studio with the Desktop development with C++ workload.
- Inno Setup 7 (64-bit edition recommended).
- The project virtual environment installed with `.[dev]`.

Build the installer from PowerShell:

```powershell
.\scripts\build_installer.ps1
```

For a clean, Authenticode-signed release:

```powershell
.\scripts\build_installer.ps1 `
  -Clean `
  -Version 0.1.0 `
  -BuildNumber 1 `
  -CertificateThumbprint "YOUR_CERTIFICATE_THUMBPRINT"
```

Release artifacts are written to `dist/`:

- `InsightForge-<version>-Setup.exe`
- `InsightForge-<version>-Setup.exe.sha256`

### Automated tagged releases

Pushing a stable semantic-version tag automatically builds the Windows installer, preserves it as a workflow artifact, creates a GitHub Release with generated notes, and attaches the installer and SHA-256 checksum:

```powershell
# First update the version in pyproject.toml, commit it, then:
git tag v0.2.0
git push origin v0.2.0
```

The tag must use `vMAJOR.MINOR.PATCH` and its version must match `project.version` in `pyproject.toml`. Other tags do not publish releases.

Release builds are unsigned unless the repository secrets `WINDOWS_SIGNING_CERTIFICATE_BASE64` and `WINDOWS_SIGNING_CERTIFICATE_PASSWORD` contain an Authenticode PFX certificate and its password. When configured, CI imports the certificate only for the build and removes it afterward.

The unsigned development installer is suitable for local QA. Public distribution should always use Authenticode signing so Windows can verify the publisher and integrity of the executable, installer, and uninstaller.
