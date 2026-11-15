"""PH-10 测试共用夹具：定位仓库、跑真实 CLI、读 JSON。

不在本模块 import 被测的宿主实现：实现缺失时由各 test_*.py 直接报错，
红证才看得见缺的是哪一层。
"""

import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)

HOST_ROOT = os.path.join(ROOT, "testdata", "0.1.0", "host", "shell")
PROFILE_FULL = os.path.join(HOST_ROOT, "profiles", "full.json")
PROFILE_MIN = os.path.join(HOST_ROOT, "profiles", "min.json")
PROFILE_NO_STDIO = os.path.join(HOST_ROOT, "profiles", "no-stdio.json")


def env_with_src(extra=None):
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC
    env.pop("RILL_TEST_PORT", None)
    env.update(extra or {})
    return env


def run_cli(args, cwd=None, env=None, sut=None):
    """真实 CLI：默认 ``python3 -m rill``；``sut`` 可覆盖为任意命令。

    ``sut`` 里的相对可执行路径按仓库根解析（fixture 会把 cwd 换到临时目录）。
    """
    command = list(sut) if sut else [sys.executable, "-m", "rill"]
    if sut and not os.path.isabs(command[0]):
        command[0] = os.path.join(ROOT, command[0])
    return subprocess.run(
        command + list(args),
        cwd=cwd or ROOT,
        env=env_with_src(env),
        capture_output=True,
        text=True,
    )


def payload_of(result):
    try:
        return json.loads(result.stdout)
    except ValueError:
        raise AssertionError(
            "stdout 不是 JSON：%r（stderr=%r）" % (result.stdout, result.stderr)
        )


def write_script(directory, name, text):
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path
