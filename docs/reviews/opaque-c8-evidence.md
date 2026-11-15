# 0.1.0 C-8（`Opaque`）测试通道与验收证据

> 结论：求值器本来就有外部值承载路径，**不需要改求值器**；测试通道已落地，
> C-8 可验收。0.1.0 转 GO 与版本重编号是 §7 的**提案**，尚未执行。
> C-6（Python 参考实现冻结）保持：`git diff --quiet HEAD -- src/rill` rc=0。

## 1. 先判定：承载路径结论

| 项 | 结论 | 证据 |
| --- | --- | --- |
| 宿主返回值入口 | 存在；`ExecOutcome.value` 原样进入解释器 | `src/rill/eval_simple.py` `_call`：`outcome = self.verbs.call(...)`，随后 `entry["value"] = outcome.value`，返回值直接 `return outcome` |
| 变量读取 | 存在；`Variable` 直接从作用域取值，不复制/不改写 | `eval_value` 的 `if kind == "Variable": return scope.get(node["name"])` |
| truthy | 已支持；`Opaque` 落在“其余一切为真” | `src/rill/value.py#L95-L110` |
| 字符串拼接 | 不做隐式转换；非字符串直接报错（本相不需要触发） | `eval_simple.py` Concat 分支要求 `isinstance(part, str)`，否则 `E-RUN-CONCAT` |
| 边界序列化 | 不有损；`jsonable` 只转 `Bytes`，`Opaque` 原样返回 | `src/rill/host/shell.py#L142-L150` |

**探针（在改动前运行，直接给假宿主塞 `Opaque`）**：

```console
$ python3 - <<'PY'  # 摘要
...
print("ok=", out.ok, "value=", out.value)
print("identity_passthrough=", it.log[1]["object"] is h)
print("verbs=", [e["verb"] for e in it.log])
print("kinds=", [value.kind(e["object"]) for e in it.log])
PY
ok= True value= taken
identity_passthrough= True
verbs= ['read', 'send', 'send']
kinds= ['string', 'opaque', 'string']
```

结论：求值器不需要任何修改；缺的只是“测试层如何造出 `Opaque`”这一条入口。
因此不走 A 案。

## 2. 通道形态

| 项 | 内容 |
| --- | --- |
| 位置 | `tests/opaque/support.py#load_test_tools`，只被 `tests/opaque/test_opaque_channel.py` 引用 |
| 输入 | 与 `--fakes` 同 schema 的 JSON（`rill-fakes-tools/0`） |
| 标记 | `{"$test-opaque": {"handle": "...", "tag": "..."}}`，递归解成 `value.Opaque(handle, tag)` |
| 装配 | 解出的值直接注册进 `FakeVerbRegistry`；`ExecOutcome` 路径与生产 fake 相同 |
| 生产隔离 | `src/rill` 零改动；生产 `fakes.load_tools` 不认识该标记（原样当对象返回） |

样例：`tests/opaque/fakes-opaque.json` 的 `read.default` 返回
`$test-opaque`，`tests/opaque/source.ri` 用 `<read>` 取值、`if $h` 判真、
`<send> $h` 透传、最后 `<parse>` 返回字符串，避免把 `Opaque` 送进 CLI 输出。

## 3. C-8 断言（写明断言什么）

| # | 断言 | 方式 |
| --- | --- | --- |
| 1 | 标记解出 `Opaque`，`kind == "opaque"`，`handle`/`tag` 保留 | `case_marker_decodes_to_opaque` |
| 2 | 透传同一性：`interp.log[1]["object"] is interp.log[0]["value"]` | `case_runtime_passthrough_and_truthy` |
| 3 | truthy：`if $h` 真分支执行（动词序列 `read, send, parse`） | 同上 |
| 4 | 边界不有损：`jsonable(h) is h`，且 `json.dumps` 抛 `TypeError` | `case_opaque_is_not_stringified_at_boundary` |
| 5 | 反向覆盖：生产 `--fakes` 装载器对标记惰性；`src/rill` 不含 `$test-opaque`，除 `value.py` 外不出现 `Opaque(` | `case_production_fakes_is_inert`、`case_channel_is_test_only` |

## 4. 红绿证据

红（副本上把测试通道换成生产 `fakes.load_tools`，即“通道不存在”时）：

```console
$ git worktree add --detach /tmp/rill-c8-red <HEAD>
$ cp tests/opaque/{fakes-opaque.json,source.ri,test_opaque_channel.py} /tmp/rill-c8-red/tests/opaque/
$ # support.py 用生产 loader 顶替（不解标记）
$ python3 tests/opaque/test_opaque_channel.py
AssertionError: 标记必须解出 Opaque，实际 {'$test-opaque': {'handle': 'test-handle-1', 'tag': 'stream'}}
RED_exit=1
```

绿（当前工作树）：

```console
$ python3 tests/opaque/test_opaque_channel.py
PASS opaque channel: C-8 透传/truthy + 测试专用守卫
$ echo $?
0

$ git diff --quiet HEAD -- src/rill; echo $?
0
```

## 5. 门禁输出

```console
$ bash tools/check.sh all
== overall: PASS ==

$ bash tools/check-0.1.0.sh --all
compliance: 88 passed, 0 failed, 0 blocked, 0 draft
smoke:      2 passed, 0 failed, 0 blocked, 0 draft
pending:    0 not run (A 0, B 0)
VERDICT: PASS (exit 0)

$ python3 tools/diff/diff.py --all
== total diffs: 0

$ for f in tests/phase*/*.py tests/opaque/*.py; do python3 "$f"; done
total_fail=0
```

## 6. 影响面

- 语言语义、词法/语法/求值/格式化：零改动。
- 真宿主（Shell/Agent）：零改动；`src/rill` 零改动，C-6 仍成立。
- CT 对拍：零新增 fixture，`diff --all` 仍 0；CT 侧不引入 `Opaque`。
- 唯一新增：`tests/opaque/` 四个文件（通道、样例源、fakes 文档、测试）。

## 7. 提案：0.1.0 转 GO 与版本重编号（未执行，待批准）

依据 `AGENTS.md` 0.3 的 C 裁定：重编号触发条件 = C-8 转 GO。

### 7.1 文案改动

| # | 文件 | 现在 | 提案 |
| --- | --- | --- | --- |
| 1 | `docs/reviews/0.1.0-verdict.md` | C-8 `❌`；“能否发布 0.1.0：不能” | C-8 `✅`（证据指向本文件 §4）；发布判定改“能”；§3 改为“已验收（测试通道）” |
| 2 | `src/rill/__init__.py` | `0.12.0` | `0.22.0` |
| 3 | `CHANGELOG.md` | `Unreleased — PH-22` | 新增 `0.22.0 — 2026-11-15` 段，收编 PH-22 条目；`version-minor=22` 说明保留 |
| 4 | `AGENTS.md` 0.3 | PH-22 → `0.12.0`；重编号点“待定” | PH-22 → `0.22.0（重编号点，0.1.0 GO）`；PH-13…PH-21 仍 `0.12.0`；解耦说明与触发条件保留 |
| 5 | `docs/session-map.md` | 产品 `0.12.0` | `0.22.0`，注明重编号点 |
| 6 | `docs/reviews/0.1.0-verdict.md` §5 | `B-1` open | 标“已完成（测试通道，见 `opaque-c8-evidence.md`）” |
| 7 | tag | 无 | `v0.22.0`（批准后创建） |

### 7.2 重编号后的映射

| phase | 产品版本 |
| --- | --- |
| PH-12 | `0.12.0` |
| PH-13…PH-21 | `0.12.0` |
| PH-22 | `0.22.0`（重编号点） |

### 7.3 需要批准的点

- 是否按上表把产品版本一次补到 `0.22.0`（C 的“补到当时 phase 号”）。
- 是否同一条提交内改 verdict、版本、CHANGELOG、映射与 session-map，并建 `v0.22.0`。

批准前不改版本号、不建 tag；本文件只作提案。
