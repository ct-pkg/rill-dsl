"""0.1.1 B-1：`Opaque` 的测试专用通道。

只在 ``tests/opaque`` 里使用：读取与 ``--fakes`` 同 schema 的 JSON，
把 ``$test-opaque`` 标记解成 ``Opaque`` 后装进 ``FakeVerbRegistry``。
生产代码（``src/rill``）不引用本模块，生产 ``fakes.load_tools`` 对标记保持惰性。
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from rill import value  # noqa: E402
from rill.verbs import FakeVerbRegistry  # noqa: E402

TOOLS_SCHEMA = "rill-fakes-tools/0"
TEST_OPAQUE = "$test-opaque"


def decode_test_value(item):
    if isinstance(item, list):
        return [decode_test_value(entry) for entry in item]
    if isinstance(item, dict):
        if set(item) == {TEST_OPAQUE}:
            spec = item[TEST_OPAQUE]
            if not isinstance(spec, dict) or "handle" not in spec:
                raise ValueError("%s 需要 {handle, tag?} 对象" % TEST_OPAQUE)
            return value.Opaque(spec["handle"], tag=spec.get("tag", "opaque"))
        return {key: decode_test_value(entry) for key, entry in item.items()}
    return item


def load_test_tools(path):
    with open(path, encoding="utf-8") as handle:
        doc = json.load(handle)
    if doc.get("schema") != TOOLS_SCHEMA:
        raise ValueError("fakes schema 必须是 %r" % TOOLS_SCHEMA)
    verbs = FakeVerbRegistry()
    for name, spec in doc["tools"].items():
        verbs.register(
            name,
            [decode_test_value(item) for item in spec.get("queue", [])],
            default=decode_test_value(spec.get("default")),
        )
    return verbs
