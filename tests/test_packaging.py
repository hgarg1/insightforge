import re
import socket
import tomllib
from pathlib import Path

import insightforge.desktop as desktop
from insightforge.core.config import (
    _default_database_url,
    _default_secret_key,
    _default_storage_dir,
)
from insightforge.desktop import _available_port, _initial_auth_mode
from insightforge.runtime_log import log_runtime, reset_runtime_log

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_packaged_defaults_use_flet_user_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    monkeypatch.delenv("INSIGHTFORGE_SECRET_KEY", raising=False)

    assert _default_storage_dir() == tmp_path
    assert _default_database_url() == f"sqlite:///{(tmp_path / 'insightforge.db').as_posix()}"

    first_key = _default_secret_key()
    assert len(first_key) >= 48
    assert _default_secret_key() == first_key
    assert (tmp_path / ".secret-key").read_text(encoding="utf-8") == first_key


def test_packaged_desktop_chooses_an_open_loopback_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen()
        used_port = occupied.getsockname()[1]

        selected = _available_port(used_port)

    assert selected != used_port
    assert 0 < selected <= 65535


def test_packaged_auth_mode_override_is_bounded(monkeypatch):
    monkeypatch.setenv("INSIGHTFORGE_INITIAL_AUTH_MODE", "signup")
    assert _initial_auth_mode() == "signup"

    monkeypatch.setenv("INSIGHTFORGE_INITIAL_AUTH_MODE", "unsupported")
    assert _initial_auth_mode() == "login"


def test_packaged_entrypoint_starts_the_flet_runner(monkeypatch):
    captured = {}

    def fake_run(target, **kwargs):
        captured["target"] = target
        captured["kwargs"] = kwargs

    monkeypatch.setattr(desktop.ft, "run", fake_run)

    desktop.run_app()

    assert captured == {"target": desktop.main, "kwargs": {"assets_dir": "assets"}}


def test_packaged_runtime_log_records_startup_diagnostics(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))

    reset_runtime_log()
    log_runtime("UI mounted")

    assert "UI mounted" in (tmp_path / "runtime.log").read_text(encoding="utf-8")


def test_release_metadata_identifies_the_publisher():
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    installer = (PROJECT_ROOT / "installer" / "InsightForge.iss").read_text(
        encoding="utf-8"
    )

    assert project["project"]["authors"] == [
        {"name": "Harshit Garg", "email": "harshit.garg@harshit-garg.com"}
    ]
    assert project["project"]["license"] == "MIT"
    assert (PROJECT_ROOT / "LICENSE").is_file()
    assert project["tool"]["flet"]["company"] == "Harshit Garg Inc."
    assert project["tool"]["flet"]["bundle_id"] == "com.harshitgarg.insightforge"
    assert project["project"]["urls"]["Support"].startswith("https://")
    assert '#define MyAppPublisher "Harshit Garg Inc."' in installer
    assert '#define MyAppSupportPhone "+1 301-525-7100"' in installer
    assert "AppPublisherURL={#MyAppWebsite}" in installer
    assert "AppSupportURL={#MyAppSupportURL}" in installer
    assert "LicenseFile={#SourcePath}\\EULA.txt" in installer


def test_release_bundle_excludes_private_development_state():
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    build_script = (PROJECT_ROOT / "scripts" / "build_installer.ps1").read_text(
        encoding="utf-8"
    )

    excludes = project["tool"]["flet"]["app"]["exclude"]
    assert {".env", ".flet", "data"}.issubset(excludes)
    assert 'Join-Path $appBundle "app\\.flet"' in build_script
    assert "Release bundle contains private development data" in build_script


def test_tagged_release_workflow_builds_and_publishes_installer():
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )

    assert '      - "v*.*.*"' in workflow
    assert "contents: write" in workflow
    assert "id-token: write" in workflow
    assert "attestations: write" in workflow
    assert "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd" in workflow
    assert "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405" in workflow
    assert "JRSoftware.InnoSetup.7" in workflow
    assert "Tag version $version does not match pyproject.toml version" in workflow
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in workflow
    assert workflow.count("actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6") == 2
    assert "cyclonedx-py.exe environment" in workflow
    assert "InsightForge-$env:RELEASE_VERSION.cdx.json" in workflow
    assert "gh release create $env:GITHUB_REF_NAME" in workflow
    assert "--verify-tag" in workflow
    assert "--generate-notes" in workflow


def test_continuous_integration_workflow_covers_quality_gates():
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "pull_request:" in workflow
    assert "contents: read" in workflow
    assert "python.exe -m ruff check" in workflow
    assert "python.exe -m pytest" in workflow
    assert "pip wheel --no-deps ." in workflow
    assert "actionlint/cmd/actionlint@v1.7.12" in workflow


def test_public_repository_health_and_supply_chain_files_are_present():
    required_files = {
        "LICENSE",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        ".github/CODEOWNERS",
        ".github/dependabot.yml",
        ".github/pull_request_template.md",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/ISSUE_TEMPLATE/config.yml",
    }

    assert all((PROJECT_ROOT / path).is_file() for path in required_files)

    workflows = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (PROJECT_ROOT / ".github" / "workflows").glob("*.yml")
    )
    assert not re.search(r"uses:\s+actions/[^@\s]+@v\d", workflows)
