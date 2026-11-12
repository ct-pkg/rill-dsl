# T-006 工具 `json_build`

- **状态**：`unverified`
- **决策**：[D-006](../../decisions/D-006.md)、[D-008](../../decisions/D-008.md)、[D-014](../../decisions/D-014.md)
- **规范**：[02 §4](../dsl/02-grammar.md)、[03 §6](../dsl/03-semantics.md)、[07 §1](../dsl/07-runtime.md)
- **契约总则**：[README](README.md) §2–§6
- **里程碑**：无排期（可选注册集；`v0.1` 提及，rev.1 未引用）
- **工具名**：`json_build`（非关键字）
- **arity**：**变长**（`params_schema=NULL`），键值成对；required：无单个必填位，但必须成对
- **accepts_context**：否（变长工具不参与 `$` 注入）
- **返回值**：`json_object`
- **截断**：不截断

## 1. 输入

```
json_build "a" 1 "b" 2                 # {"a":1,"b":2}
json_build                             # {}
json_build "outer" (json_build "in" 1) # 嵌套靠分组实参
let k = "dyn"
json_build k 3                         # 键可以来自变量
```

`args_json`（偶数长度，键在偶位、值在奇位）：

```
["a", 1, "b", 2]
```

- 实参按书写顺序成对解释：第 0、2、4… 位是键，必须是 `string`；第 1、3、5… 位是值，可为任意六类 payload。
- 0 个实参 → `{}`，合法（空结果契约见 [README](README.md) §4.1）。
- 变长：`params_schema` 为 NULL。按 [03 §6](../dsl/03-semantics.md)，schema 没有固定 arity 或为变长时 **不注入 `$`**；即使声明 `accepts_context: true` 也不会注入，故契约为 `false`，避免脚本误以为可以省略末参。
- 没有“分隔符”“类型标记”等额外参数；不带键的类型推断，`1` 是 number、`"1"` 是 string。
- **注册状态（已落正文）**：`json_build` 属于**可选注册集**，不是 MVP 必备五件套。未注册时脚本调用报加载期 `unknown_tool`（[07 §3.1](../dsl/07-runtime.md)），不产生运行期行为；本目录不把它计入 M2/M10 的必过夹具。已落 07 §1：可选工具，`# allow:` 与参数约束照常适用。

## 2. 输出

- payload：`json_object`。键序 = 书写顺序（不排序）。正文没有规定对象序列化是否排序，本条目取插入序；该点属正文待补项。
- 同名键重复 → 见 §3，不采用“后者覆盖”。
- `truncated=0`；`original_size` = 对象序列化后的 UTF-8 字节数。
- 不截断：序列化超过 `max_output_bytes` → `limit`；结果嵌套深度超过 `max_payload_depth` → `limit`。半截 JSON 不能作为合法 payload。
- 嵌套对象由值位传入另一个 `json_build` 的结果构成；**本期不主张数组构造**（没有 `json_build_array`），需要数组时只能来自工具结果或既有值。

## 3. 失败语义

| 场景 | `error_kind` | handler | `\|?` 捕获 |
| --- | --- | --- | --- |
| 实参个数为奇数（键无值、值无键） | `constraint` | 执行并失败 | 否 |
| 键位不是 `string` | `constraint` | 执行并失败 | 否 |
| 同名键出现两次 | `invalid_input` | 执行并失败 | 是 |
| 结果序列化 > `max_output_bytes` | `limit` | 执行并失败 | 否 |
| 结果嵌套深度 > `max_payload_depth` | `limit` | 执行并失败 | 否 |
| `max_tool_calls`/`timeout_ms` 超限、策略强杀 | `limit`/`revoked` | 边界检查 | 否 |
| 未归类 | `internal` | — | 否 |

- **产生 `constraint`（逐位形状）与 `invalid_input`（内容）**：变长工具没有固定 `m`，加载期不做个数校验；成对性、键为 `string` 属于**值层形状**，按 [04 §2.1](../dsl/04-pipeline-errors.md)“变长工具的 handler 逐位校验”归 `constraint`（不可捕获）；同名键重复属于数据内容问题，归 `invalid_input`（可捕获）。固定 arity 工具的个数不符则在加载期报 `arity`（见 [README](README.md) §2.1），三者的分界是“个数静态 / 值层形状 / 数据内容”。
- 重复键归 `invalid_input` 而非 `dup_key`：`dup_key` 是加载期类别，只用于 emit 字面量与 args JSON（[07 §3.1](../dsl/07-runtime.md)）；运行期枚举里没有它，且这里的重复是 handler 在数据里发现的。
- 嵌套深度不设 `json_build` 专属上限；调用层数由 `max_tool_calls` 与 `timeout_ms` 兜底，**结果深度**按 `max_payload_depth` 校验（07 §2 已定为通用上限，见 [T-004](T-004-tool-json-parse.md) §2），超限 → `limit`。

## 4. 参数约束

| 参数 | 约束类 | 档位 | 本期 |
| --- | --- | --- | --- |
| 全部实参 | 无 schema：成对性与键类型由 handler 逐位校验，归 `constraint`；重复键归 `invalid_input` | 必做（值层） | 声明 |
| 路径 / argv / 域名 / emit 类 | — | 不适用 | 不声明 |
| `args_json` 单次解析、约束与 handler 同源 | 双通道 | 必做（运行时统一） | 由运行时执行 |

`args_json` 里的重复键指**协议层**的 JSON 对象重复键（本工具的实参是数组，正常不会出现）；emit payload 字面量的重复键是加载期 `E_DUP_KEY`，与本工具的“同名业务键”是两件事。

## 5. 验收命令与阈值

- **命令**：`尚未落盘`。
- 计划：无专属里程碑；随 M5 `tools/check.sh m5-into-fn`（调用/嵌套）与 M6 `m6-events`（值序列化）顺带覆盖。
- **阈值**：
  - 4 条合法输入（0 参、2 参、4 参、嵌套）逐字节比对序列化结果，键序与书写序一致；
  - 非法输入分类断言：奇数个、非 `string` 键 → `constraint` 且不可捕获；重复键 → `invalid_input` 且可捕获；
  - 超 `max_output_bytes` 1 例报 `limit`，不可捕获；
  - 结果深度超 `max_payload_depth` 1 例报 `limit`，不可捕获；
  - `$` 注入计数 0：`into` 内 `json_build "a" 1` 的 `args_json` 不得多出 `$`。

## 6. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 工具存在性 | `docs/design/dsl-spec-v0.1.md` L201（“其他场景需要构造 JSON 时，用 `json_build` 工具”） | 历史输入 |
| 无通用对象字面量 | [02 §4](../dsl/02-grammar.md) L110、[dsl/README §4](../dsl/README.md) L64 | 规范正文 |
| 变长不注入 | [03 §6](../dsl/03-semantics.md) L70、[D-007](../../decisions/D-007.md) L58 | 规范 + 决策 |
| 重复键取向 | [D-006](../../decisions/D-006.md) L58、[02 §4](../dsl/02-grammar.md) L108 | 决策 + 规范 |
| 唯一提及事实 | [D-006](../../decisions/D-006.md) L41（全仓一次提及，无接口无 schema） | 决策出证 |
