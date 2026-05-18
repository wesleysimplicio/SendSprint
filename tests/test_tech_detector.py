"""Tests for sendsprint/tech/detector.py — detect_tech(repo_path) -> TechFingerprint."""

import json
from pathlib import Path

import pytest

from sendsprint.tech.detector import TechFingerprint, detect_tech

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pkg(
    tmp_path: Path,
    dependencies: dict | None = None,
    dev_dependencies: dict | None = None,
) -> None:
    data: dict = {}
    if dependencies is not None:
        data["dependencies"] = dependencies
    if dev_dependencies is not None:
        data["devDependencies"] = dev_dependencies
    (tmp_path / "package.json").write_text(json.dumps(data), encoding="utf-8")


def _requirements(tmp_path: Path, *packages: str) -> None:
    (tmp_path / "requirements.txt").write_text("\n".join(packages) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Empty repo
# ---------------------------------------------------------------------------


def test_empty_repo(tmp_path: Path) -> None:
    fp = detect_tech(tmp_path)
    assert isinstance(fp, TechFingerprint)
    assert fp.techs == []
    assert fp.roles == ["other"]


# ---------------------------------------------------------------------------
# 2. Node repo — package.json with no framework deps
# ---------------------------------------------------------------------------


def test_node_repo(tmp_path: Path) -> None:
    _pkg(tmp_path, dependencies={"lodash": "^4.17.21"})
    fp = detect_tech(tmp_path)
    assert "node" in fp.techs
    assert "npm" in fp.package_managers


# ---------------------------------------------------------------------------
# 3. Angular repo
# ---------------------------------------------------------------------------


def test_angular_repo(tmp_path: Path) -> None:
    _pkg(tmp_path, dependencies={"@angular/core": "^17.0.0"})
    fp = detect_tech(tmp_path)
    assert "angular" in fp.techs
    assert "front" in fp.roles


# ---------------------------------------------------------------------------
# 4. React repo
# ---------------------------------------------------------------------------


def test_react_repo(tmp_path: Path) -> None:
    _pkg(tmp_path, dependencies={"react": "^18.0.0", "react-dom": "^18.0.0"})
    fp = detect_tech(tmp_path)
    assert "react" in fp.techs


# ---------------------------------------------------------------------------
# 5. Next.js repo (react + next)
# ---------------------------------------------------------------------------


def test_nextjs_repo(tmp_path: Path) -> None:
    _pkg(tmp_path, dependencies={"react": "^18.0.0", "next": "^14.0.0"})
    fp = detect_tech(tmp_path)
    assert "nextjs" in fp.techs


# ---------------------------------------------------------------------------
# 6. Python repo — requirements.txt without a framework
# ---------------------------------------------------------------------------


def test_python_repo(tmp_path: Path) -> None:
    _requirements(tmp_path, "requests>=2.31.0", "pydantic>=2.0.0")
    fp = detect_tech(tmp_path)
    assert "python" in fp.techs
    assert "pip" in fp.package_managers


# ---------------------------------------------------------------------------
# 7. Django repo
# ---------------------------------------------------------------------------


def test_django_repo(tmp_path: Path) -> None:
    _requirements(tmp_path, "Django>=4.2", "djangorestframework>=3.14")
    fp = detect_tech(tmp_path)
    assert "django" in fp.techs


# ---------------------------------------------------------------------------
# 8. .NET repo — empty .csproj file
# ---------------------------------------------------------------------------


def test_dotnet_repo(tmp_path: Path) -> None:
    (tmp_path / "MyApp.csproj").write_text("", encoding="utf-8")
    fp = detect_tech(tmp_path)
    assert "dotnet" in fp.techs
    assert "nuget" in fp.package_managers


# ---------------------------------------------------------------------------
# 9. Go repo
# ---------------------------------------------------------------------------


def test_go_repo(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module example.com/myapp\n\ngo 1.22\n", encoding="utf-8")
    fp = detect_tech(tmp_path)
    assert "go" in fp.techs


# ---------------------------------------------------------------------------
# 10. Rust repo
# ---------------------------------------------------------------------------


def test_rust_repo(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "myapp"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    fp = detect_tech(tmp_path)
    assert "rust" in fp.techs
    assert "cargo" in fp.package_managers


# ---------------------------------------------------------------------------
# 11. Flutter repo
# ---------------------------------------------------------------------------


def test_flutter_repo(tmp_path: Path) -> None:
    (tmp_path / "pubspec.yaml").write_text(
        "name: myapp\nenvironment:\n  sdk: '>=3.0.0 <4.0.0'\n", encoding="utf-8"
    )
    fp = detect_tech(tmp_path)
    assert "flutter" in fp.techs
    assert "mobile" in fp.roles


# ---------------------------------------------------------------------------
# 12. Docker-only repo
# ---------------------------------------------------------------------------


def test_docker_only_repo(tmp_path: Path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM alpine:3.19\n", encoding="utf-8")
    fp = detect_tech(tmp_path)
    assert "docker" in fp.techs
    assert "infra" in fp.roles


# ---------------------------------------------------------------------------
# 13. Non-existent path raises FileNotFoundError
# ---------------------------------------------------------------------------


def test_nonexistent_path_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        detect_tech(missing)


# ---------------------------------------------------------------------------
# 14. primary_tech and primary_role properties
# ---------------------------------------------------------------------------


def test_primary_tech_and_role(tmp_path: Path) -> None:
    _pkg(tmp_path, dependencies={"@angular/core": "^17.0.0"})
    fp = detect_tech(tmp_path)
    assert fp.primary_tech == fp.techs[0]
    assert fp.primary_role == fp.roles[0]


def test_primary_tech_none_on_empty(tmp_path: Path) -> None:
    fp = detect_tech(tmp_path)
    assert fp.primary_tech is None


def test_primary_role_other_on_empty(tmp_path: Path) -> None:
    fp = detect_tech(tmp_path)
    assert fp.primary_role == "other"


# ---------------------------------------------------------------------------
# 15. Bun runtime detection (TASK-001)
# ---------------------------------------------------------------------------


def test_detector_bun_only(tmp_path: Path) -> None:
    """AC-1: bun.lockb alone returns ['bun']."""
    (tmp_path / "bun.lockb").write_bytes(b"\x00binary lockfile")
    fp = detect_tech(tmp_path)
    assert "bun" in fp.techs
    assert "bun" in fp.package_managers
    assert fp.primary_tech == "bun"


def test_detector_bun_wins_over_node(tmp_path: Path) -> None:
    """AC-2: bun.lockb + package.json (no framework) → bun beats generic node."""
    (tmp_path / "bun.lockb").write_bytes(b"\x00binary lockfile")
    _pkg(tmp_path, dependencies={"lodash": "^4.17.21"})
    fp = detect_tech(tmp_path)
    assert "bun" in fp.techs
    assert "node" not in fp.techs
    assert fp.primary_tech == "bun"


def test_detector_bun_with_framework(tmp_path: Path) -> None:
    """Bun runtime + React framework: both detected."""
    (tmp_path / "bun.lockb").write_bytes(b"\x00")
    _pkg(tmp_path, dependencies={"react": "^18.0.0"})
    fp = detect_tech(tmp_path)
    assert "bun" in fp.techs
    assert "react" in fp.techs
    assert "node" not in fp.techs


def test_detector_bunfig_marker(tmp_path: Path) -> None:
    """bunfig.toml alone (no lockfile) also detects bun."""
    (tmp_path / "bunfig.toml").write_text('[install]\nregistry = "https://registry.npmjs.org"\n')
    fp = detect_tech(tmp_path)
    assert "bun" in fp.techs


def test_detector_bun_role_back(tmp_path: Path) -> None:
    """Bun without a frontend framework is a back-end runtime."""
    (tmp_path / "bun.lockb").write_bytes(b"\x00")
    fp = detect_tech(tmp_path)
    assert "back" in fp.roles


# ---------------------------------------------------------------------------
# 16. Deno runtime detection (Sprint 3 issue #12)
# ---------------------------------------------------------------------------


def test_detector_deno_json(tmp_path: Path) -> None:
    (tmp_path / "deno.json").write_text("{}")
    fp = detect_tech(tmp_path)
    assert "deno" in fp.techs
    assert "deno" in fp.package_managers


def test_detector_deno_jsonc(tmp_path: Path) -> None:
    (tmp_path / "deno.jsonc").write_text("{}")
    fp = detect_tech(tmp_path)
    assert "deno" in fp.techs


def test_detector_deno_lock(tmp_path: Path) -> None:
    (tmp_path / "deno.lock").write_text('{"version":"3"}')
    fp = detect_tech(tmp_path)
    assert "deno" in fp.techs


def test_detector_deno_wins_over_node(tmp_path: Path) -> None:
    """Deno + package.json (rare) keeps deno as primary, drops generic node."""
    (tmp_path / "deno.json").write_text("{}")
    _pkg(tmp_path, dependencies={"lodash": "^4.17.21"})
    fp = detect_tech(tmp_path)
    assert "deno" in fp.techs
    assert "node" not in fp.techs


def test_detector_deno_role_back(tmp_path: Path) -> None:
    (tmp_path / "deno.json").write_text("{}")
    fp = detect_tech(tmp_path)
    assert "back" in fp.roles
