"""PH-22 测试共用夹具：解析、加载、求值与 AST 规范化。"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from rill import ast, lexer, loader, parser, result  # noqa: E402
from rill.errors import LexError, LoadError, ParseError  # noqa: E402
from rill.eval_simple import EvalError, Interpreter  # noqa: E402
from rill.verbs import FakeVerbRegistry  # noqa: E402

__all__ = [
    "ROOT",
    "LexError",
    "LoadError",
    "ParseError",
    "EvalError",
    "Interpreter",
    "ast",
    "lexer",
    "loader",
    "parser",
    "result",
    "canonical",
    "sexpr",
    "parse_source",
    "load",
    "run_loaded",
    "objects",
    "success",
    "failure",
]


def parse_source(text):
    return parser.parse(lexer.tokenize(text))


def load(text, profile="shell"):
    return loader.check_program(parse_source(text), profile)


def canonical(node):
    return ast.strip_spans(node)


def sexpr(node):
    return json.dumps(canonical(node), ensure_ascii=False, sort_keys=True)


def success(value=None):
    return result.ExecOutcome.success(value)


def failure(error=None):
    return result.ExecOutcome.failure(error)


def registry(script):
    verbs = FakeVerbRegistry()
    for name, spec in script.items():
        if isinstance(spec, dict):
            verbs.register(name, spec.get("queue", []), default=spec.get("default"))
        else:
            verbs.register(name, spec)
    return verbs


def run_loaded(text, script=None, variables=None):
    tree = parse_source(text)
    tables = loader.check_program(tree)
    interp = Interpreter(registry(script or {}), functions=tables.functions)
    return interp, interp.eval_program(tree, variables=variables)


def objects(interp, verb):
    return [entry["object"] for entry in interp.log if entry["verb"] == verb]
