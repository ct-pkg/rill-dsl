# T-004 工具 `json_parse`

- **状态**：`unverified`
- **决策**：[D-002](../../decisions/D-002.md)、[D-008](../../decisions/D-008.md)、[D-014](../../decisions/D-014.md)
- **规范**：[03 §1/§6](../dsl/03-semantics.md)、[05 §1](../dsl/05-data-metadata.md)、[07 §2](../dsl/07-runtime.md)
- **契约总则**：[README](README.md) §2–§6
- **里程碑**：M5（调用）、M6（截断交互）
- **工具名**：`json_parse`（非关键字）
- **arity**：1 个固定位置参数 `text`；required：`text`
- **accepts_context**：否
- **返回值**：六类值之一（`null`/`bool`/`number`/`string`/`json_object`/`json_array`）
- **截断**：不截断

## 1. 输入

```
read "config.json" |> json_parse        # json_parse(text)
json_parse text
```

`args_json`：

```
["{ \"server\": { \"port\": 8080 } }"]
```

- `text` 必须是 `string`；个数 ≠ 1 或类型不符 → `constraint`，handler 不执行。
- 输入是整个 JSON 文本，不是文件路径；读文件由 `read` 承担。这也让 `read |> json_parse` 成为唯一正确组合。
- 不接受 `$` 注入。`into` 内 `json_parse` 裸名是零参调用 → `constraint`；`into` 内 `$ |> json_parse` = 1 个管道值 → 正常。
- 只接受标准 JSON：不接受注释、尾随逗号、单引号字符串、`NaN`/`Infinity`、前导零。

## 2. 输出

- payload：解析后的六类值之一。JSON 字面量 `null` 解析为 `null` 值，属于**成功**，不是失败（[04 §2.1](../dsl/04-pipeline-errors.md) 末条）。
- 数字按 [03 §1](../dsl/03-semantics.md) 转 `number`（IEEE-754 双精度；±2^53 内整数保持整数格式化）。
- 对象键序保留输入顺序；重复键见 §3。
- `truncated=0`；`original_size` = 返回值重新序列化后的 UTF-8 字节数。
- 不截断：结果序列化超过 `max_output_bytes` → `limit`；输入文本嵌套深度或结果深度超过 `max_payload_depth` → `limit`。半截 JSON 不能作为合法 payload，因此本工具不允许用截断代替上限。
  - **本条目主张**：`max_payload_depth` 的语义从“emit payload 上限”扩为“任何进入或离开运行时的 JSON payload 深度上限”，由 `json_parse`、`json_build` 与 emit 共用，不新造 `max_parse_depth`。深度按对象/数组嵌套层数计，字符串内的括号不计。需正文跟进 07 §2 的字段注释与 05 §2.2 的适用范围。

## 3. 失败语义

| 场景 | `error_kind` | handler | `\|?` 捕获 |
| --- | --- | --- | --- |
| 实参个数 ≠ 1，或 `text` 非 `string` | `constraint` | 未执行 | 否 |
| 任一实参 payload 的 `truncated=true`（上游截断） | `limit` | 未执行 | 否 |
| JSON 语法错误、尾随垃圾、非法转义、非法数字 | `invalid_input` | 执行并失败 | 是 |
| 同一对象内重复键 | `invalid_input` | 执行并失败 | 是 |
| 结果序列化 > `max_output_bytes`，或深度 > `max_payload_depth` | `limit` | 执行并失败 | 否 |
| `max_tool_calls`/`timeout_ms` 超限、策略强杀 | `limit`/`revoked` | 边界检查 | 否 |
| 未归类 | `internal` | — | 否 |

- 重复键不采用“后者覆盖”：这与 emit 字面量的加载期 `E_DUP_KEY`（[02 §4](../dsl/02-grammar.md) L108）和 args JSON 的重复键规则（[06 §5.4](../dsl/06-security.md)）保持同一取向——同一份文本不允许两个值。运行期没有 `dup_key` 类别，故归 `invalid_input`。
- 不产生 `not_found`/`transient`/`denied`：无文件、无网络、无权限面。

### 上游截断的归一（本条目主张）

`read` 被截断时，`json_parse` 只收到截断后的 `payload`，看不到 `meta`（[05 §1.2](../dsl/05-data-metadata.md)），handler 无法自行判断。本条目把归一责任交给运行时：

- `json_parse` 声明 `requires_complete_input=true`（`ToolDef` 新字段或等价注册属性）。
- 运行时在参数约束通过后、handler 之前检查任一实参 payload 的 `truncated`；为真 → `limit`，不可捕获，handler 未执行，错误位置指向调用点，详情行为 `Constraint: input was truncated upstream`。
- 不得降为 `invalid_input`：截断是资源上限的结果，不是数据非法；降级会让 `|?` 静默接管，重新制造 D-008 要消除的假阴性。
- 需要“截断也能继续”的脚本先显式判断 `(read p).truncated` 再决定下一步；`json_parse` 本身不提供部分解析。

**需正文/接口跟进**：07 §1 的 `ToolDef` 增加该字段；07 §3.2 或 04 §2.1 明确 `limit` 也用于“输入被上游截断”。

## 4. 参数约束

| 参数 | 约束类 | 档位 | 本期 |
| --- | --- | --- | --- |
| `text` | 固定 arity + `string` 类型浅校验 | 必做（[03 §6](../dsl/03-semantics.md)） | 声明 |
| `text` 长度上限 | 无对应约束类；结果侧由 `max_output_bytes` 兜底 | 本期不主张 | 不声明 |
| 上游截断（调用前置条件，非 `ParamConstraint`） | `requires_complete_input` | 必做（本条目主张） | 声明 |
| 路径 / argv / 域名 / emit 类 | — | 不适用 | 不声明 |

## 5. 验收命令与阈值

- **命令**：`尚未落盘`。
- 计划：M5 `tools/check.sh m5-into-fn` 跑调用形态；M6 `m6-events` 跑与截断的交互。
- **阈值**：
  - 六类顶层值各 1 例（含字面量 `null` 必须 `ok=1`、值为 `null`）；
  - 4 条非法输入（语法错、尾随垃圾、重复键、非法数字）均报 `invalid_input` 且可被 `|?` 捕获；
  - 超过 `max_output_bytes` 与超过 `max_payload_depth` 各 1 例报 `limit`，不可捕获；深度超限必须 handler 未执行（不是解析到一半才失败）；
  - 截断输入 1 例：`read` 截断 → `json_parse`，断言 `ok=0`、`error_kind=limit`、不可捕获、handler 未执行；与“普通非法 JSON → `invalid_input`、可捕获”对照，二者不得互换。

## 6. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 调用形态 | [08 §2](../dsl/08-examples.md) L24-L28、[08 §5](../dsl/08-examples.md) L78-L84 | 规范示例 |
| 值模型与数字 | [03 §1](../dsl/03-semantics.md) L7-L12 | 规范正文 |
| 工具边界只拿 payload | [05 §1.2](../dsl/05-data-metadata.md) L21-L25 | 规范正文 |
| 可捕获集 | [04 §2.1](../dsl/04-pipeline-errors.md) L41-L52 | 规范正文 |
| 重复键取向 | [02 §4](../dsl/02-grammar.md) L108、[06 §5.4](../dsl/06-security.md) | 规范正文 |
| 解析工具存在性 | `docs/design/dsl-spec-v0.1.md` L129、L415 | 历史输入 |
| 截断归一（本条目主张） | 07 §1 `ToolDef` 无 `requires_complete_input` 字段 | 规范缺口 |
