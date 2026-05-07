"""Unit tests for sendsprint/architecture/builder.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from sendsprint.architecture import ArchitectureBuildResult, build_architecture
from sendsprint.tech import TechFingerprint

EXPECTED_FILES = [
    "README.md",
    "ARCHITECTURE.md",
    "docs/architecture/overview.md",
    "docs/adr/0001-initial.md",
    "docs/dependencies.md",
    "docs/deploy.md",
]


# ---------------------------------------------------------------------------
# Test 1 – empty repo creates all 6 files, score >= 0.6, is_mapped True
# ---------------------------------------------------------------------------


def test_empty_repo_creates_all_files(tmp_path: Path) -> None:
    result = build_architecture(tmp_path)

    assert isinstance(result, ArchitectureBuildResult)
    assert len(result.created_files) == 6
    assert result.skipped_files == []
    assert result.final_score >= 0.6
    assert result.is_mapped is True

    for rel in EXPECTED_FILES:
        assert (tmp_path / rel).exists(), f"expected {rel} to be created"


# ---------------------------------------------------------------------------
# Test 2 – repo with existing README.md skips it, creates the other 5
# ---------------------------------------------------------------------------


def test_existing_readme_is_skipped(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Existing README\n", encoding="utf-8")

    result = build_architecture(tmp_path)

    assert len(result.created_files) == 5
    assert len(result.skipped_files) == 1
    assert str(readme) in result.skipped_files

    # Remaining 5 files must have been created
    for rel in EXPECTED_FILES:
        if rel != "README.md":
            assert (tmp_path / rel).exists(), f"expected {rel} to be created"

    # Original README content must be unchanged
    assert readme.read_text(encoding="utf-8") == "# Existing README\n"


# ---------------------------------------------------------------------------
# Test 3 – all files already present: no creation, all skipped
# ---------------------------------------------------------------------------


def test_all_files_present_skips_all(tmp_path: Path) -> None:
    for rel in EXPECTED_FILES:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"# {rel}\n", encoding="utf-8")

    result = build_architecture(tmp_path)

    assert result.created_files == []
    assert len(result.skipped_files) == 6


# ---------------------------------------------------------------------------
# Test 4 – non-existent repo_path raises FileNotFoundError
# ---------------------------------------------------------------------------


def test_nonexistent_path_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    with pytest.raises(FileNotFoundError):
        build_architecture(missing)


# ---------------------------------------------------------------------------
# Test 5 – custom repo_name appears in generated content
# ---------------------------------------------------------------------------


def test_custom_repo_name_in_content(tmp_path: Path) -> None:
    custom_name = "my-custom-project"
    result = build_architecture(tmp_path, repo_name=custom_name)

    assert result.repo_name == custom_name

    readme_text = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert custom_name in readme_text

    arch_text = (tmp_path / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert custom_name in arch_text


# ---------------------------------------------------------------------------
# Test 6 – passing a fingerprint uses it instead of auto-detecting
# ---------------------------------------------------------------------------


def test_passed_fingerprint_is_used(tmp_path: Path) -> None:
    fp = TechFingerprint(
        repo_path=str(tmp_path),
        techs=["python"],
        roles=["back"],
        package_managers=["pip"],
    )

    result = build_architecture(tmp_path, fingerprint=fp)

    assert result.fingerprint is fp

    # The supplied fingerprint data must appear in at least one generated file
    readme_text = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "python" in readme_text.lower()
    assert "pip" in readme_text.lower()
