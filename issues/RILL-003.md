---
id: RILL-003
status: verified
owner: REV
opened: 2026-11-18
anchor: ce97219
---

## 现象

`ct/src/eval/eval.h.ct` 的 `eval_fn_call` 用固定数组收集函数参数与遍历栈，超限分支静默丢弃：

- `pname[64]` / `pdef[64]` / `bind[64]` / `has[64]`；新增参数仅当 `np < 64`。
- `stack[512]`；入栈仅当 `sp < 512`。
- 加载期 `load_collect_params` 用动态 `ParamList`，不设这两个上限，因此“能加载、运行期丢参数”。

65 个介宾参数的函数可正常通过 `ct check`，运行期第 65 个参数根本没进 `pname`，函数体引用时报 `E-RUN-UNDEFINED`，而不是明确的 arity/limit 诊断。这比“不支持 >64 参数”更糟：调用点不会报缺参，错误位置指向函数体变量。

## 复现

红测（修复前应失败）：

```console
$ python3 tests/regressions/test_fn_param_limit.py
AssertionError: (65, 2, {'error': {'stage': 'run', 'code': 'E-RUN-UNDEFINED', ... '变量 $p65 未定义'}})
```

测试生成 65 与 600 个 `[to] $pN` 介宾参数；600 同时覆盖 `stack[512]`。加载期均接受：

```console
$ ./ct/bin/rill check /tmp/fn65.rill
{"warnings":[]}
[exit=0]
```

## 影响

- 参数超过 64 或模板节点超过 512 时，超出部分的参数收集被悄悄跳过；函数体可能读到未定义变量/外层同名变量，或默认值绑定错位。
- 没有用户可见的 known-limits 条目，也没有加载期诊断；用户无法从错误码判断是“参数太多”。
- 影响所有 `//fn` 调用，属于运行时正确性缺陷，不是设计限制。

## 期望

1. 移除固定上限：`pname`/`pdef`/`bind`/`has`/`stack` 改为按需增长（或加载期给出明确的 `E-LOAD-FN-LIMIT` 并写入 known-limits；本 issue 选前者）。
2. 65 与 600 参数的函数在 CT 与 Python 两侧都能绑定并返回最后一个参数值。
3. 无静默丢弃；若未来加防御性上限，必须在加载期报错。

## 红证（2026-11-18，baseline `ce97219`）

```console
$ python3 tests/regressions/test_fn_param_limit.py
AssertionError: (65, 2, {'error': {'stage': 'run', 'code': 'E-RUN-UNDEFINED', 'line': 0, 'col': 0, 'message': '变量 $p65 未定义'}})
[exit=1]
```

## 处置（DEV 追加，不改 status）

fix: `63ac0e8`（`fix(ct): RILL-003 函数参数收集移除 64/512 静默上限`）

- `pname` / `pdef` / `bind` / `has` 与遍历栈改为 `xrealloc` 按需增长。
- 删除 `if (np < 64)` 与 `if (sp < 512)` 的静默丢弃；加载期与运行期口径一致。
- 重新 `./ct/build.sh` 产出 `ct/bin/rill`。

验证原始输出：

```console
$ python3 tests/regressions/test_fn_param_limit.py
PASS
[exit=0]

$ bash ct/test.sh
VERDICT: PASS (exit 0)

$ python3 tools/diff/diff.py --layer eval
== total diffs: 0
```

回归覆盖 65（原 `pname[64]` 边界）与 600（原 `stack[512]` 边界）个介宾参数，CT 与 Python 两侧均返回最后一个参数值。

## 复核（REV）

- 复核日期：2026-11-18
- 干净检出 sha：`152365d`（`git fetch origin main` 后 `origin/main` = `152365de15e31f85f5554f70c866035a55e7cedb`）
- 临时目录：`<TMP>`（本次 `/tmp/rill-rev-s2Rusj`）；`git archive origin/main | tar -x -C <TMP>/work`
- 构建：`HOME=<TMP>/cthome CT_HOME=<TMP>/cthome/.ct CT=/Users/samxx/.local/bin/ct bash ct/build.sh` → 退出 0，`ct/bin/rill` 存在（sha256 `2f047f099ce2db61424023492434e75d058c7836dceecfb761af6b096e3f3d8f`）
- 环境：macOS，Python 3.15.2，ct 0.65.1
- 手工生成（内联 `python3`，非调用回归脚本）：按 issue 期望模板 `//fn{ @ <send> "x" [to] $p1 … [to] $pN { <send> $pN } }` + 调用 `[to] "v1" … [to] "vN"`，得到 `fn65.ri`（1397 字节）与 `fn600.ri`（13635 字节），置于 `<TMP>/repro/fn/`

逐项原始输出：

```console
$ ct/bin/rill run fn65.ri --profile shell
{"ok":true,"value":"v65","error":null,"host_meta":{},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
[exit=0]

$ PYTHONPATH=src python3 -m rill run fn65.ri --profile shell
{"ok": true, "value": "v65", "error": null, "host_meta": {}, "host": {"profile": "shell", "principal": {"kind": "os-user", "name": "samxx"}}}
[exit=0]

$ ct/bin/rill check fn65.ri
{"warnings":[]}
[exit=0]
```

```console
$ ct/bin/rill run fn600.ri --profile shell
{"ok":true,"value":"v600","error":null,"host_meta":{},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
[exit=0]

$ PYTHONPATH=src python3 -m rill run fn600.ri --profile shell
{"ok": true, "value": "v600", "error": null, "host_meta": {}, "host": {"profile": "shell", "principal": {"kind": "os-user", "name": "samxx"}}}
[exit=0]
```

两轮输出中 `E-RUN-UNDEFINED` 命中数均为 0（`grep -c` 对 stdout/stderr 均为 `0`）；65 参数脚本 `check` 退出 0，未见参数上限诊断。

补充回归（同一干净归档内）：

```console
$ python3 tests/regressions/test_fn_param_limit.py
PASS
[exit=0]

$ bash ct/test.sh
summary
  compliance: 18 passed, 0 failed, 0 blocked, 0 draft
  smoke:     0 passed, 0 failed, 0 blocked, 0 draft
  pending:   0 not run (A 0, B 0)
VERDICT: PASS (exit 0)

ct/test.sh: PASS
[exit=0]

$ python3 tools/diff/diff.py --layer eval
== layer=eval
   sources=24 ok=23 diagnostics=0 expected=1 diffs=0
   RESULT: PASS
== total diffs: 0
[exit=0]
```

结论：独立复现通过。65/600 个介宾参数在加载期与运行期口径一致，CT 与 Python 均绑定并返回最后一个参数值，无静默丢弃、无 `E-RUN-UNDEFINED`。
