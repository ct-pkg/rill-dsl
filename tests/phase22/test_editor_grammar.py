"""PH-22-T7：编辑器语法匹配 ``@ <verb>``，不再匹配旧形态（``@`` 后跟字符串）。

覆盖 E-23。plain python 脚本与 pytest 均可运行。
"""

import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GRAMMAR = os.path.join(ROOT, "editors", "vscode", "syntaxes", "rill.tmLanguage.json")


def _load():
    with open(GRAMMAR, encoding="utf-8") as handle:
        return json.load(handle)


def test_grammar_is_valid_json():
    doc = _load()
    assert doc["scopeName"] == "source.rill"
    assert isinstance(doc["repository"], dict)


def test_fn_rules_match_verb_call():
    repo = _load()["repository"]
    for key in ("fn-definition", "function-call"):
        pattern = repo[key]["match"]
        assert "<[^>\\n]+>" in pattern, pattern
        assert '"' not in pattern and "'" not in pattern, pattern
        compiled = re.compile(pattern)
        assert compiled.search("@ <read>"), key
        assert compiled.search("@   <send>"), key
        assert not compiled.search("@" + " " + '"name"'), key
        assert not compiled.search("@ 'name'"), key


TESTS = [value for key, value in sorted(globals().items()) if key.startswith("test_")]


def main():
    for test in TESTS:
        test()
    print("PASS phase22 editor: %d 项" % len(TESTS))


if __name__ == "__main__":
    main()
