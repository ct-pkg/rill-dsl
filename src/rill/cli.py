"""``rill`` CLI（P1：仅 tokenize 可用）。

SUT 协议见 ``tools/rill_harness/sut.py``：
  0  成功，stdout 是 JSON；
  2  诊断，stdout 是 ``{"error": {stage, code, line, col, message}}``；
  3  未实现。
"""

import json
import os
import sys

from .errors import LexError
from .lexer import tokenize

EXIT_OK = 0
EXIT_DIAGNOSTIC = 2
EXIT_NOT_IMPLEMENTED = 3


def _emit(payload, code):
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=False) + "\n")
    return code


def _usage(message):
    return _emit(
        {
            "error": {
                "stage": "cli",
                "code": "E_USAGE",
                "line": 0,
                "col": 0,
                "message": message,
            }
        },
        EXIT_DIAGNOSTIC,
    )


def _not_implemented(what):
    sys.stderr.write("not implemented: %s (P1 only implements tokenize)\n" % what)
    return EXIT_NOT_IMPLEMENTED


def _source_path(args):
    rest = [arg for arg in args if not arg.startswith("-")]
    return rest


def cmd_tokenize(args):
    paths = _source_path(args)
    if len(paths) != 1:
        return _usage("tokenize 需要且只需要一个源文件参数")
    path = paths[0]
    try:
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        return _usage("无法读取 %s：%s" % (path, exc))
    try:
        tokens = tokenize(source)
    except LexError as exc:
        return _emit({"error": exc.as_dict()}, EXIT_DIAGNOSTIC)
    return _emit({"tokens": [token.as_dict() for token in tokens]}, EXIT_OK)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return _usage("缺少子命令")
    command = argv[0]
    if command == "tokenize":
        return cmd_tokenize(argv[1:])
    if command in ("parse", "check", "run", "fmt"):
        return _not_implemented(command)
    if command in ("-h", "--help"):
        sys.stdout.write("usage: rill tokenize <file>\n")
        return EXIT_OK
    return _usage("未知子命令 %r" % command)


if __name__ == "__main__":
    sys.exit(main())
