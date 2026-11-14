# PH-6 红证记录

每个任务在实现提交之前记录一次：`baseline`、命令、原始输出、退出码。
`baseline` 为实现落地前的提交（`git merge-base --is-ancestor <baseline> HEAD` 必须为真）。
实现完成后追加 `green` 行，原始输出不覆盖、不美化。

## PH-6-T1

- baseline: `1fde2fe`
- 命令: `python3 tests/phase6/test_value.py`
- 退出码: `1`
- 原始输出:

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase6/test_value.py", line 12, in <module>
    from rill import value
ImportError: cannot import name 'value' from 'rill' (/Users/samxx/trae-ws/rill-dsl/tests/phase6/../../src/rill/__init__.py)
```

- green: `python3 tests/phase6/test_value.py` → `rc=0`，
  `PASS value: 11 种值形态、Bytes/Opaque 只读与透传、真值判定`。

## PH-6-T2

- baseline: `1fde2fe`
- 命令: `python3 tests/phase6/test_result.py`
- 退出码: `1`
- 原始输出:

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase6/test_result.py", line 12, in <module>
    from rill import result
ImportError: cannot import name 'result' from 'rill' (/Users/samxx/trae-ws/rill-dsl/tests/phase6/../../src/rill/__init__.py)
```

- green: `python3 tests/phase6/test_result.py` → `rc=0`，
  `PASS result: ok 只看 ok、默认错误、$ 投影、exit_code 钩子、顶层中断`。

## PH-6-T3

- baseline: `1fde2fe`
- 命令: `python3 tests/phase6/test_truthy.py`
- 退出码: `1`
- 原始输出:

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase6/test_truthy.py", line 64, in <module>
    main()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase6/test_truthy.py", line 43, in main
    assert result.field(obj, "a") == 1
AttributeError: module 'rill.result' has no attribute 'field'
```

- green: `python3 tests/phase6/test_truthy.py` → `rc=0`，
  `PASS truthy: 6 个 falsy、9 个真值、$ 基准与 .字段`。

## PH-6-T4

- baseline: `1fde2fe`
- 命令: `python3 tests/phase6/test_verbs.py`
- 退出码: `1`
- 原始输出:

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase6/test_verbs.py", line 12, in <module>
    from rill import result, verbs
ImportError: cannot import name 'verbs' from 'rill' (/Users/samxx/trae-ws/rill-dsl/tests/phase6/../../src/rill/__init__.py)
```

- green: `python3 tests/phase6/test_verbs.py` → `rc=0`，
  `PASS verbs: 队列顺序、default、空队列失败、未注册 KeyError`。

## PH-6-T5

- baseline: `1fde2fe`
- 命令: `python3 tests/phase6/test_pipe.py`
- 退出码: `1`
- 原始输出:

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase6/test_pipe.py", line 12, in <module>
    from rill import pipe, result
ImportError: cannot import name 'pipe' from 'rill' (/Users/samxx/trae-ws/rill-dsl/tests/phase6/../../src/rill/__init__.py)
```

- green: `python3 tests/phase6/test_pipe.py` → `rc=0`，
  `PASS pipe: expr/stmt 分流、只传 value、失败短路、each 失败轮与恢复`。




