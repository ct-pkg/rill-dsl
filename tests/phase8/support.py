"""PH-8 测试共用夹具：源码解析、fake registry、结果与轨迹断言。

不 import 被测实现的控制流函数；实现缺失时由 `rill.eval_simple` 的
后续求值路径直接报错。
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from rill import lexer, parser, result
from rill.eval_simple import EvalError, Interpreter
from rill.verbs import FakeVerbRegistry


def parse_source(text):
    return parser.parse(lexer.tokenize(text))


def success(value=None):
    return result.ExecOutcome.success(value)


def failure(error=None):
    return result.ExecOutcome.failure(error)


def registry(script):
    """script: name -> 结果列表，或 {"queue": [...], "default": 结果}。"""
    verbs = FakeVerbRegistry()
    for name, spec in script.items():
        if isinstance(spec, dict):
            verbs.register(name, spec.get("queue", []), default=spec.get("default"))
        else:
            verbs.register(name, spec)
    return verbs


def run(source, script, variables=None):
    interp = Interpreter(registry(script))
    return interp, interp.eval_program(parse_source(source), variables=variables)


def called(interp):
    return [entry["verb"] for entry in interp.log]


def objects(interp, verb):
    return [entry["object"] for entry in interp.log if entry["verb"] == verb]


def events(interp, name):
    return [entry for entry in interp.trace if entry["event"] == name]
