"""PH-11 测试共用夹具：定位仓库、跑真实 CLI、写 agent manifest。

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

HOST_ROOT = os.path.join(ROOT, "testdata", "0.1.0", "host", "agent")
SHARED_ROOT = os.path.join(ROOT, "testdata", "0.1.0", "host", "shared")

DEFAULT_VERBS = (
    "read",
    "write",
    "parse",
    "send",
    "search",
    "replace",
    "contains",
    "review",
    "run",
    "env",
)


def env_with_src(extra=None):
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC
    env.pop("RILL_TEST_SECRET", None)
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


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)
    return path


def write_tools(directory, tools, name="tools.json"):
    return write_json(
        os.path.join(directory, name),
        {"schema": "rill-fakes-tools/0", "tools": tools},
    )


def manifest_doc(**overrides):
    doc = {
        "schema": "rill.agent-profile/0",
        "name": "agent-test",
        "description": "PH-11 测试宿主",
        "role": "engineer",
        "roles": {
            "engineer": {"verbs": list(DEFAULT_VERBS)},
            "auditor": {"verbs": ["read", "review"]},
        },
        "types": {"file": "path", "net": "text"},
        "context": {},
        "limits": {"steps": 32, "time_ms": 2000, "bytes": 65536},
        "tools": "tools.json",
    }
    doc.update(overrides)
    return doc


def write_manifest(directory, **overrides):
    """写 agent manifest；``tools`` 默认为同目录 tools.json。"""
    path = os.path.join(directory, "agent.json")
    return write_json(path, manifest_doc(**overrides))


def entry(verb, subject=None, object=None, input_value=None, post=None):
    return {
        "verb": verb,
        "subject": subject,
        "object": object,
        "post": post or [],
        "input": input_value,
    }
