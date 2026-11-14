"""RILL 0.1.0 harness 命令行入口。

用法：
  tools/check-0.1.0.sh                # 跑全部可运行用例
  tools/check-0.1.0.sh --all          # 全样例门禁：pending=0 且任何非 PASS 都失败
  tools/check-0.1.0.sh --list         # 列出用例与资产，不执行
  tools/check-0.1.0.sh --check-fakes  # 只校验 profile / fake 资产
  tools/check-0.1.0.sh --show <case>  # 显示某个用例的被测输出
"""

import argparse
import json
import os
import shlex
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rill_harness import cases as case_mod
from rill_harness import fakes as fakes_mod
from rill_harness import host as host_mod
from rill_harness import runner as runner_mod
from rill_harness import sut as sut_mod

COMPLIANCE_BUCKETS = ("positive", "negative", "host")
EXIT_OK = 0
EXIT_FAIL = 1
EXIT_NOT_IMPLEMENTED = 3


def parse_args(argv):
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser = argparse.ArgumentParser(
        prog="check-0.1.0.sh",
        description="RILL 0.1.0 用例 harness（Phase 0 基座）",
    )
    parser.add_argument("--repo-root", default=here, help="仓库根目录")
    parser.add_argument("--root", default="", help="测试根目录，默认 <repo>/testdata/0.1.0")
    parser.add_argument("--phase", default="", help="只跑某个阶段声明的用例，如 p1 / p2 / r3")
    parser.add_argument("--kind", default="", help="只跑某种期望，如 ast / tokens / error / run")
    parser.add_argument("--bucket", default="", help="只跑某个桶，如 positive / negative / pending")
    parser.add_argument("--case", action="append", default=[], metavar="CASE",
                        help="只跑指定用例，可重复；按相对 id 或唯一后缀匹配")
    parser.add_argument("--sut", default="", help="覆盖被测命令，如 'python3 tools/rill_stub/rill.py'")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    parser.add_argument(
        "--all",
        action="store_true",
        help="全样例门禁：所有桶必须执行、pending 必须为 0、任何非 PASS 都失败",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list", action="store_true", help="列出用例与资产，不执行")
    group.add_argument("--check-fakes", action="store_true", help="只校验 profile 与 fake 资产")
    group.add_argument("--show", metavar="CASE", default="", help="显示某个用例的被测输出")
    return parser.parse_args(argv)


def _rel(path, repo_root):
    return os.path.relpath(path, repo_root).replace(os.sep, "/")


def load_assets(root, repo_root):
    """返回 (profiles, tools, host_stubs, errors)。资产缺失不算错误，资产写错才算。"""
    errors = []
    profiles = {}
    tools = None
    stubs = None
    try:
        profiles = host_mod.load_profiles(root)
    except host_mod.ProfileError as exc:
        errors.append(str(exc))
    tools_path = os.path.join(root, "fakes", "tools.json")
    if os.path.isfile(tools_path):
        try:
            tools = fakes_mod.load_tools(tools_path)
        except fakes_mod.FakeError as exc:
            errors.append(str(exc))
    host_path = os.path.join(root, "fakes", "host.json")
    if os.path.isfile(host_path):
        try:
            stubs = fakes_mod.load_host(host_path)
        except fakes_mod.FakeError as exc:
            errors.append(str(exc))
    return profiles, tools, stubs, errors


def describe_assets(profiles, tools, stubs, repo_root):
    lines = []
    if profiles:
        lines.append("profiles : %s（已加载）" % ", ".join(sorted(profiles)))
    else:
        lines.append("profiles : 无")
    if tools is not None:
        lines.append(
            "fake 工具: %s（%d 个工具）"
            % (_rel(tools.path, repo_root), len(tools.scripts))
        )
    if stubs is not None:
        lines.append(
            "能力桩  : %s（%s）"
            % (_rel(stubs.path, repo_root), ", ".join(fakes_mod.HOST_SLOTS))
        )
    return lines


def filter_cases(all_cases, args, wanted):
    selected = []
    for case in all_cases:
        if args.phase and case.phase != args.phase:
            continue
        if args.kind and case.kind != args.kind:
            continue
        if args.bucket and case.bucket != args.bucket:
            continue
        if wanted and case.rel not in wanted:
            continue
        selected.append(case)
    return selected


def golden_stats(selected, root):
    required = 0
    present = 0
    for case in selected:
        if case.kind in ("ast", "tokens") and not case.has_inline_expect:
            required += 1
            if os.path.isfile(case.golden_path(root)):
                present += 1
    return required, present


def cmd_list(selected, root, repo_root, profiles, tools, stubs):
    counts = case_mod.bucket_counts(selected)
    print("RILL 0.1.0 fixtures")
    print("root     : %s" % _rel(root, repo_root))
    print("fixtures : %d" % len(selected))
    for bucket in case_mod.BUCKETS:
        extra = ""
        if bucket == "pending" and counts.get(bucket):
            blocked = {}
            for case in selected:
                if case.bucket != "pending":
                    continue
                key = case.expect.get("blocked_by")
                blocked[key] = blocked.get(key, 0) + 1
            extra = " (%s)" % ", ".join("%s %d" % (k, blocked[k]) for k in sorted(blocked))
        print("  %-9s %d%s" % (bucket + ":", counts.get(bucket, 0), extra))
    print("goldens  : %s" % _golden_line(*golden_stats(selected, root)))
    for line in describe_assets(profiles, tools, stubs, repo_root):
        print(line)
    print("")
    for case in selected:
        extra = ""
        if case.kind == "pending":
            extra = "  blocked_by=%s：%s" % (
                case.expect.get("blocked_by"),
                case.expect.get("reason"),
            )
        elif case.stub_only:
            extra = "  [stub-only]"
        print("%-45s %-10s %-3s%s" % (case.rel, case.kind, case.phase, extra))
    return EXIT_OK


def _golden_line(required, present):
    missing = required - present
    return "%d required, %d present, %d missing（missing 的用例记为 DRAFT）" % (
        required,
        present,
        missing,
    )


def cmd_check_fakes(root, repo_root, profiles, tools, stubs, errors):
    print("RILL 0.1.0 host assets")
    for profile in sorted(profiles):
        item = profiles[profile]
        try:
            bound = host_mod.bind_capabilities(
                item, lambda binding: {"provider": binding.provider, "ref": binding.ref}
            )
            slots = sum(1 for name in host_mod.CAPABILITY_SLOTS if bound.slot(name) is not None)
        except (KeyError, host_mod.ProfileError) as exc:
            print("FAIL  profile %s 绑定失败：%s" % (item.name, exc))
            continue
        print(
            "PASS  profile %-6s kind=%s slots=%s bound=%d"
            % (item.name, item.kind, ",".join(host_mod.CAPABILITY_SLOTS), slots)
        )
    if tools is not None:
        print(
            "PASS  fake tools %s：%s"
            % (_rel(tools.path, repo_root), ", ".join(sorted(tools.scripts)))
        )
    if stubs is not None:
        print(
            "PASS  host stubs %s：%s"
            % (_rel(stubs.path, repo_root), ", ".join(fakes_mod.HOST_SLOTS))
        )
    for error in errors:
        print("FAIL  %s" % error)
    return EXIT_FAIL if errors else EXIT_OK


def cmd_show(case, sut, runner, repo_root):
    sut = runner.sut_for(case)
    print("case : %s (%s, %s)" % (case.rel, case.kind, case.phase))
    print("sut  : %s" % sut.display)
    if case.kind == "pending":
        print("pending: blocked_by=%s" % case.expect.get("blocked_by"))
        print("reason : %s" % case.expect.get("reason"))
        return EXIT_OK

    source = runner._source_arg(case)
    if case.kind == "tokens":
        result = sut.run(["tokenize", source], env=case.sut_env)
    elif case.kind == "error":
        command = case.expect.get("command", "check")
        if command == "tokenize":
            result = sut.run(["tokenize", source], env=case.sut_env)
        elif command == "parse":
            result = sut.run(["parse", "--dump-ast", source, "--profile", "shell"], env=case.sut_env)
        else:
            result = sut.run(["check", source, "--profile", "shell"], env=case.sut_env)
    elif case.kind == "warning":
        result = sut.run(["check", source, "--profile", "shell"], env=case.sut_env)
    elif case.kind == "check":
        result = sut.run(
            ["check", source, "--profile", case.profiles()[0]], env=case.sut_env
        )
    elif case.kind == "run":
        result = sut.run(
            [
                "run",
                source,
                "--profile",
                case.expect["profile"],
                "--fakes",
                runner._fakes_arg(case),
            ],
            env=case.sut_env,
        )
    else:
        result = sut.run(
            ["parse", "--dump-ast", source, "--profile", case.profiles()[0]],
            env=case.sut_env,
        )

    print("exit : %r" % result.exit_code)
    if result.stderr.strip():
        print("stderr:")
        print(result.stderr.rstrip())
    if result.payload:
        print("stdout:")
        print(json.dumps(result.payload, indent=2, ensure_ascii=False, sort_keys=True))
    if result.status == "not_implemented":
        return EXIT_NOT_IMPLEMENTED
    return EXIT_OK


def run_cases(selected, sut, root, repo_root):
    runner = runner_mod.Runner(sut, root, repo_root)
    outcomes = [runner.run(case) for case in selected]
    return outcomes


def _retired_pending(root):
    """统计 pending/ 下 ``retired: true`` 的痕迹目录；不参与发现与执行。"""
    count = 0
    pending_root = os.path.join(root, "pending")
    for dirpath, _, file_names in os.walk(pending_root):
        if case_mod.CASE_FILE not in file_names:
            continue
        try:
            with open(os.path.join(dirpath, case_mod.CASE_FILE), encoding="utf-8") as handle:
                doc = json.load(handle)
        except (OSError, ValueError):
            continue
        if isinstance(doc, dict) and doc.get("retired") is True:
            count += 1
    return count


def gate_problems(selected, summary, root):
    """``--all`` 的额外判据：见过的桶齐全 + pending 为 0。"""
    problems = []
    counts = case_mod.bucket_counts(selected)
    for bucket in ("positive", "negative", "host"):
        if not counts.get(bucket):
            problems.append("桶 %s 没有用例" % bucket)
    pending = sum(summary["pending"].values())
    if pending:
        problems.append("pending=%d（要求 0）" % pending)
    return problems


def summarize(outcomes):
    summary = {
        "compliance": {status: 0 for status in (runner_mod.PASS, runner_mod.FAIL, runner_mod.BLOCK, runner_mod.DRAFT)},
        "smoke": {status: 0 for status in (runner_mod.PASS, runner_mod.FAIL, runner_mod.BLOCK, runner_mod.DRAFT)},
        "pending": {key: 0 for key in case_mod.BLOCKED_BY},
    }
    for outcome in outcomes:
        bucket = outcome.case.bucket
        group = "smoke" if bucket == "smoke" else "compliance"
        if outcome.status == runner_mod.PENDING:
            blocked = outcome.case.expect.get("blocked_by")
            summary["pending"][blocked] = summary["pending"].get(blocked, 0) + 1
        else:
            summary[group][outcome.status] += 1
    return summary


def exit_code(summary):
    compliance = summary["compliance"]
    smoke = summary["smoke"]
    if compliance[runner_mod.FAIL] or smoke[runner_mod.FAIL]:
        return EXIT_FAIL
    if compliance[runner_mod.BLOCK] or compliance[runner_mod.DRAFT]:
        return EXIT_NOT_IMPLEMENTED
    if smoke[runner_mod.BLOCK] or smoke[runner_mod.DRAFT]:
        return EXIT_NOT_IMPLEMENTED
    return EXIT_OK


def verdict(code):
    return {
        EXIT_OK: "PASS",
        EXIT_FAIL: "FAIL",
        EXIT_NOT_IMPLEMENTED: "NOT IMPLEMENTED",
    }.get(code, "FAIL")


def print_human(
    selected, sut, root, repo_root, profiles, outcomes, summary, code, filters, gate=None
):
    counts = case_mod.bucket_counts(selected)
    print("RILL 0.1.0 harness")
    print("root     : %s" % _rel(root, repo_root))
    print("sut      : %s" % sut.display)
    if gate is not None:
        print(
            "gate     : all buckets; pending=%d, retired=%d, problems=%s"
            % (
                gate["pending"],
                gate["retired"],
                "; ".join(gate["problems"]) if gate["problems"] else "无",
            )
        )
    overrides = sorted(
        {
            " ".join(shlex.split(outcome.case.sut))
            if isinstance(outcome.case.sut, str)
            else " ".join(outcome.case.sut)
            for outcome in outcomes
            if outcome.case.sut
        }
    )
    if overrides:
        print("sut(smoke): %s" % "; ".join(overrides))
    print("profiles : %s" % (", ".join(sorted(profiles)) if profiles else "无"))
    print(
        "fixtures : %d (%s)"
        % (len(selected), ", ".join("%s %d" % (b, counts[b]) for b in case_mod.BUCKETS if counts.get(b)))
    )
    if filters:
        print("filters  : %s" % filters)
    print("")

    for outcome in outcomes:
        if outcome.status != runner_mod.PENDING:
            print(outcome.line())
    pending = [item for item in outcomes if item.status == runner_mod.PENDING]
    if pending:
        print("")
        for outcome in pending:
            print(outcome.line())

    print("")
    print("summary")
    for group in ("compliance", "smoke"):
        data = summary[group]
        print(
            "  %-10s %d passed, %d failed, %d blocked, %d draft"
            % (group + ":", data[runner_mod.PASS], data[runner_mod.FAIL], data[runner_mod.BLOCK], data[runner_mod.DRAFT])
        )
    print(
        "  %-10s %d not run (A %d, B %d)"
        % (
            "pending:",
            sum(summary["pending"].values()),
            summary["pending"].get("A", 0),
            summary["pending"].get("B", 0),
        )
    )
    print("VERDICT: %s (exit %d)" % (verdict(code), code))


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.all and (
        args.phase
        or args.kind
        or args.bucket
        or args.case
        or args.sut
        or args.list
        or args.check_fakes
        or args.show
    ):
        print("FAIL  --all 不能与筛选、--sut 或查看选项同用")
        return EXIT_FAIL
    repo_root = os.path.abspath(args.repo_root)
    root = os.path.abspath(args.root) if args.root else os.path.join(repo_root, "testdata", "0.1.0")

    all_cases, errors = case_mod.discover(root)
    profiles, tools, stubs, asset_errors = load_assets(root, repo_root)
    errors.extend(asset_errors)

    if errors:
        for error in errors:
            print("FAIL  %s" % error)
        print("")
        print("fixtures 不合法，未执行任何用例。")
        return EXIT_FAIL

    wanted = []
    for needle in args.case:
        try:
            wanted.append(case_mod.find_case(all_cases, needle).rel)
        except KeyError as exc:
            print("FAIL  %s" % exc)
            return EXIT_FAIL

    selected = filter_cases(all_cases, args, wanted)
    filters = " ".join(
        part
        for part in (
            "phase=%s" % args.phase if args.phase else "",
            "kind=%s" % args.kind if args.kind else "",
            "bucket=%s" % args.bucket if args.bucket else "",
            "case=%s" % ",".join(wanted) if wanted else "",
        )
        if part
    )

    if args.list:
        return cmd_list(selected, root, repo_root, profiles, tools, stubs)
    if args.check_fakes:
        return cmd_check_fakes(root, repo_root, profiles, tools, stubs, [])

    if args.sut:
        command = shlex.split(args.sut)
        sut = sut_mod.Sut(command, repo_root)
    else:
        sut, error = sut_mod.from_manifest(repo_root)
        if error:
            print("FAIL  %s" % error)
            return EXIT_FAIL

    if args.show:
        try:
            case = case_mod.find_case(selected, args.show)
        except KeyError as exc:
            print("FAIL  %s" % exc)
            return EXIT_FAIL
        return cmd_show(case, sut, runner_mod.Runner(sut, root, repo_root), repo_root)

    outcomes = run_cases(selected, sut, root, repo_root)
    summary = summarize(outcomes)
    code = exit_code(summary)
    gate = None
    if args.all:
        problems = gate_problems(selected, summary, root)
        if problems:
            code = EXIT_FAIL
        gate = {
            "pending": sum(summary["pending"].values()),
            "retired": _retired_pending(root),
            "problems": problems,
        }

    if args.json:
        payload = {
            "root": _rel(root, repo_root),
            "sut": sut.display,
            "placeholder": sut.placeholder,
            "filters": filters,
            "gate": gate,
            "cases": [
                {
                    "rel": outcome.case.rel,
                    "bucket": outcome.case.bucket,
                    "kind": outcome.case.kind,
                    "phase": outcome.case.phase,
                    "status": outcome.status,
                    "detail": outcome.detail,
                }
                for outcome in outcomes
            ],
            "summary": summary,
            "exit": code,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print_human(
            selected,
            sut,
            root,
            repo_root,
            profiles,
            outcomes,
            summary,
            code,
            filters,
            gate,
        )
    return code


if __name__ == "__main__":
    sys.exit(main())
