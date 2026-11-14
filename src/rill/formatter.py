"""RILL 压缩态/展示态的最小格式化器。

规范依据：``docs/RILL-0.1.0.md`` §4.16、§4.17。本模块只做 token 级机械
转换，不执行、不校验、不 import 宿主模块。

范围与缺口（``docs/phases/PH-12/card.md`` §7 #1、#8）：
  - 这是 PH-12 为 round-trip 门禁准备的最小实现；PH-5 的
    ``expected/fmt`` golden、完整反向映射（内层覆盖外层）与二进制值规则
    仍归 PH-5。
  - 压缩态：去掉 token 之间的可选空白，保留语句换行；把映射长词换回短词引用。
  - 展示态：加空格、按花括号缩进，并把值类/动词类映射引用展开为长词。
  - 映射表按文件内首次绑定建模；局部覆盖尚未实现，登记为 PH-5 回归项。
  - 相邻词元的拼接关系按源码列位置保留，避免把 ``"a"$x`` 拆成两段。
"""

import re

from .lexer import tokenize

_NUMBER_RE = re.compile(r"-?[0-9]+")
_KEYWORDS = ("if", "else", "else-if", "each", "parallel", "break")
_SEMANTIC = set("<>()[]{}|@?,\"'`$\\")


def _normalize(source):
    return source.replace("\r\n", "\n").replace("\r", "\n")


def _line(source, lineno):
    lines = source.split("\n")
    return lines[lineno - 1] if 1 <= lineno <= len(lines) else ""


def _raw_width(source, token):
    """token 在源码里的原始宽度；相邻判定与 parser 的 ``_adjacent`` 同口径。"""
    if token.kind == "STRING":
        line = _line(source, token.line)
        start = token.col - 1
        if start >= len(line):
            return len(token.text)
        quote = line[start]
        index = start + 1
        while index < len(line):
            if quote == '"' and line[index] == "\\":
                index += 2
                continue
            if line[index] == quote:
                return index + 1 - start
            index += 1
        return len(line) - start
    if token.kind in ("MAP_REF", "VERB"):
        return len(token.text) + 2
    if token.kind in ("VARIABLE", "FIELD"):
        return len(token.text) + 1
    if token.kind == "DOLLAR":
        return 1
    return len(token.text)


def _adjacent(source, previous, current):
    if previous.line != current.line:
        return False
    return current.col == previous.col + _raw_width(source, previous)


def _map_entries(tokens):
    """短词 -> (标记符, 长词)；同一文件内首次绑定，与 parser 的 setdefault 一致。"""
    entries = {}
    index = 0
    while index + 2 < len(tokens):
        if (
            tokens[index].kind == "MAP_SHORT"
            and tokens[index + 1].kind == "MAP_MARK"
            and tokens[index + 2].kind == "MAP_LONG"
        ):
            entries.setdefault(
                tokens[index].text,
                (tokens[index + 1].text, tokens[index + 2].text),
            )
            index += 3
            continue
        index += 1
    return entries


def _quote(text):
    """输出一个回读值不变的字符串字面量；单引号优先。"""
    if "'" not in text and "\\" not in text and '"' not in text:
        return "'" + text + "'"
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + escaped + '"'


def _render(token):
    kind = token.kind
    if kind == "STRING":
        return _quote(token.text)
    if kind == "VARIABLE":
        return "$" + token.text
    if kind == "FIELD":
        return "." + token.text
    if kind == "DOLLAR":
        return "$"
    if kind == "VERB":
        return "<" + token.text + ">"
    if kind == "MAP_REF":
        return "`" + token.text + "`"
    if kind == "MAP_HEADER":
        return "//map{"
    if kind == "FN_HEADER":
        return "//fn{"
    return token.text


def _value_replacement(text, reverse_value):
    """把长词前缀换回短词引用；长词优先，避免 alpha/alphabet 互相遮住。"""
    for long_word in sorted(reverse_value, key=len, reverse=True):
        if not long_word:
            continue
        if text == long_word:
            return "`" + reverse_value[long_word] + "`"
        if text.startswith(long_word):
            rest = text[len(long_word):]
            if rest and not rest[0].isalnum() and rest[0] not in "_-":
                return "`" + reverse_value[long_word] + "`" + rest
    return None


def _units(tokens, source, mode):
    entries = _map_entries(tokens)
    reverse_value = {}
    reverse_verb = {}
    for short, (marker, long_word) in entries.items():
        if marker in ("'", "`"):
            reverse_value.setdefault(long_word, short)
        else:
            reverse_verb.setdefault(long_word, short)

    units = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.kind == "EOF":
            break
        if token.kind == "NEWLINE":
            units.append({"newline": True})
            index += 1
            continue

        tight = index > 0 and tokens[index - 1].kind != "NEWLINE" and _adjacent(
            source, tokens[index - 1], token
        )
        text = None
        next_index = index + 1

        if mode == "display":
            mapped = entries.get(token.text)
            if token.kind == "MAP_REF" and mapped and mapped[0] in ("'", "`"):
                parts = [mapped[1]]
                cursor = index + 1
                while cursor < len(tokens) and tokens[cursor].kind in (
                    "BARE",
                    "STRING",
                    "MAP_REF",
                ):
                    if not _adjacent(source, tokens[cursor - 1], tokens[cursor]):
                        break
                    if tokens[cursor].kind == "STRING":
                        parts.append(tokens[cursor].text)
                    elif tokens[cursor].kind == "MAP_REF":
                        inner = entries.get(tokens[cursor].text)
                        if inner and inner[0] in ("'", "`"):
                            parts.append(inner[1])
                        else:
                            parts.append(tokens[cursor].text)
                    else:
                        parts.append(tokens[cursor].text)
                    cursor += 1
                text = _quote("".join(parts))
                next_index = cursor
            elif token.kind == "VERB" and mapped and mapped[0] == "<":
                text = "<" + mapped[1] + ">"
        else:
            if token.kind in ("BARE", "STRING"):
                text = _value_replacement(token.text, reverse_value)
            elif token.kind == "VERB":
                short = reverse_verb.get(token.text)
                if short:
                    text = "<" + short + ">"

        if text is None:
            text = _render(token)
        units.append(
            {"newline": False, "kind": token.kind, "text": text, "tight": tight}
        )
        index = next_index
    return units


def _merges(previous, current):
    """压缩态下两个词元直接拼接是否会改变词法切分。"""
    if not previous or not current:
        return False
    left, right = previous[-1], current[0]
    return (left.isalnum() or left in "_-.:$") and (
        right.isalnum() or right in "_-."
    )


def _display_space(previous, current):
    if current["tight"]:
        return False
    if previous["kind"] in ("LBRACKET", "LPAREN", "MAP_HEADER", "FN_HEADER"):
        return current["kind"] != "LBRACE"
    if current["kind"] in ("RBRACKET", "RPAREN", "COMMA", "RBRACE"):
        return False
    return True


def format_tokens(tokens, source, mode):
    """把 token 流重排为压缩态或展示态文本。"""
    source = _normalize(source)
    units = _units(tokens, source, mode)
    out = []
    depth = 0
    previous = None
    at_line_start = False
    for unit in units:
        if unit.get("newline"):
            out.append("\n")
            at_line_start = True
            previous = None
            continue
        if unit["kind"] == "RBRACE":
            depth = max(0, depth - 1)
        if at_line_start and mode == "display":
            out.append("  " * depth)
        elif previous is not None:
            if mode == "display":
                if _display_space(previous, unit):
                    out.append(" ")
            elif not unit["tight"] and _merges(previous["text"], unit["text"]):
                out.append(" ")
        out.append(unit["text"])
        if unit["kind"] == "LBRACE":
            depth += 1
        at_line_start = False
        previous = unit
    return "".join(out).rstrip("\n") + "\n"


def format_source(source, mode):
    """``mode`` 只接受 ``compress`` / ``display``。"""
    if mode not in ("compress", "display"):
        raise ValueError("未知格式 %r（只允许 compress / display）" % (mode,))
    return format_tokens(tokenize(source), source, mode)
