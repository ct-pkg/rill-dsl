"""PH-22 版本措辞白名单的负例与正例。

负例 `v9.9.9` 必须让 `version_wording.py` 红；正例 `v0.22.0` 必须绿。
这是门禁脚本改动的同提交负例夹具（G8）。
"""

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "tools" / "checks" / "version_wording.py"


def run(tmp_path: Path, text: str) -> subprocess.CompletedProcess:
    (tmp_path / "docs" / "spec").mkdir(parents=True)
    (tmp_path / "docs" / "spec" / "x.md").write_text(text, encoding="utf-8")
    env = dict(os.environ, ROOT=str(tmp_path))
    return subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, env=env
    )


def test_unlisted_version_fails(tmp_path: Path) -> None:
    proc = run(tmp_path, "v9.9.9\n")
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0, out
    assert "v9.9.9" in out, out


def test_v0220_allowed(tmp_path: Path) -> None:
    proc = run(tmp_path, "v0.22.0\n")
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out
