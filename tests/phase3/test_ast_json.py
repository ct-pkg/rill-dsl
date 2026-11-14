"""PH-3-T1：AST 节点词汇、字段顺序与 span 归一化的独立断言。

用法：python3 tests/phase3/test_ast_json.py（退出 0 = 通过）。
不依赖 harness，也不启动 CLI；T1 的交付物只有 ast.py，验收只能在这一层做。
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from rill import ast


def main():
    prog = ast.make("Program", span={"line": 1, "col": 1}, headers=[], body=[])
    assert list(prog) == ["kind", "headers", "body", "span"], list(prog)
    assert prog["kind"] == "Program"

    string = ast.make("String", span={"line": 2, "col": 5}, value='a"b')
    assert list(string) == ["kind", "value", "span"], list(string)
    assert string["value"] == 'a"b'

    assert ast.strip_spans(prog) == {"kind": "Program", "headers": [], "body": []}
    assert ast.strip_spans({"x": [string]}) == {"x": [{"kind": "String", "value": 'a"b'}]}

    assert json.loads(ast.to_json(prog)) == prog

    expected = {
        "Program",
        "MapBlock",
        "MapEntry",
        "FnBlock",
        "FnDef",
        "Block",
        "SimpleStmt",
        "CallStmt",
        "VerbCall",
        "Adverb",
        "PrepPhrase",
        "PrepBlockStmt",
        "IfStmt",
        "IfBranch",
        "EachStmt",
        "ParallelStmt",
        "BreakStmt",
        "Assign",
        "OkBlock",
        "ErrorBlock",
        "IntoBlock",
        "Pipe",
        "String",
        "Number",
        "Variable",
        "Self",
        "Field",
        "Bare",
        "Concat",
    }
    missing = sorted(expected - set(ast.FIELDS))
    assert not missing, "缺少节点：%s" % ", ".join(missing)

    try:
        ast.make("NotANode")
    except ValueError:
        pass
    else:
        raise AssertionError("未知节点必须抛 ValueError")

    print("PASS ast-json: %d 个节点，字段顺序与 span 归一化符合预期" % len(expected))
    return 0


if __name__ == "__main__":
    sys.exit(main())
