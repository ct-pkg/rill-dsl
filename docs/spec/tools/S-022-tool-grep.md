# S-022 工具 `grep`

- **状态**：`unverified`
- **决策**：[D-002](../../decisions/D-002.md)、[D-008](../../decisions/D-008.md)、[D-014](../../decisions/D-014.md)
- **规范**：[03 §6](../dsl/03-semantics.md)、[05 §1](../dsl/05-data-metadata.md)、[07 §1](../dsl/07-runtime.md)
- **契约总则**：[README](README.md) §2–§6
- **里程碑**：M4（管道）、M6（截断）
- **工具名**：`grep`（非关键字）
- **arity**：2 个固定位置参数 `pattern`、`text`；required：`pattern`、`text`
- **accepts_context**：否
- **返回值**：`json_array`（元素为 `string`）
- **截断**：可截断

## 1. 输入

```
content |> grep "malloc"        # grep("malloc", content)
grep "TODO" text
grep "a.*b" content
```

`args_json`：

```
["malloc", "<content>"]
```

- `pattern` 是正则表达式文本，必须 `string`；`text` 必须是 `string`。任一不符 → `constraint`，handler 不执行。
- `grep` 只搜字符串，不读文件；要搜文件先 `read`，再用 `|>` 追加。这与 [dsl/README §4](../dsl/README.md) 的非目标一致：没有正则字面量，模式只能是字符串数据。
- 不接受 `$` 注入。`into` 内 `grep "m"` 只有 1 个实参且不注入 → `constraint`（1≠2）。
- 管道值只追加到末尾：`content |> grep "m"` 的 `pattern` 是 `"m"`、`text` 是 `content`；反过来 `"m" |> grep content` 的 `pattern` 是 `content` 的值，两者不自动换位。

## 2. 输出

- payload：`json_array<string>`，按行匹配。每个元素是**整行原文**，去掉行尾 `\n`（`\r\n` 同时去掉 `\r`），按文件顺序；同一行多次命中只出现一次。
- 无匹配、空输入串 → `[]`（空数组），不是 `null`，不是错误。
- 不截断时：`truncated=0`，`original_size` = 整个数组序列化后的 UTF-8 字节数。
- 超过 `max_output_bytes` 时：
  - 按出现顺序保留条目，直到再加入下一条会超出预算为止，丢弃尾部剩余条目；
  - 若单条本身超预算，则保留该条，并把该字符串按 UTF-8 边界切成前缀；
  - `truncated=1`；`original_size` = **切前**完整数组的序列化字节数；payload 内不加标记。
- 输入的粘性由运行时归并：`read` 截断后再 `grep`，即使 `grep` 自身未截断，结果仍是 `truncated=true`（[05 §1.4](../dsl/05-data-metadata.md)、[S-009](../S-009-truncation.md) 场景 C）。

## 3. 失败语义

| 场景 | `error_kind` | handler | `\|?` 捕获 |
| --- | --- | --- | --- |
| `pattern`/`text` 非 `string`，或实参个数 ≠ 2 | `constraint` | 未执行 | 否 |
| `pattern` 不是合法正则 | `invalid_input` | 执行并失败 | 是 |
| 结果超过 `max_output_bytes` | 不报错，走截断 | 执行 | — |
| `max_tool_calls`/`timeout_ms` 超限、策略强杀 | `limit`/`revoked` | 边界检查 | 否 |
| 未归类 | `internal` | — | 否 |

- `grep` 不产生 `not_found`（没有文件概念）、不产生 `transient`/`denied`（纯计算，无 I/O 权限面）。
- 正则编译失败是**数据**问题，所以归 `invalid_input`（可捕获），不是 `constraint`。判定者不同是这两类的机械分界，见 [README](README.md) §5 规则 3。

## 4. 参数约束

| 参数 | 约束类 | 档位 | 本期 |
| --- | --- | --- | --- |
| `pattern`、`text` | 固定 arity + `string` 类型浅校验 | 必做（[03 §6](../dsl/03-semantics.md)） | 声明 |
| `pattern` 长度/复杂度上限（ReDoS 防护） | 正则黑名单类 | 本期不主张 | 不声明 |
| `text` | 路径 / argv / 域名 / emit 类 | 不适用 | 不声明 |

ReDoS 风险明确记录为“本期不主张”：没有长度上限与超时，恶意模式可能占满 `timeout_ms`；`timeout_ms` 超限仍是 `limit`，不会变成 `invalid_input`。

## 5. 验收命令与阈值

- **命令**：`尚未落盘`。
- 计划：M4 `tools/check.sh m4-pipeline` 跑管道顺序；M6 `m6-events` 跑截断与粘性。
- **阈值**：
  - 4 条输入：有匹配、无匹配、空串、同一行多次命中 → 数组形态与顺序逐条断言；
  - 截断 2 例（多条目超限、单条目超限）均保持合法 JSON 与合法 UTF-8，`original_size` 等于切前序列化字节；
  - 粘性 1 例：上游 `truncated=1` 时 `grep` 结果为 `truncated=true`；
  - 正则非法 1 例报 `invalid_input` 且可被 `|?` 捕获。

## 6. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 管道追加 | [04 §1](../dsl/04-pipeline-errors.md) L8-L14、[08 §1](../dsl/08-examples.md) L11 | 规范正文 + 示例 |
| 空数组 | [S-009](../S-009-truncation.md) L14 | 规格条目 |
| 数组内建字段 | [03 §8](../dsl/03-semantics.md) L83-L85、[08 §4](../dsl/08-examples.md) L67 | 规范正文 |
| 截断与粘性 | [D-008](../../decisions/D-008.md) L48-L56、[05 §1.4](../dsl/05-data-metadata.md) L40-L51 | 决策 + 规范 |
| 正则作为字符串 | `docs/design/dsl-spec-v0.1.md` L434 | 历史输入 |

### 与示例的已知不一致

[08 §1](../dsl/08-examples.md) L12、L41、L66 用 `matches != null` 判断“有没有匹配”。本条目按 [S-009](../S-009-truncation.md) 把无匹配定义为 `[]`，而 `[] != null` 恒为 `true`，条件不起过滤作用。正确写法是 `matches.length > 0`（`length` 见 [03 §8](../dsl/03-semantics.md)）。这是正文示例的问题，本目录不修改正文。
