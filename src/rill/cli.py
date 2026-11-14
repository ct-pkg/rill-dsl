"""``rill`` CLI（PH-3：tokenize 与 parse）。

SUT 协议见 ``tools/rill_harness/sut.py``：
  0  成功，stdout 是 JSON；
  2  诊断，stdout 是 ``{"error": {stage, code, line, col, message}}``；
  3  未实现。
"""

import json
import sys

from .errors import LexError, ParseError
from .lexer import tokenize
from .parser import parse

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


def cmd_parse(args):
    dump = False
    profile = "shell"
    paths = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--dump-ast":
            dump = True
        elif arg == "--profile":
            index += 1
            if index >= len(args):
                return _usage("--profile 缺参数")
            profile = args[index]
        elif arg.startswith("--profile="):
            profile = arg.split("=", 1)[1]
        elif arg.startswith("-"):
            return _usage("parse 不认识的参数 %r" % arg)
        else:
            paths.append(arg)
        index += 1
    if len(paths) != 1:
        return _usage("parse 需要且只需要一个源文件参数")
    if not dump:
        return _usage("parse 目前只支持 --dump-ast")
    if profile not in ("shell", "agent"):
        return _usage("未知 profile %r（只允许 shell / agent）" % profile)
    path = paths[0]
    try:
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        return _usage("无法读取 %s：%s" % (path, exc))
    try:
        tree = parse(tokenize(source))
    except LexError as exc:
        return _emit({"error": exc.as_dict()}, EXIT_DIAGNOSTIC)
    except ParseError as exc:
        return _emit({"error": exc.as_dict()}, EXIT_DIAGNOSTIC)
    return _emit({"ast": tree}, EXIT_OK)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return _usage("缺少子命令")
    command = argv[0]
    if command == "tokenize":
        return cmd_tokenize(argv[1:])
    if command == "parse":
        return cmd_parse(argv[1:])
    if command in ("check", "run", "fmt"):
        return _not_implemented(command)
    if command in ("-h", "--help"):
        sys.stdout.write("usage: rill tokenize <file> | rill parse --dump-ast <file> [--profile shell|agent]\n")
        return EXIT_OK
    return _usage("未知子命令 %r" % command)


if __name__ == "__main__":
    sys.exit(main())
