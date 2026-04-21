"""M6 design-partner surface: docs exist, metadata honest, packaging buildable."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_design_partner_eval_and_release_evaluator_docs_exist() -> None:
    root = _repo_root()
    assert (root / "docs/azimuth_bench/DESIGN_PARTNER_EVAL.md").is_file()
    assert (root / "release/evaluator/README.md").is_file()


def test_pyproject_names_distribution_and_console_scripts() -> None:
    text = (_repo_root() / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "benchmark-v2"' in text
    assert 'license = "MIT"' in text
    assert 'license = {text = "MIT"}' not in text
    assert 'azbench = "azimuth_bench.cli.entrypoint:main"' in text
    assert "keywords =" in text
    assert "classifiers =" in text
    assert "License :: OSI Approved :: MIT License" not in text


def test_release_evidence_dir_is_addressable() -> None:
    """Operator slot for audit bundles; optional and empty by default."""
    root = _repo_root()
    assert (root / "release/evidence").is_dir()


def test_m6_release_gate_evidence_bundle_files_exist() -> None:
    """Release-gate audit bundle is present for independent verification."""
    root = _repo_root()
    bundle = root / "release/evidence/m6_release_gate_v1"
    for name in (
        "README.md",
        "commands.txt",
        "results.md",
        "artifacts_manifest.txt",
        "claims_ledger.md",
    ):
        assert (bundle / name).is_file(), name


def test_m6_release_gate_bundle_is_clone_portable() -> None:
    """Committed release-gate evidence should not hardcode one local checkout path."""
    root = _repo_root()
    bundle = root / "release/evidence/m6_release_gate_v1"
    commands = (bundle / "commands.txt").read_text(encoding="utf-8")
    results = (bundle / "results.md").read_text(encoding="utf-8")
    assert "repository root (`$(pwd)` after `cd` into your clone)" in commands
    assert '--repo-root "$(pwd)"' in commands
    assert "/Users/cj/Workspace/active/benchmark-v2" not in commands
    assert "stale recorded checkout path or commit pin" in results
    assert "1130597" not in results


def test_python_m_build_produces_wheel_and_sdist(tmp_path: Path) -> None:
    """Honest local packaging check (not PyPI publication). Requires optional dev dep `build`."""
    root = _repo_root()
    pre = subprocess.run(
        [sys.executable, "-m", "build", "--help"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if pre.returncode != 0:
        pytest.skip("PEP 517 build frontend (`python -m build`) not runnable in this interpreter")

    out = tmp_path / "dist"
    proc = subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(out), "--no-isolation"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    combined = proc.stdout + proc.stderr
    assert "SetuptoolsDeprecationWarning" not in combined
    wheels = list(out.glob("*.whl"))
    sdist = list(out.glob("*.tar.gz"))
    assert wheels, "expected at least one wheel"
    assert sdist, "expected sdist tarball"
    assert any("benchmark" in w.name.lower() for w in wheels)
