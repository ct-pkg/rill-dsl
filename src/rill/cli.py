"""``rill`` CLI（tokenize / parse / check）。

SUT 协议见 ``tools/rill_harness/sut.py``：
  0  成功，stdout 是 JSON；
  2  诊断，stdout 是 ``{"error": {stage, code, line, col, message}}``；
  3  未实现。
"""

import json
import os
import sys

from . import fakes as fakes_mod
from . import formatter
from . import loader
from .errors import LexError, LoadError, ParseError
from .eval_simple import EvalError, Interpreter
from .host import agent as agent_host
from .host.shell import (
    CapabilityDenied,
    ShellHost,
    ShellVerbRegistry,
    default_shell_policy,
    jsonable,
    load_shell_profile,
)
from .lexer import tokenize
from .parser import parse, parse_with_warnings
from .verbs import FakeVerbRegistry

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


def _diagnostic(code, message):
    return _emit(
        {
            "error": {
                "stage": "run",
                "code": code,
                "line": 0,
                "col": 0,
                "message": message,
            }
        },
        EXIT_DIAGNOSTIC,
    )


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


def cmd_check(args):
    profile = "shell"
    paths = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--profile":
            index += 1
            if index >= len(args):
                return _usage("--profile 缺参数")
            profile = args[index]
        elif arg.startswith("--profile="):
            profile = arg.split("=", 1)[1]
        elif arg.startswith("-"):
            return _usage("check 不认识的参数 %r" % arg)
        else:
            paths.append(arg)
        index += 1
    if len(paths) != 1:
        return _usage("check 需要且只需要一个源文件参数")
    if profile not in ("shell", "agent"):
        return _usage("未知 profile %r（只允许 shell / agent）" % profile)
    path = paths[0]
    try:
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        return _usage("无法读取 %s：%s" % (path, exc))
    try:
        tree, warnings = parse_with_warnings(tokenize(source))
        loader.check_program(tree, profile)
    except LexError as exc:
        return _emit({"error": exc.as_dict()}, EXIT_DIAGNOSTIC)
    except ParseError as exc:
        return _emit({"error": exc.as_dict()}, EXIT_DIAGNOSTIC)
    except LoadError as exc:
        return _emit({"error": exc.as_dict()}, EXIT_DIAGNOSTIC)
    return _emit({"warnings": warnings}, EXIT_OK)


def _run_verbs(profile, fakes_path, host_profile_path):
    """返回 ``(verbs, policy)``；``policy`` 只在真实宿主模式出现。

    有 ``--fakes`` 时 fake 优先，能力清单不参与：这条顺序就是 PH-10-T3 的契约。
    """
    if fakes_path:
        return fakes_mod.load_tools(fakes_path), None
    if profile == "agent":
        if host_profile_path:
            try:
                policy = agent_host.load_agent_profile(
                    host_profile_path, cwd=os.getcwd()
                )
            except ValueError as exc:
                return None, ("profile", "E-RUN-HOST-PROFILE", str(exc))
        else:
            policy = agent_host.default_agent_policy(cwd=os.getcwd())
        host = agent_host.AgentHost(policy)
        return agent_host.AgentVerbRegistry(host), policy
    if host_profile_path:
        try:
            policy = load_shell_profile(host_profile_path)
        except ValueError as exc:
            return None, ("profile", "E-RUN-HOST-PROFILE", str(exc))
    else:
        policy = default_shell_policy()
    return ShellVerbRegistry(ShellHost(policy, cwd=os.getcwd())), policy


def cmd_run(args):
    profile = "shell"
    fakes_path = ""
    host_profile_path = ""
    paths = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--profile":
            index += 1
            if index >= len(args):
                return _usage("--profile 缺参数")
            profile = args[index]
        elif arg.startswith("--profile="):
            profile = arg.split("=", 1)[1]
        elif arg == "--fakes":
            index += 1
            if index >= len(args):
                return _usage("--fakes 缺参数")
            fakes_path = args[index]
        elif arg.startswith("--fakes="):
            fakes_path = arg.split("=", 1)[1]
        elif arg == "--host-profile":
            index += 1
            if index >= len(args):
                return _usage("--host-profile 缺参数")
            host_profile_path = args[index]
        elif arg.startswith("--host-profile="):
            host_profile_path = arg.split("=", 1)[1]
        elif arg.startswith("-"):
            return _usage("run 不认识的参数 %r" % arg)
        else:
            paths.append(arg)
        index += 1
    if len(paths) != 1:
        return _usage("run 需要且只需要一个源文件参数")
    if profile not in ("shell", "agent"):
        return _usage("未知 profile %r（只允许 shell / agent）" % profile)
    path = paths[0]
    try:
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        return _usage("无法读取 %s：%s" % (path, exc))

    try:
        verbs, policy = _run_verbs(profile, fakes_path, host_profile_path)
    except (OSError, ValueError) as exc:
        return _diagnostic("E-RUN-FAKES", "fakes 无法加载：%s" % exc)
    if isinstance(policy, tuple):
        return _diagnostic(policy[1], policy[2])
    if verbs is None:
        return _diagnostic("E-RUN-HOST-UNAVAILABLE", policy)

    try:
        tree = parse(tokenize(source))
        tables = loader.check_program(tree, profile)
        if profile == "agent" and hasattr(verbs, "host"):
            verbs.host.validate_program(tree)
        outcome = Interpreter(verbs, functions=tables.functions).eval_program(tree)
    except LexError as exc:
        return _emit({"error": exc.as_dict()}, EXIT_DIAGNOSTIC)
    except ParseError as exc:
        return _emit({"error": exc.as_dict()}, EXIT_DIAGNOSTIC)
    except LoadError as exc:
        return _emit({"error": exc.as_dict()}, EXIT_DIAGNOSTIC)
    except EvalError as exc:
        return _emit({"error": exc.as_dict()}, EXIT_DIAGNOSTIC)
    except CapabilityDenied as exc:
        # §4.10 的隐式 [error] 会把失败改写成 "RILL DSL ERROR"；能力拒绝必须
        # 在诊断里保留 slot.operation，所以走 run 诊断而不是 ok=false。
        return _diagnostic(exc.code, exc.message)
    except agent_host.AgentHostError as exc:
        # 角色表不合法或越权：加载期语义，但错误码属于宿主，走 run 诊断。
        return _diagnostic(exc.code, exc.message)
    code = EXIT_OK
    if policy is not None:
        code = policy.exit_code(outcome.ok)
    return _emit(
        {
            "ok": outcome.ok,
            "value": jsonable(outcome.value),
            "error": outcome.error,
            "host_meta": jsonable(outcome.host_meta or {}),
        },
        code,
    )


def cmd_fmt(args):
    mode = ""
    paths = []
    for arg in args:
        if arg == "--compress":
            if mode:
                return _usage("fmt 只能选一种格式（--compress / --display）")
            mode = "compress"
        elif arg == "--display":
            if mode:
                return _usage("fmt 只能选一种格式（--compress / --display）")
            mode = "display"
        elif arg.startswith("-"):
            return _usage("fmt 不认识的参数 %r" % arg)
        else:
            paths.append(arg)
    if not mode:
        return _usage("fmt 需要 --compress 或 --display")
    if len(paths) != 1:
        return _usage("fmt 需要且只需要一个源文件参数")
    path = paths[0]
    try:
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        return _usage("无法读取 %s：%s" % (path, exc))
    try:
        text = formatter.format_source(source, mode)
    except LexError as exc:
        return _emit({"error": exc.as_dict()}, EXIT_DIAGNOSTIC)
    sys.stdout.write(text)
    return EXIT_OK


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return _usage("缺少子命令")
    command = argv[0]
    if command == "tokenize":
        return cmd_tokenize(argv[1:])
    if command == "parse":
        return cmd_parse(argv[1:])
    if command == "check":
        return cmd_check(argv[1:])
    if command == "run":
        return cmd_run(argv[1:])
    if command == "fmt":
        return cmd_fmt(argv[1:])
    if command in ("-h", "--help"):
        sys.stdout.write(
            "usage: rill tokenize <file> | rill parse --dump-ast <file> [--profile shell|agent]"
            " | rill check <file> [--profile shell|agent]"
            " | rill run <file> [--profile shell|agent] [--fakes <path>]"
            " [--host-profile <path>]"
            " | rill fmt --compress|--display <file>\n"
        )
        return EXIT_OK
    return _usage("未知子命令 %r" % command)


if __name__ == "__main__":
    sys.exit(main())
