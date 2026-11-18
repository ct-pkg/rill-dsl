---
id: RILL-003
status: open
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

（待修复）
