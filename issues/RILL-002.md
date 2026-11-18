---
id: RILL-002
status: open
owner: REV
opened: 2026-11-18
anchor: eb5c74b
---

## 现象

`parallel` 分支内的 `break` 带非字符串值时，分支失败被静默吞成整体成功：

- `ct/src/eval/eval.h.ct:197` 的 `break_error()` 只认 `J_STR`，其他类型返回 `NULL`。
- `ct/src/eval/eval.h.ct:504-515` 把分支 break 转成 `eout_failure(&br, break_error(bv))`；`br.error` 为 `NULL` 时 `first_error` 保持 0。
- `ct/src/eval/eval.h.ct:517-518` 因此走 `eout_success`，整个 `parallel` 返回 `ok:true`、退出 0。

规范 §4.15 允许 `break` 的值是 `NUMBER` / `$变量` / `.字段`，并规定“值最终落字符串”；本缺陷不是“只支持字符串”的能力差异，而是失败信号丢失。

## 复现

红测（修复前应失败）：

```console
$ python3 tests/regressions/test_break_value.py
```

最小脚本：

```rill
parallel {
    <read> missing.rill [error] { break 42 }
}
```

CT 侧修复前：

```console
$ ./ct/bin/rill run /tmp/b2.rill --profile shell
{"ok":true,"value":[null],"error":null,"host_meta":{},"host":{"profile":"shell",...}}
[exit=0]
```

Python 参考实现同一脚本为 `ok:false, error:42, exit=1`；CT 与参考实现不一致，且失败方向是“误报成功”。

同一根因也影响 `[results]` 块与函数体 break：修复前 CT 退化为 `"RILL DSL ERROR"`，虽不误报成功，但丢失用户给的 break 值。

### 红证（2026-11-18，baseline `eb5c74b`）

```console
$ python3 tests/regressions/test_break_value.py
Traceback (most recent call last):
  File "tests/regressions/test_break_value.py", line 80, in <module>
    test_parallel_break_number_is_failure()
  File "tests/regressions/test_break_value.py", line 48, in _assert_failure
    assert rc == 1, "退出码 %r，payload=%r" % (rc, payload)
AssertionError: 退出码 0，payload={'ok': True, 'value': [None], 'error': None, ...}
[exit=1]
```

## 影响

- 调用方只读 `payload.ok` 或退出码时，会把一个显式失败的分支当成成功；依赖 `parallel` 做 best-effort 汇聚的脚本会静默漏错。
- 违反规范 §4.15 的“值最终落字符串”，也违反 `{value, ok}` 信封的失败语义。
- 属于 `docs/RILL-0.1.0.md` §4.14 / §4.15 的运行时实现缺陷，不是设计缺口。

## 期望

1. `parallel` 分支内 `break 42` → 整体 `ok:false`、`error:"42"`、退出 1；`value` 仍为 `[null]`。
2. `[results]` 块内 `break 42` 同样得到 `"42"`；函数体内 `break 42` 在调用点 `[error]` 块中可见为 `"42"`（未处理调用仍按 §4.10 落默认错误串，这是既有语义）。
3. 字符串 break 值（`break "boom"`）保持原样。
4. CT 与 Python 两侧对同一脚本输出一致；红测覆盖上述三类位置。

## 处置（DEV 追加，不改 status）

fix: `07baf72`（`fix(ct): RILL-002 非字符串 break 值不再吞失败`）

- CT `break_error`：字符串原样、int/float/bool/null 落字符串；数组/对象/字节回落默认错误串。
- Python `result.break_error` 同口径，`eval_parallel._run_branch` / `_run_results` / `eval_fn` 三处接入。
- 重新 `./ct/build.sh` 产出 `ct/bin/rill`；构建脚本另加 `--c-boundary=allow`（`9cbf54f`，适配 ct 0.65 strict 边界）。

验证原始输出：

```console
$ ./ct/bin/rill run /tmp/b2.rill --profile shell
{"ok":false,"value":[null],"error":"42","host_meta":{},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
[exit=1]

$ PYTHONPATH=src python3 -m rill run /tmp/b2.rill --profile shell
{"ok": false, "value": [null], "error": "42", "host_meta": {}, "host": {"profile": "shell", "principal": {"kind": "os-user", "name": "samxx"}}}
[exit=1]

$ python3 tests/regressions/test_break_value.py
PASS
[exit=0]

$ bash ct/test.sh
VERDICT: PASS (exit 0)

$ python3 tools/diff/diff.py --layer eval
== total diffs: 0
```

脚本内容：

```rill
parallel {
    <read> missing.rill [error] { break 42 }
}
```
