"""被测命令（SUT）适配层。

这一层只认“命令 + 退出码 + stdout JSON”，不认任何具体实现语言或产品 CLI 细节：
  0  成功，stdout 是 JSON
  2  诊断，stdout 是 {"error": {stage, code, line, col, message}}
  3  未实现（Phase 0 的占位实现走这条），stdout/stderr 只作说明
其他  视为内部错误

产品 CLI 最终长什么样尚未裁定；若与这里的调用形状不同，只改本文件，不动用例。
"""

import json
import os
import shlex
import subprocess

EXIT_OK = 0
EXIT_DIAGNOSTIC = 2
EXIT_NOT_IMPLEMENTED = 3

SUT_MANIFEST = "sut.json"


class SutResult(object):
    def __init__(self, status, exit_code, payload, stdout, stderr, argv):
        self.status = status  # ok / diagnostic / not_implemented / internal / timeout
        self.exit_code = exit_code
        self.payload = payload
        self.stdout = stdout
        self.stderr = stderr
        self.argv = argv

    @property
    def message(self):
        if self.status == "diagnostic":
            err = self.payload.get("error", {})
            return err.get("message", "")
        if self.status == "not_implemented":
            text = (self.stderr or self.stdout).strip()
            return text.splitlines()[0] if text else "not implemented"
        return (self.stderr or self.stdout).strip()


class Sut(object):
    def __init__(self, command, repo_root, timeout=15, extra_env=None, placeholder=False):
        self.command = list(command)
        self.repo_root = repo_root
        self.timeout = timeout
        self.extra_env = dict(extra_env or {})
        self.placeholder = placeholder

    @property
    def display(self):
        return " ".join(shlex.quote(part) for part in self.command) + (
            "  [PLACEHOLDER]" if self.placeholder else ""
        )

    def run(self, args, env=None):
        argv = self.command + list(args)
        merged = dict(os.environ)
        merged.update(self.extra_env)
        merged.update(env or {})
        try:
            proc = subprocess.run(
                argv,
                cwd=self.repo_root,
                env=merged,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return SutResult("timeout", None, {}, "", "timeout after %ss" % self.timeout, argv)
        except OSError as exc:
            return SutResult("internal", None, {}, "", "无法启动被测命令：%s" % exc, argv)

        status = "internal"
        payload = {}
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        if proc.returncode == EXIT_NOT_IMPLEMENTED:
            status = "not_implemented"
        elif proc.returncode in (EXIT_OK, EXIT_DIAGNOSTIC):
            try:
                payload = json.loads(stdout) if stdout.strip() else {}
            except ValueError as exc:
                return SutResult(
                    "internal",
                    proc.returncode,
                    {},
                    stdout,
                    "stdout 不是 JSON：%s" % exc,
                    argv,
                )
            if not isinstance(payload, dict):
                return SutResult(
                    "internal", proc.returncode, {}, stdout, "stdout JSON 顶层必须是对象", argv
                )
            if proc.returncode == EXIT_OK:
                status = "ok"
            else:
                status = "diagnostic" if isinstance(payload.get("error"), dict) else "internal"
                if status == "internal":
                    stderr = "退出码 2 但 stdout 缺少 error 对象"

        return SutResult(status, proc.returncode, payload, stdout, stderr, argv)


def from_manifest(repo_root, manifest_path=None):
    """读 testdata/0.1.0/sut.json；返回 (Sut, error)。"""
    path = manifest_path or os.path.join(repo_root, "testdata", "0.1.0", SUT_MANIFEST)
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        return None, "%s: 无法读取被测命令清单（%s）" % (path, exc)

    command = doc.get("command")
    if isinstance(command, str):
        command = shlex.split(command)
    if not isinstance(command, list) or not command:
        return None, "%s.command: 必须是非空数组" % path

    env = doc.get("env") or {}
    if not isinstance(env, dict):
        return None, "%s.env: 必须是对象" % path

    sut = Sut(
        command,
        repo_root,
        timeout=doc.get("timeout_seconds", 15),
        extra_env=env,
        placeholder=bool(doc.get("placeholder", False)),
    )
    return sut, None
