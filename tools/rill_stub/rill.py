#!/usr/bin/env python3
"""RILL CLI 占位实现（Phase 0 专用）。

真实 CLI 已按 P1 落地在 `src/rill`（默认由 sut.json 指向）；本文件只服务 `smoke/` 桶，
用来证明 harness 的调用、比对、双 profile 一致性链路在任何实现状态下都能自证。

这不是词法器，也不是语法分析器，不实现 0.1.0 的任何语义：
  1. 默认对所有子命令返回“未实现”（退出码 3）；
  2. 在 RILL_STUB_MODE=echo 时，让 `parse --dump-ast` 回显一个 StubProgram 节点。

当真实 CLI 覆盖 parse 后，smoke/ 桶与本文件可以一起删除。
"""

import json
import os
import sys

EXIT_USAGE = 2
EXIT_NOT_IMPLEMENTED = 3


def usage_error(message):
    diag = {
        "error": {
            "stage": "cli",
            "code": "E_USAGE",
            "line": 0,
            "col": 0,
            "message": message,
        }
    }
    print(json.dumps(diag, ensure_ascii=False))
    return EXIT_USAGE


def not_implemented(what):
    sys.stderr.write(
        "not implemented: %s (Phase 0 placeholder; smoke-only, real CLI is src/rill)\n" % what
    )
    return EXIT_NOT_IMPLEMENTED


def source_from_args(args):
    # 兼容 `parse --dump-ast <file> --profile shell` 与 `tokenize <file>`。
    files = [arg for arg in args if not arg.startswith("-")]
    for index, arg in enumerate(args):
        if arg == "--profile" and index + 1 < len(args):
            files = [item for item in files if item != args[index + 1]]
    if len(files) != 1:
        raise ValueError("需要且只需要一个源文件参数")
    return files[0]


def cmd_parse(args):
    if os.environ.get("RILL_STUB_MODE") != "echo":
        return not_implemented("parse --dump-ast")
    try:
        path = source_from_args(args)
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
    except (OSError, ValueError) as exc:
        return usage_error(str(exc))
    print(
        json.dumps(
            {
                "ast": {
                    "kind": "StubProgram",
                    "placeholder": True,
                    "source": source,
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


def info():
    payload = {
        "placeholder": True,
        "phase": "p0",
        "implements": ["parse --dump-ast（仅 RILL_STUB_MODE=echo 的链路自证）"],
        "does_not_implement": [
            "tokenize",
            "parse（真实语法）",
            "check",
            "run",
            "fmt",
        ],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def main(argv):
    if not argv:
        return usage_error("缺少子命令")
    if argv[0] == "--stub-info":
        return info()
    command = argv[0]
    if command == "parse":
        return cmd_parse(argv[1:])
    if command == "tokenize":
        return not_implemented("tokenize")
    if command == "check":
        return not_implemented("check")
    if command == "run":
        return not_implemented("run")
    if command == "fmt":
        return not_implemented("fmt")
    return usage_error("未知子命令 %r" % command)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
