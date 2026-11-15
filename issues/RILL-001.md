---
id: RILL-001
status: open
owner: REV
opened: 2026-11-16
anchor: 7d80c79
---

## 现象

0.1.0 判定中的 C-8（`Opaque` 值通道）证据是 Python 专用，产品改为 CT 唯一实现后不可复跑：

- `tests/opaque/test_opaque_channel.py:26-28` 直接 import `rill.fakes`、`rill.loader`、`rill.parser`、`rill.lexer`、`rill.value`、`rill.eval_simple.Interpreter`、`rill.host.shell.jsonable`；`src/rill/` 退场后该文件 `ModuleNotFoundError`。
- `tests/opaque/support.py:16-17` 同样依赖 `rill.value` 与 `rill.verbs.FakeVerbRegistry`。
- CT 侧没有对应值种类：`ct/src/common/common.h.ct:141-150` 的 `enum JKind` 只有 `J_NULL/J_BOOL/J_INT/J_FLOAT/J_STR/J_BYTES/J_ARR/J_OBJ`，无 `Opaque`。

## 复现

当前（`src/rill/` 尚未删除）：

```
python3 tests/opaque/test_opaque_channel.py
```

Python 退场后预计得到：

```
ModuleNotFoundError: No module named 'rill'
```

CT 侧缺口可静态核对：

```
grep -c 'Opaque' ct/src/common/common.h.ct   # 期望 0
grep -n 'enum JKind' -A9 ct/src/common/common.h.ct
```

## 影响

- `docs/reviews/0.1.0-verdict.md` 的 C-8 与 `docs/reviews/opaque-c8-evidence.md` 的红绿证据失去可复跑性；PH-23 卡 §10 已把 C-8 改记为“证据归档、不可复跑”。
- 不影响 2026-11-15 的 GO 判定与 `v0.22.0` 已发布事实，只影响该条判据的回归能力。
- 阻塞“C-8 在任何 CI/门禁里复查”的能力，不阻塞 PH-23 收口。

## 期望

在 CT 侧补齐测试通道后，C-8 可用一条命令复跑，且满足：

1. 能构造 `Opaque(handle, tag)`，沿 `read → if → send` 链路保持**同一对象**（同一性可断言，不靠值相等）。
2. `if $h` 对 Opaque 走真分支；动词序列为 `read, send, parse`。
3. Opaque 穿过边界层时原样返回且**不可 JSON 序列化**（或给出等价的可核对错误码）。
4. 生产路径不产出 Opaque：生产 `--fakes` 对 `$test-opaque` 标记保持惰性，且有可机械检查的守卫。
5. 复跑命令独立可执行并给出 0/非 0 退出码；在通道未加入时该命令必须红（先红后绿，红证含 `baseline: <sha>` 与原始输出）。

验收命令建议：`python3 tests/opaque/run_ct.py`（或 `bash tests/opaque/run.sh`），并纳入 `tools/check.sh` 的既有门禁或作为独立脚本被收口记录引用。
