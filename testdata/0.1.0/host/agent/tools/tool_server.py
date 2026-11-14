#!/usr/bin/env python3
"""canonical Agent 工具的真实子进程实现（PH-11-T6）。

协议：stdin 一行 JSON ``{"tool": name, "args": {...}}``；stdout 一行 JSON
``{"ok": bool, "value": ..., "error": ...}``。工作目录由宿主设为 workspace。

工具：
- ``read`` / ``write``：真实文件 I/O；路径必须落在 workspace 内；
- ``run``：真实子进程，返回 ``{code, stdout, stderr}``；
- ``send`` / ``emit``：没有 OS stdout，返回文本，可选写入 ``RILL_TOOL_LOG``；
- 未知工具返回 ``E-HOST-TOOL-UNKNOWN``。

``RILL_TOOL_LOG`` 只用于验收证据：每次调用追加一行 ``pid/tool/args``。
"""

import base64
import json
import os
import shlex
import subprocess
import sys

ROOT = os.path.realpath(os.getcwd())


def log(tool, args):
    path = os.environ.get("RILL_TOOL_LOG")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {"pid": os.getpid(), "tool": tool, "args": args},
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )


def encode(raw):
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return {"$bytes": base64.b64encode(raw).decode("ascii")}


def decode(content):
    if isinstance(content, dict) and set(content) == {"$bytes"}:
        return base64.b64decode(content["$bytes"])
    if isinstance(content, str):
        return content.encode("utf-8")
    raise ValueError("write 内容只接受字符串或 $bytes")


def resolve(relative):
    target = relative if os.path.isabs(relative) else os.path.join(ROOT, relative)
    target = os.path.realpath(target)
    if target != ROOT and not target.startswith(ROOT + os.sep):
        raise ValueError("E-HOST-FS-OUTSIDE: %r 越出 workspace %r" % (relative, ROOT))
    return target


def call(tool, args):
    if tool == "read":
        path = resolve(args["path"])
        with open(path, "rb") as handle:
            return {"ok": True, "value": encode(handle.read())}

    if tool == "write":
        path = resolve(args["path"])
        with open(path, "wb") as handle:
            handle.write(decode(args["content"]))
        return {"ok": True, "value": os.path.relpath(path, ROOT).replace(os.sep, "/")}

    if tool in ("run", "exec"):
        command = args["command"]
        argv = shlex.split(command)
        if not argv:
            return {"ok": False, "error": "E-HOST-TOOL-ARGS: run 命令为空"}
        stdin = args.get("stdin")
        raw = decode(stdin) if stdin is not None else b""
        proc = subprocess.run(
            argv,
            cwd=ROOT,
            input=raw,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        value = {
            "code": proc.returncode,
            "stdout": encode(proc.stdout),
            "stderr": encode(proc.stderr),
        }
        if proc.returncode == 0:
            return {"ok": True, "value": value}
        return {
            "ok": False,
            "error": encode(proc.stderr) if proc.stderr else "E-HOST-TOOL-EXIT: %d" % proc.returncode,
            "value": value,
        }

    if tool in ("send", "emit"):
        text = args.get("text", "")
        if not isinstance(text, str):
            text = json.dumps(text, ensure_ascii=False, sort_keys=True)
        return {"ok": True, "value": text}

    return {
        "ok": False,
        "error": "E-HOST-TOOL-UNKNOWN: 工具 %r 没有 canonical 实现" % tool,
    }


def main():
    try:
        request = json.load(sys.stdin)
        tool = request["tool"]
        args = request.get("args") or {}
    except (ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": "E-HOST-TOOL-ARGS: %s" % exc}))
        return 0

    log(tool, args)
    try:
        response = call(tool, args)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        response = {"ok": False, "error": "E-HOST-TOOL-FAILED: %s" % exc}
    print(json.dumps(response, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
