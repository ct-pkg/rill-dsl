"""RILL 0.1.x 运行时值模型（PH-6）。

只定义值形态与真值判定，不做执行、不读 AST、不接宿主：
- STRING / NUMBER / 数组 / 对象 / null / bool 用 Python 原生类型承载；
- ``Bytes`` / ``Opaque`` 是给宿主预留的最小不可变包装，避免 Shell 接入时
  再改运行时核心；裸 ``bytes`` 与任意 Python 对象不算 Value。
规范依据：``docs/RILL-0.1.0.md`` §4.12（truthy/falsy）、§五（类型边界）；
形状缺口见 ``docs/phases/PH-6/card.md`` §8。
"""


class Bytes(object):
    """二进制值；只读，按内容比较。"""

    __slots__ = ("_data",)

    def __init__(self, data):
        if not isinstance(data, bytes):
            raise TypeError("Bytes 只接受 bytes，实际 %r" % type(data))
        self._data = data

    @property
    def data(self):
        return self._data

    def __eq__(self, other):
        return isinstance(other, Bytes) and self._data == other._data

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((Bytes, self._data))

    def __repr__(self):
        return "Bytes(%r)" % (self._data,)


class Opaque(object):
    """宿主句柄；只透传，不解释内容，按同一性比较。"""

    __slots__ = ("_handle", "_tag")

    def __init__(self, handle, tag="opaque"):
        self._handle = handle
        self._tag = tag

    @property
    def handle(self):
        return self._handle

    @property
    def tag(self):
        return self._tag

    def __repr__(self):
        return "Opaque(%r, tag=%r)" % (self._handle, self._tag)


def kind(value):
    """返回规范值类型名；不是 Value 时抛 TypeError。"""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, Bytes):
        return "bytes"
    if isinstance(value, Opaque):
        return "opaque"
    raise TypeError("不是 RILL Value：%r" % (value,))


def is_value(value):
    try:
        kind(value)
    except TypeError:
        return False
    return True


def passthrough(value):
    """宿主值透传：校验是 Value 后原样返回，不复制、不改写。"""
    kind(value)
    return value


def truthy(value):
    """§4.12：null/false/0/""/[]/{} 为 false，其余（含 Bytes/Opaque）为 true。"""
    value_kind = kind(value)
    if value_kind == "null" or value is False:
        return False
    if value_kind == "bool":
        return True
    if value_kind == "number":
        return value != 0
    if value_kind == "string":
        return value != ""
    if value_kind == "array":
        return len(value) > 0
    if value_kind == "object":
        return len(value) > 0
    return True
