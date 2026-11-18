"""RILL-002 之后：g8-version 识别 CT 包 tag 的正/负例。

用临时 git 仓库跑 tools/checks/g8_version.py，避免依赖真实 tag 列表：
- 合法包 tag 通过；
- message/tag 名/ct.pkg 不一致、缺 ct.pkg、既非 phase 也非包 tag 必须红。
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GATE = os.path.join(ROOT, "tools", "checks", "g8_version.py")


def _git(repo, *args):
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-C", repo]
        + list(args),
        capture_output=True,
        text=True,
    )


def _gate(repo):
    env = dict(os.environ, ROOT=repo)
    return subprocess.run(
        [sys.executable, GATE], env=env, capture_output=True, text=True
    )


def _write_pkg(repo, version="0.2.0", name="pkg"):
    with open(os.path.join(repo, "ct.pkg"), "w", encoding="utf-8") as handle:
        handle.write(
            "name = %s\npublisher = p\nns-root = .\nversion = %s\n"
            % (name, version)
        )


def _commit(repo, message):
    _git(repo, "add", "-A")
    assert _git(repo, "commit", "-qm", message).returncode == 0


def test_valid_package_tag_passes():
    with tempfile.TemporaryDirectory() as repo:
        assert _git(repo, "init", "-q").returncode == 0
        _write_pkg(repo)
        _commit(repo, "init")
        assert _git(repo, "tag", "-a", "v0.2.0", "-m", "pkg 0.2.0").returncode == 0
        proc = _gate(repo)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "包 tag pkg 0.2.0" in proc.stdout, proc.stdout


def test_version_mismatch_fails():
    with tempfile.TemporaryDirectory() as repo:
        assert _git(repo, "init", "-q").returncode == 0
        _write_pkg(repo)
        _commit(repo, "init")
        assert _git(repo, "tag", "-a", "v0.3.0", "-m", "pkg 0.3.0").returncode == 0
        proc = _gate(repo)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "ct.pkg version" in proc.stdout, proc.stdout


def test_missing_ct_pkg_fails():
    with tempfile.TemporaryDirectory() as repo:
        assert _git(repo, "init", "-q").returncode == 0
        with open(os.path.join(repo, "README"), "w", encoding="utf-8") as handle:
            handle.write("no package\n")
        _commit(repo, "init")
        assert _git(repo, "tag", "-a", "v0.5.0", "-m", "pkg 0.5.0").returncode == 0
        proc = _gate(repo)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "包 tag 缺 ct.pkg" in proc.stdout, proc.stdout


def test_neither_phase_nor_package_fails():
    with tempfile.TemporaryDirectory() as repo:
        assert _git(repo, "init", "-q").returncode == 0
        _write_pkg(repo)
        _commit(repo, "init")
        assert _git(repo, "tag", "-a", "v0.4.0", "-m", "oops").returncode == 0
        proc = _gate(repo)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "也不符合包 tag" in proc.stdout, proc.stdout


if __name__ == "__main__":
    test_valid_package_tag_passes()
    test_version_mismatch_fails()
    test_missing_ct_pkg_fails()
    test_neither_phase_nor_package_fails()
    print("PASS")
