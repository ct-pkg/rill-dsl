"""0.1.1 B-1：`Opaque` 的测试通道（fakes）与 C-8 验收。

用法：python3 tests/opaque/test_opaque_channel.py（退出 0 = 通过）。

通道只在 ``tests/opaque`` 里生效：``support.load_test_tools`` 把
``$test-opaque`` 标记解成 ``Opaque`` 后装进假宿主（``FakeVerbRegistry``）。
生产代码与真宿主不引用该通道。断言：
1. 标记解出 ``Opaque(handle, tag)``；
2. 运行时透传同一性：值从 ``<read>`` 到 ``<send>`` 是同一对象；
3. truthy：``if $h`` 走真分支；
4. 边界不有损：``jsonable`` 原样返回，Opaque 不可 JSON 序列化；
5. 反向覆盖：生产 ``fakes.load_tools`` 对标记保持惰性；``src/rill`` 不引用通道。
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from support import load_test_tools  # noqa: E402

from rill import fakes, loader, parser, lexer, value  # noqa: E402
from rill.eval_simple import Interpreter  # noqa: E402
from rill.host.shell import jsonable  # noqa: E402

FAKES = os.path.join(HERE, "fakes-opaque.json")
SOURCE = os.path.join(HERE, "source.ri")


def parse_source_file():
    with open(SOURCE, encoding="utf-8") as handle:
        return parser.parse(lexer.tokenize(handle.read()))


def case_marker_decodes_to_opaque():
    verbs = load_test_tools(FAKES)
    outcome = verbs.call("read", {})
    handle = outcome.value
    assert isinstance(handle, value.Opaque), "标记必须解出 Opaque，实际 %r" % (handle,)
    assert value.kind(handle) == "opaque"
    assert handle.handle == "test-handle-1"
    assert handle.tag == "stream"


def case_runtime_passthrough_and_truthy():
    verbs = load_test_tools(FAKES)
    tree = parse_source_file()
    tables = loader.check_program(tree)
    interp = Interpreter(verbs, functions=tables.functions)
    outcome = interp.eval_program(tree)

    assert outcome.ok is True, outcome
    assert outcome.value == "done", outcome.value
    handle = interp.log[0]["value"]
    assert isinstance(handle, value.Opaque), interp.log[0]
    assert interp.log[1]["object"] is handle, "透传必须是同一对象，不能复制/改写"
    assert [entry["verb"] for entry in interp.log] == ["read", "send", "parse"]


def case_opaque_is_not_stringified_at_boundary():
    handle = value.Opaque("test-handle-2", tag="stream")
    assert jsonable(handle) is handle, "边界层不得把 Opaque 转成文本/对象"
    try:
        json.dumps({"value": jsonable(handle)})
    except TypeError:
        return
    raise AssertionError("Opaque 必须保持不可 JSON 序列化，不能有损转字符串")


def case_production_fakes_is_inert():
    """反向覆盖：生产 --fakes 装载器不认识标记，真宿主不可能凭空产出 Opaque。"""
    outcome = fakes.load_tools(FAKES).call("read", {})
    assert not isinstance(outcome.value, value.Opaque), outcome.value
    assert outcome.value == {
        "$test-opaque": {"handle": "test-handle-1", "tag": "stream"}
    }, outcome.value


def case_channel_is_test_only():
    src_root = os.path.join(ROOT, "src", "rill")
    for current, _dirs, files in os.walk(src_root):
        for name in files:
            if not name.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(current, name), src_root)
            with open(os.path.join(current, name), encoding="utf-8") as handle:
                text = handle.read()
            assert "$test-opaque" not in text, "%s 不得引用测试通道" % rel
            if rel != "value.py":
                assert "Opaque(" not in text, "%s 不得构造 Opaque" % rel


def main():
    case_marker_decodes_to_opaque()
    case_runtime_passthrough_and_truthy()
    case_opaque_is_not_stringified_at_boundary()
    case_production_fakes_is_inert()
    case_channel_is_test_only()
    print("PASS opaque channel: C-8 透传/truthy + 测试专用守卫")


if __name__ == "__main__":
    main()
