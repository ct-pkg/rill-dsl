"""RILL AST 节点词汇、字段顺序与序列化。

节点是普通 dict：``{"kind": ..., <按 FIELDS 顺序的字段...>, "span": {"line","col"}}``。
``FIELDS`` 是唯一的字段顺序来源；新增节点只改这一处，序列化与 golden 都随之稳定。

规范依据：``docs/RILL-0.1.0.md`` §三、§4.17（忽略 span 后节点类型与 value 逐一相等）。
本模块不解析、不校验、不感知宿主。
"""

import json

# kind -> 字段顺序（不含 kind 与 span）。顺序即 JSON 键顺序，golden 可读性依赖它。
FIELDS = {
    # 程序与区块
    "Program": ("headers", "body"),
    "MapBlock": ("entries",),
    "MapEntry": ("short", "marker", "long"),
    "FnBlock": ("defs",),
    "FnDef": ("name", "template", "body"),
    "Block": ("body",),
    # 语句
    "SimpleStmt": ("call", "tail", "pipe"),
    "CallStmt": ("name", "args", "tail", "pipe"),
    "PrepBlockStmt": ("prep", "subject", "block"),
    "IfStmt": ("branches", "else_body"),
    "IfBranch": ("condition", "body"),
    "EachStmt": ("var", "source", "body", "tail"),
    "ParallelStmt": ("branches", "results", "pipe"),
    "BreakStmt": ("value", "target"),
    # 语句尾巴
    "Assign": ("target",),
    "OkBlock": ("body",),
    "ErrorBlock": ("body",),
    "IntoBlock": ("body",),
    # 调用与表达式
    "VerbCall": ("subject", "verb", "object", "post"),
    "Adverb": ("items",),
    "PrepPhrase": ("prep", "object"),
    "Pipe": ("stages",),
    # 值
    "String": ("value",),
    "Number": ("value",),
    "Variable": ("name",),
    "Default": ("name", "value"),
    "Self": (),
    "Field": ("name",),
    "Bare": ("text",),
    "Concat": ("parts",),
}

SPAN_KEY = "span"


def make(kind, span=None, **fields):
    """按 FIELDS 的字段顺序构造节点；字段缺失/多余都视为实现错误。"""
    if kind not in FIELDS:
        raise ValueError("未知 AST 节点 %r" % (kind,))
    expected = FIELDS[kind]
    if set(fields) != set(expected):
        missing = sorted(set(expected) - set(fields))
        extra = sorted(set(fields) - set(expected))
        raise ValueError(
            "节点 %s 字段不符：缺 %s，多 %s" % (kind, missing or "无", extra or "无")
        )
    node = {"kind": kind}
    for name in expected:
        node[name] = fields[name]
    node[SPAN_KEY] = span
    return node


def strip_spans(value):
    """递归删除 span 键；§4.17 的等价判据就是比较它。"""
    if isinstance(value, dict):
        return {
            key: strip_spans(item)
            for key, item in value.items()
            if key != SPAN_KEY
        }
    if isinstance(value, list):
        return [strip_spans(item) for item in value]
    return value


def to_json(node):
    """`--dump-ast` 的稳定序列化：保留字段顺序，非 ASCII 不转义。"""
    return json.dumps(node, ensure_ascii=False, sort_keys=False)
