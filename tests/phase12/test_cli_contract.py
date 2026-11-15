"""PH-12-T1：四个子命令的统一参数、退出码与错误分层。

用法：python3 tests/phase12/test_cli_contract.py（退出 0 = 通过）。
覆盖 E-1 的 CLI 契约部分：``tokenize`` / ``parse`` / ``check`` / ``run`` /
``fmt`` 共用 0（成功）/ 2（诊断）退出码；成功输出 JSON（fmt 除外），
诊断输出 ``{"error": {stage, code, line, col, message}}``。
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from support import ast_of, payload_of, run_cli, write_file


def case_help_lists_four_commands():
    result = run_cli(["--help"])
    assert result.returncode == 0, (result.stdout, result.stderr)
    for command in ("tokenize", "parse", "check", "run", "fmt"):
        assert command in result.stdout, "帮助缺少子命令 %r：%r" % (
            command,
            result.stdout,
        )


def case_usage_errors_are_exit_2():
    checks = [
        [],
        ["nope"],
        ["parse"],
        ["check"],
        ["run"],
        ["fmt"],
        ["parse", "--dump-ast", "a.ri", "--bogus"],
        ["run", "a.ri", "--profile", "nobody"],
    ]
    for args in checks:
        result = run_cli(args)
        assert result.returncode == 2, (args, result.returncode, result.stdout)
        payload = payload_of(result)
        error = payload.get("error", {})
        assert error.get("stage") == "cli", (args, error)
        assert error.get("code") == "E_USAGE", (args, error)


def case_diagnostics_are_exit_2():
    with tempfile.TemporaryDirectory() as tmp:
        bad = write_file(tmp, "bad.ri", 'x <read> "unclosed\n')
        for args in (
            ["tokenize", bad],
            ["parse", "--dump-ast", bad],
            ["check", bad],
            ["run", bad],
        ):
            result = run_cli(args)
            assert result.returncode == 2, (args, result.returncode, result.stdout)
            error = payload_of(result).get("error", {})
            assert error.get("code"), (args, error)
            assert error.get("stage") in ("tokenize", "parse", "load", "run"), (
                args,
                error,
            )


def case_fmt_round_trips_through_cli():
    source = "//map{\ncfg`configuration\n}\n<read> `cfg`.yml\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = write_file(tmp, "sample.ri", source)
        before = ast_of(path)
        for mode in ("--compress", "--display"):
            result = run_cli(["fmt", mode, path])
            assert result.returncode == 0, (mode, result.stdout, result.stderr)
            assert result.stdout.strip(), "%s 没有输出" % mode
            formatted = write_file(tmp, mode.strip("-") + ".ri", result.stdout)
            after = ast_of(formatted)
            assert before == after, "%s 改变了 AST" % mode


def main():
    case_help_lists_four_commands()
    case_usage_errors_are_exit_2()
    case_diagnostics_are_exit_2()
    case_fmt_round_trips_through_cli()
    print("PASS phase12 cli: 四子命令/退出码分层/fmt 回读")


if __name__ == "__main__":
    main()
