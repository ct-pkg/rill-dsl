# PH-22 红证（baseline: e4bf1bb）

> 按 PH-22 卡 §6：先测后码。红证在 `git worktree` 副本上执行，未在原件上反复改。
> 副本内容：`e4bf1bb`（PH-22-T1 规范提交）+ 仅复制本相新增的 `tests/phase22/*.py`。

基线：`e4bf1bb docs(spec): PH-22-T1 函数签名去名`
命令：`python3 tests/phase22/<file>`

## T2 解析（tests/phase22/test_fn_shape_parse.py）

```console
$ python3 tests/phase22/test_fn_shape_parse.py
Traceback (most recent call last):
  ...
  File ".../src/rill/parser.py", line 86, in _error
    raise ParseError(code, message, token.line, token.col)
rill.errors.ParseError: 期望 函数名（@ 后必须是字符串），实际 'send'
```

退出码非 0：基线解析器仍要求 `@` 后跟字符串名字。

## T3 加载（tests/phase22/test_fn_shape_load.py）

```console
$ python3 tests/phase22/test_fn_shape_load.py
rill.errors.ParseError: 期望 函数名（@ 后必须是字符串），实际 'send'
```

退出码非 0。

## T4 求值（tests/phase22/test_fn_shape_eval.py）

```console
$ python3 tests/phase22/test_fn_shape_eval.py
rill.errors.ParseError: 期望 函数名（@ 后必须是字符串），实际 'read'
```

退出码非 0。

## T7 编辑器（tests/phase22/test_editor_grammar.py）

```console
$ python3 tests/phase22/test_editor_grammar.py
File ".../tests/phase22/test_editor_grammar.py", line 29, in test_fn_rules_match_verb_call
    assert "<[^>\\n]+>" in pattern, pattern
AssertionError: (@)([ \t]*)("(?:[^"\\\n]|\\.)*"|'[^'\n]*')
```

退出码非 0：基线语法仍匹配 `@ "name"`。

## T5 对拍红

`tools/diff/diff.py --layer ast --filter fn` 在基线副本上无法运行：`--filter` 与
`--all` 在 PH-22 之前不存在（见卡面偏差表）。T5 的“先建红”以 T2/T3/T4 的 Python 侧
红证为准，CT 侧在 T5 内按同一批夹具逐层转绿。
