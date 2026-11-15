"""用仓库内 RILL 实现为 VS Code 插件扫描器产出对照数据。

- 符号位置来自 ``src/rill/lexer.py`` 的真实 token 流；
- 函数定义/调用名再与 ``src/rill/parser.py`` 的 AST 交叉核对。
"""

import json
import os
import sys
from collections import Counter

EXCLUDE_DIRS = {".git", "node_modules", ".ctbuild", "dist", "out", "build", ".venv"}


def u16(text):
    return len(text.encode("utf-16-le")) // 2


def collect_rill_files(root):
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name for name in dirnames if name not in EXCLUDE_DIRS
        )
        for name in sorted(filenames):
            if name.endswith(".rill"):
                path = os.path.join(dirpath, name)
                result.append(os.path.relpath(path, root).replace(os.sep, "/"))
    return result


def raw_name(line, token):
    """返回 (name_start_utf16, raw_length_utf16, raw_content)。"""
    quote_index = token.col - 1
    quote = line[quote_index] if quote_index < len(line) else ""
    index = quote_index + 1
    while index < len(line):
        ch = line[index]
        if quote == '"' and ch == "\\":
            index += 2
            continue
        if ch == quote:
            break
        index += 1
    raw = line[quote_index + 1 : index]
    return u16(line[: quote_index + 1]), u16(raw), raw


def from_tokens(tokens, lines):
    definitions = []
    calls = []
    fn_depth = 0
    in_map = False
    previous = None
    for token in tokens:
        if in_map:
            if token.kind == "RBRACE":
                in_map = False
            previous = None
            continue
        if token.kind == "MAP_HEADER":
            in_map = True
            previous = None
            continue
        if token.kind == "FN_HEADER":
            fn_depth = 1
            previous = None
            continue
        if token.kind == "NEWLINE":
            previous = None
            continue
        if token.kind == "LBRACE" and fn_depth > 0:
            fn_depth += 1
        elif token.kind == "RBRACE" and fn_depth > 0:
            fn_depth -= 1
        if token.kind == "AT":
            previous = token
            continue
        if (
            token.kind == "STRING"
            and previous is not None
            and previous.kind == "AT"
            and previous.line == token.line
            and fn_depth in (0, 1)
        ):
            line = lines[token.line - 1]
            character, length, raw = raw_name(line, token)
            entry = {
                "name": token.text,
                "line": token.line - 1,
                "character": character,
                "length": length,
                "raw": raw,
            }
            (definitions if fn_depth == 1 else calls).append(entry)
        previous = token
    return definitions, calls


def from_ast(tree):
    definitions = []
    calls = []

    def walk(node):
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict) or "kind" not in node:
            return
        if node["kind"] == "CallStmt":
            calls.append(node["name"])
        for key, value in node.items():
            if key in ("kind", "span"):
                continue
            walk(value)

    for header in tree.get("headers", []):
        if header["kind"] == "FnBlock":
            definitions.extend(item["name"] for item in header["defs"])
    walk(tree.get("body", []))
    return definitions, calls


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    sys.path.insert(0, os.path.join(root, "src"))

    from rill.errors import LexError, ParseError
    from rill.lexer import tokenize
    from rill.parser import parse_with_warnings

    output = {"files": {}, "count": 0}
    for relative in collect_rill_files(root):
        path = os.path.join(root, relative)
        with open(path, "r", encoding="utf-8") as handle:
            source = handle.read()
        entry = {
            "definitions": [],
            "calls": [],
            "lex_error": None,
            "parse_error": None,
            "ast": None,
        }
        try:
            tokens = tokenize(source)
        except LexError as error:
            entry["lex_error"] = {"code": error.code, "line": error.line, "col": error.col}
            output["files"][relative] = entry
            continue

        lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        definitions, calls = from_tokens(tokens, lines)
        entry["definitions"] = definitions
        entry["calls"] = calls
        try:
            tree, _warnings = parse_with_warnings(tokens)
        except ParseError as error:
            entry["parse_error"] = {"code": error.code, "line": error.line, "col": error.col}
        else:
            ast_definitions, ast_calls = from_ast(tree)
            entry["ast"] = {
                "definitions": ast_definitions,
                "calls": ast_calls,
            }
            if Counter(item["name"] for item in definitions) != Counter(ast_definitions):
                entry["ast"]["definition_mismatch"] = True
            if Counter(item["name"] for item in calls) != Counter(ast_calls):
                entry["ast"]["call_mismatch"] = True
        output["files"][relative] = entry
        output["count"] += 1

    json.dump(output, sys.stdout, ensure_ascii=False, sort_keys=True)


if __name__ == "__main__":
    main()
