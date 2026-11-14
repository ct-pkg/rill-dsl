"""PH-12-T3：压缩态↔展示态的 round-trip 门禁。

用法：python3 tests/phase12/test_roundtrip.py（退出 0 = 通过）。
覆盖 E-3：对全部可解析正例与双宿主脚本，``compress -> display ->
compress`` 后的 AST 忽略 span 必须与原文相等。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import ROOT, canonical, fixture_sources

from rill.ast import strip_spans
from rill.formatter import format_source
from rill.lexer import tokenize
from rill.parser import parse

GATE = os.path.join(ROOT, "tools", "check-fmt.sh")


def ast_of(source):
    return strip_spans(parse(tokenize(source)))


def host_scripts():
    found = []
    base = os.path.join(ROOT, "testdata", "0.1.0", "host")
    for dirpath, dir_names, file_names in os.walk(base):
        dir_names.sort()
        if "script.rill" in file_names and "expect.json" in file_names:
            found.append(os.path.join(dirpath, "script.rill"))
    found.sort()
    return found


def case_gate_script_exists():
    assert os.path.isfile(GATE), "缺少 round-trip 门禁：%s" % GATE


def case_all_parseable_fixtures_roundtrip():
    paths = [
        path
        for _, path, _ in fixture_sources(
            kinds=("ast", "check", "run", "warning", "host-ast-equal")
        )
    ]
    paths.extend(host_scripts())
    assert len(paths) >= 60, "round-trip 覆盖面过小：%d" % len(paths)

    failures = []
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        original = canonical(ast_of(source))
        compressed = format_source(source, "compress")
        if canonical(ast_of(compressed)) != original:
            failures.append((path, "compress"))
            continue
        displayed = format_source(compressed, "display")
        if canonical(ast_of(displayed)) != original:
            failures.append((path, "display"))
            continue
        recompressed = format_source(displayed, "compress")
        if canonical(ast_of(recompressed)) != original:
            failures.append((path, "recompress"))
    assert not failures, "round-trip AST 不等：%r" % failures[:5]


def main():
    case_gate_script_exists()
    case_all_parseable_fixtures_roundtrip()
    print(
        "PASS phase12 roundtrip: compress→display→compress AST 等价（%d 个 fixture）"
        % (
            len(
                fixture_sources(
                    kinds=("ast", "check", "run", "warning", "host-ast-equal")
                )
            )
            + len(host_scripts())
        )
    )


if __name__ == "__main__":
    main()
