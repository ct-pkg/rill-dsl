"""函数签名形状键（PH-22 / D-022）。

形状只由模板第一段 ``verb_call`` 机械导出，用来替代字符串函数名：

  ``{verb, subject, object, preps[], adverbs[]}``

槽位（slot）：

  ``{"role": "none"}`` / ``{"role": "param"}`` / ``{"role": "const", "value": ...}``
  / ``{"role": "value"}``

模板侧的 ``param``（``$变量`` / ``$变量?默认值``）与调用侧的 ``value`` 都是
“这里是值”的位置；匹配时模板 ``param`` 接受调用侧任何非空值。常量位按值的
字符串形态比较：``'ok'`` / ``"ok"`` / ``ok`` 同值。参数名、默认值、状语值不进签名。

本模块只读 AST，不解析、不求值、不 import 宿主。
"""

SLOT_NONE = {"role": "none"}
SLOT_PARAM = {"role": "param"}
SLOT_VALUE = {"role": "value"}


def _strip_type_prefix(text):
    """P-025 未裁定前：常量位的 ``类型:值`` 前缀不进形状键。"""
    if ":" not in text:
        return text
    head, tail = text.split(":", 1)
    if not head or not tail:
        return text
    if not (head[0].isalpha() or head[0] == "_"):
        return text
    for ch in head:
        if not (ch.isalnum() or ch in "_-"):
            return text
    return tail


def const_value(node):
    """常量位的字符串形态；不是常量返回 ``None``。"""
    if not isinstance(node, dict):
        return None
    kind = node.get("kind")
    if kind == "String":
        return _strip_type_prefix(node["value"])
    if kind == "Bare":
        return _strip_type_prefix(node["text"])
    if kind == "Number":
        return str(node["value"])
    return None


def slot(node, template):
    """把一个值位归约为槽位；``template`` 区分定义侧与调用侧。"""
    if node is None:
        return dict(SLOT_NONE)
    kind = node.get("kind")
    if kind == "Variable" or kind == "Default":
        return dict(SLOT_PARAM if template else SLOT_VALUE)
    value = const_value(node)
    if value is not None:
        return {"role": "const", "value": value}
    return dict(SLOT_VALUE)


def _adverb_name(node):
    if not isinstance(node, dict):
        return ""
    if node.get("kind") == "Bare":
        text = node["text"]
    elif node.get("kind") == "String":
        text = node["value"]
    elif node.get("kind") == "Number":
        text = str(node["value"])
    else:
        return ""
    return text.split(":", 1)[0]


def adverb_names(post):
    names = set()
    for item in post:
        if item.get("kind") != "Adverb":
            continue
        for node in item["items"]:
            names.add(_adverb_name(node))
    return sorted(names)


def shape_of(call, template):
    """``verb_call`` → 形状键；``template`` 决定槽位身份用定义侧还是调用侧。"""
    preps = []
    for item in call["post"]:
        if item.get("kind") == "PrepPhrase":
            preps.append(
                {"prep": item["prep"], "object": slot(item["object"], template)}
            )
    return {
        "verb": call["verb"],
        "subject": slot(call["subject"], template),
        "object": slot(call["object"], template),
        "preps": preps,
        "adverbs": adverb_names(call["post"]),
    }


def _preps_of(call):
    return [item for item in call["post"] if item.get("kind") == "PrepPhrase"]


def _slot_accepts(def_slot, call_slot):
    role = def_slot["role"]
    if role == "none":
        return call_slot["role"] == "none"
    if role == "const":
        return (
            call_slot["role"] == "const"
            and call_slot.get("value") == def_slot.get("value")
        )
    # param / value：调用侧写任何值都算填上
    return call_slot["role"] != "none"


def _prep_optional(definition, index):
    """第 ``index`` 个介宾的参数位是否带默认值（可整段省略）。"""
    template = definition["template"][0]
    preps = _preps_of(template)
    if index >= len(preps):
        return False
    obj = preps[index]["object"]
    return obj.get("kind") == "Default"


def classify(definition, call_shape):
    """把调用形状与一个定义比对：``"exact"`` / ``"arity"`` / ``"none"``。"""
    def_shape = definition["shape"]
    if def_shape["verb"] != call_shape["verb"]:
        return "none"
    if not _slot_accepts(def_shape["subject"], call_shape["subject"]):
        return "none"
    if not _slot_accepts(def_shape["object"], call_shape["object"]):
        return "none"
    if def_shape["adverbs"] != call_shape["adverbs"]:
        return "none"

    def_preps = def_shape["preps"]
    call_preps = call_shape["preps"]
    if len(call_preps) > len(def_preps):
        return "none"

    names_def = [item["prep"] for item in def_preps]
    names_call = [item["prep"] for item in call_preps]
    if names_call == names_def[: len(names_call)]:
        status = "exact"
        for index in range(len(call_preps), len(def_preps)):
            if not _prep_optional(definition, index):
                status = "arity"
                break
    elif _is_subsequence(names_call, names_def):
        # 中间跳过介宾：不是形状相同，也不是“无候选”
        status = "arity"
    else:
        return "none"

    for index in range(len(call_preps)):
        if not _slot_accepts(def_preps[index]["object"], call_preps[index]["object"]):
            return "none"
    return status


def _is_subsequence(needle, haystack):
    position = 0
    for item in haystack:
        if position < len(needle) and needle[position] == item:
            position += 1
    return position == len(needle)


def find(definition_list, call_shape):
    """返回 ``(exact_defs, arity_def)``；调用只按精确相等选型。"""
    exact = []
    arity = None
    for definition in definition_list:
        status = classify(definition, call_shape)
        if status == "exact":
            exact.append(definition)
        elif status == "arity" and arity is None:
            arity = definition
    return exact, arity


def describe(shape):
    """错误 Hint 用的一行形状文本；不含参数名。"""
    parts = []

    def render(sl):
        role = sl["role"]
        if role == "none":
            return "-"
        if role == "param":
            return "$?"
        if role == "const":
            return repr(sl.get("value", ""))
        return "$"

    if shape["subject"]["role"] != "none":
        parts.append(render(shape["subject"]))
    parts.append("<%s>" % shape["verb"])
    parts.append(render(shape["object"]))
    for item in shape["preps"]:
        parts.append("[%s] %s" % (item["prep"], render(item["object"])))
    if shape["adverbs"]:
        parts.append("(%s)" % ",".join(shape["adverbs"]))
    return " ".join(parts)


def param_positions(definition, call):
    """按模板第一段对齐调用位置，返回 ``[(name, call_value_node)]``。

    ``call`` 已通过形状匹配；调用省略的尾部可选介宾不在结果里。
    """
    template = definition["template"][0]
    pairs = []

    subject = template["subject"]
    if subject is not None and subject.get("kind") in ("Variable", "Default"):
        pairs.append((subject["name"], call["subject"]))

    obj = template["object"]
    if obj.get("kind") in ("Variable", "Default"):
        pairs.append((obj["name"], call["object"]))

    template_preps = _preps_of(template)
    call_preps = _preps_of(call)
    for index in range(min(len(template_preps), len(call_preps))):
        target = template_preps[index]["object"]
        if target.get("kind") in ("Variable", "Default"):
            pairs.append((target["name"], call_preps[index]["object"]))
    return pairs
