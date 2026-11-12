# T-003 工具 `write`

- **状态**：`unverified`
- **决策**：[D-002](../../decisions/D-002.md)、[D-008](../../decisions/D-008.md)、[D-014](../../decisions/D-014.md)
- **规范**：[03 §6](../dsl/03-semantics.md)、[05 §1](../dsl/05-data-metadata.md)、[06 §5.1](../dsl/06-security.md)、[07 §1](../dsl/07-runtime.md)
- **契约总则**：[README](README.md) §2–§6
- **里程碑**：M5（调用）、M8（路径约束）
- **工具名**：`write`（非关键字）
- **arity**：2 个固定位置参数 `path`、`content`；required：`path`、`content`
- **accepts_context**：否
- **返回值**：`null`
- **截断**：不产生截断；结果携带输入的粘性元数据

## 1. 输入

```
write "report.txt" matches              # write("report.txt", matches)
write "out.txt" $                       # into 内显式写 $
$ |> write "out.txt"                    # 管道形式，等价 write("out.txt", $)
write "issues.txt" (a + b)              # 第二个实参是分组表达式
```

`args_json`：

```
["report.txt", <content 的 payload>]
```

- `path` 必须是 `string`；`content` 可以是任意六类 payload。任一参数缺失（个数 ≠ 2）或 `path` 非 `string` → `constraint`，handler 不执行。
- `content` 为 `string` 时，写入其原始 UTF-8 字节，不额外加引号或换行；为其他五类时，写入该值的 JSON 序列化结果（紧凑、无尾随换行）。因此 `write "x" matches`（`matches` 为数组）写出的字节与其 JSON 文本相同。
- `write` **不声明** `accepts_context`（[08 §2](../dsl/08-examples.md) L31）：`into` 块内 `write "out.txt"` 只有 1 个实参，不注入 → `constraint`；要写 `$` 必须显式写或走管道。
- 没有追加、偏移、权限、编码等可选参数；这些属于内核工具注册的扩展决定，不在本契约。

## 2. 输出

- payload：`null`。写成功不返回写入字节数，也不返回被覆盖文件的旧内容。
- `truncated`：本工具不产生截断。但运行时按 [05 §1.4](../dsl/05-data-metadata.md) 归并粘性：若 `content` 的 payload 来自被截断的 `read`，则 `(write ...).truncated == true`，`original_size` 取该输入的最大值。这是调用方检测“写入了半截内容”的唯一手段。
- 未发生粘性时：`truncated=0`，`original_size` = `"null"` 的序列化字节数 `4`（[05 §1.4](../dsl/05-data-metadata.md) 第三条分支）。
- 覆盖语义：目标存在则截断重写，不存在则创建；写入的就是 `content` 的 payload，不是原始文件内容。
- 输入上限：**本条目主张** `content` 序列化后的 UTF-8 字节数不得超过 `ExecLimits.max_input_bytes`（新增字段，默认 `262144`，与 `max_output_bytes` 同口径）。超限 → `limit`，不可捕获，handler 未执行，目标文件不被创建或截断。需正文跟进 07 §2 增加该字段、默认值表与“输入”计数口径。

## 3. 失败语义

| 场景 | `error_kind` | handler | `\|?` 捕获 |
| --- | --- | --- | --- |
| 路径解析后不在 root 界内、指向界外的 symlink、basename 是 symlink | `constraint` | 未执行 | 否 |
| 实参个数 ≠ 2，或 `path` 非 `string` | `constraint` | 未执行 | 否 |
| `content` 序列化 > `max_input_bytes` | `limit` | 未执行 | 否 |
| 父目录不存在（`ENOENT`/`ENOTDIR`） | `not_found` | 执行并失败 | 是 |
| 目标是目录（`EISDIR`） | `invalid_input` | 执行并失败 | 是 |
| 操作系统拒绝访问（`EACCES`/`EPERM`）、空间耗尽（`ENOSPC`） | `denied` | 执行并失败 | 否 |
| 可重试 I/O（`EIO`/`EBUSY`） | `transient` | 执行并失败 | 是 |
| `max_tool_calls`/`timeout_ms` 超限、策略强杀 | `limit`/`revoked` | 边界检查 | 否 |
| 未归类 | `internal` | — | 否 |

- `ENOSPC` 归 `denied` 而不是 `transient`：重试不会成功，且静默降级会掩盖磁盘故障。
- 本工具**不承诺原子写**（无临时文件 + rename）。`transient` 失败时目标可能已被截断或留下部分内容。原子性属于实现增强，不在本期契约主张。
- 失败前已发生的截断不可回滚，与 [04 §3](../dsl/04-pipeline-errors.md)“副作用不回滚”一致。

## 4. 参数约束

| 参数 | 约束类 | 档位 | 本期 |
| --- | --- | --- | --- |
| `path` | `CONSTRAINT_PATH_PREFIX`：canonical 绝对路径、等于 root 或 `root + "/"` 前缀；写不存在文件时解析父目录 realpath，basename 不是 symlink；判定与打开同源 | 必做（D-014 §5.1） | 声明 |
| `path` | `CONSTRAINT_DENY_PATTERN`（如 `*.key`） | 本期不主张 | 不声明 |
| `content` | 类型不设约束：六类 payload 都可写 | — | 不声明 |
| `content` 序列化字节数 | `max_input_bytes`（新增 `ExecLimits` 字段，默认 `262144`） | 必做（本条目主张） | 声明 |

`write` 是路径约束的第二个宿主，夹具与 [S-017](../S-017-path-constraint.md) 共享六例；其中 `/workspace/new.txt` 一例专门覆盖“写不存在文件时解析父目录”的分支。

## 5. 验收命令与阈值

- **命令**：`尚未落盘`。
- 计划：M8 `tools/check.sh m8-constraints` 跑路径六例；M6 `m6-events` 跑粘性；M3 `m3-control` 跑 arity。
- **阈值**：
  - 路径 6/6；写不存在的 `/workspace/new.txt` 必须允许，父目录是 symlink 指向界外必须拒绝；
  - 字符串与非字符串内容各 1 例，落盘字节逐字节比对；
  - 粘性 1 例：`read` 截断 → `write` → `(write ...).truncated == true`；
  - `into` 内 `write "out.txt"`（不写 `$`）必须报 `constraint` 且 handler 未执行；
  - `content` 超 `max_input_bytes` 1 例：报 `limit`、不可捕获、handler 未执行，且目标文件保持原样（不得先截断再失败）。

## 6. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 调用形态 | [08 §1](../dsl/08-examples.md) L13、L27、L49、L83 | 规范示例 |
| 不声明 context | [08 §2](../dsl/08-examples.md) L31 | 规范示例说明 |
| 管道追加 | `docs/design/dsl-spec-v0.1.md` L117-L121 | 历史输入 |
| 路径规则 | [06 §5.1](../dsl/06-security.md) L81-L91、[D-014](../../decisions/D-014.md) L50 | 规范 + 决策 |
| 侧车与粘性 | [05 §1.1–1.4](../dsl/05-data-metadata.md) L9-L51 | 规范正文 |
| `params_schema`/`accepts_context` | [07 §1](../dsl/07-runtime.md) L15-L23 | 规范正文 |
| 输入上限（本条目主张） | [07 §2](../dsl/07-runtime.md) 的 `ExecLimits` 无输入字段 | 规范缺口 |
