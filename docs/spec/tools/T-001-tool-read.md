# T-001 工具 `read`

- **状态**：`unverified`
- **决策**：[D-002](../../decisions/D-002.md)、[D-008](../../decisions/D-008.md)、[D-014](../../decisions/D-014.md)
- **规范**：[03 §6](../dsl/03-semantics.md)、[05 §1](../dsl/05-data-metadata.md)、[06 §5.1](../dsl/06-security.md)、[07 §1](../dsl/07-runtime.md)
- **契约总则**：[README](README.md) §2–§6
- **里程碑**：M5（调用）、M6（截断）、M8（路径约束）
- **工具名**：`read`（非关键字）
- **arity**：1 个固定位置参数 `path`；required：`path`
- **accepts_context**：否
- **返回值**：`string`
- **截断**：可截断

## 1. 输入

```
read "src/main.c"
read path
```

`args_json` 为 JSON 数组，元素按书写顺序：

```
["src/main.c"]
```

- `path` 必须是 `string`，否则 `constraint`，handler 不执行。
- 相对路径以 **workspace root** 为基准解析，不以进程 cwd 为基准；`..` 在解析时消解（[06 §5.1](../dsl/06-security.md) 只规定判定对象是解析后的绝对路径，未规定相对路径基准，本条目取 root）。
- 不接受 `$` 注入：`into` 块内调用 `read` 不会补参数。管道值只追加不替换，因此 `x |> read "p"` = `read("p", x)`，两个实参 → `constraint`。
- 裸名 `read` 是零参调用（[03 §2](../dsl/03-semantics.md)），`[]` ≠ 1 → `constraint`。

## 2. 输出

- payload：文件内容的 UTF-8 解码结果，`string`。空文件返回 `""`，不是 `null`。
- 不截断时：`truncated=0`，`original_size` 按 [05 §1.4](../dsl/05-data-metadata.md) 第三分支取“本值序列化字节数”（`string` 含引号与转义），**不等于**文件字节数。
- 文件字节数 > `ExecLimits.max_output_bytes`（默认 `262144`，[07 §2](../dsl/07-runtime.md)）时：
  - 返回文件前缀，字节数 ≤ `max_output_bytes`，且切点落在 UTF-8 序列边界，绝不切断多字节字符；
  - `truncated=1`；`original_size` = **切前**文件字节数（原始字节，不含序列化的引号）；
  - payload 内不加省略号、不加任何标记；截断事实只在侧车。
- 两条分支的 `original_size` 口径不同（截断取原始字节、未截断取序列化字节），这是 [05 §1.4](../dsl/05-data-metadata.md) 的原文；调用方不能用它反推文件大小，只能用截断分支的值判断“丢了多少”。
- 粘性由运行时归并（[05 §1.4](../dsl/05-data-metadata.md)）：本工具是截断源，不是消费侧。

## 3. 失败语义

| 场景 | `error_kind` | handler | `\|?` 捕获 |
| --- | --- | --- | --- |
| 路径解析后不在 root 界内、指向界外的 symlink、`/workspace-evil/x` | `constraint` | 未执行 | 否 |
| 实参个数 ≠ 1，或 `path` 非 `string` | `constraint` | 未执行 | 否 |
| 文件或父目录不存在（`ENOENT`/`ENOTDIR`） | `not_found` | 执行并失败 | 是 |
| 操作系统拒绝访问（`EACCES`/`EPERM`） | `denied` | 执行并失败 | 否 |
| 可重试 I/O（`EIO`/`EBUSY`/`EAGAIN`） | `transient` | 执行并失败 | 是 |
| 目标是目录（`EISDIR`）、或字节不是合法 UTF-8 | `invalid_input` | 执行并失败 | 是 |
| `max_tool_calls`/`timeout_ms` 超限、策略强杀 | `limit`/`revoked` | 边界检查 | 否 |
| 未归类 | `internal` | — | 否 |

- 单次结果过大**不产生** `limit`：`read` 的应答是截断 + 侧车，不是错误。
- `denied` 的 OS 来源与策略来源共用类别，靠详情行区分；归属表见 [README](README.md) §5。
- 失败时 `value_json=NULL`；`truncated`/`original_size` 无意义，运行时不得把它们并入后续粘性计算。

## 4. 参数约束

| 参数 | 约束类 | 档位 | 本期 |
| --- | --- | --- | --- |
| `path` | `CONSTRAINT_PATH_PREFIX`：canonical 绝对路径、等于 root 或 `root + "/"` 前缀、`..` 已消解、打开同源 | 必做（D-014 §5.1） | 声明 |
| `path` | `CONSTRAINT_DENY_PATTERN`（如 `*.key`） | 本期不主张（D-014 必做清单未列） | 不声明 |
| `path` | argv / 域名 / emit 类 | 不适用 | 不声明 |

- 夹具沿用 [S-017](../S-017-path-constraint.md) 六例：`/workspace/a.txt` 允、`/workspace/../../etc/passwd` 拒、symlink→`/etc` 拒、symlink→`/workspace/sub` 允、`/workspace-evil/x` 拒、`/workspace/new.txt` 允。最后一条对 `read` 只证明**约束放行**；文件不存在时 handler 随后报 `not_found`，两者不矛盾。
- `args_json` 只解析一次；重复键 `E_DUP_KEY` 由运行时统一执行（[06 §5.4](../dsl/06-security.md)）。

## 5. 验收命令与阈值

- **命令**：`尚未落盘`。
- 计划：M8 `tools/check.sh m8-constraints` 跑路径六例；M6 `m6-events` 跑截断；M3 `m3-control` 跑 arity。
- **阈值**：
  - 路径 6/6 与 [S-017](../S-017-path-constraint.md) 一致，handler 未执行 3/3；
  - 截断 2 例（大文件、切点落在 3 字节字符中间）均不得产生非法 UTF-8，截断分支的 `original_size` 等于 `stat` 字节数；未截断分支的 `original_size` 等于返回串的序列化字节数；
  - `x |> read "p"`、裸 `read`、`read 1` 三条负例均报 `constraint` 且 handler 未执行；
  - 0 次泄漏 `meta` 到 `args_json`。

## 6. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 调用形态 | [08 §1](../dsl/08-examples.md) L10、L39、L65 | 规范示例 |
| 工具边界与侧车 | [05 §1.1–1.2](../dsl/05-data-metadata.md) L9-L25 | 规范正文 |
| 截断与粘性 | [05 §1.4](../dsl/05-data-metadata.md) L40-L51、[D-008](../../decisions/D-008.md) L48-L56 | 规范 + 决策 |
| 路径约束 | [06 §5.1](../dsl/06-security.md) L81-L91 | 规范正文 |
| `ToolDef` 字段 | [07 §1](../dsl/07-runtime.md) L15-L23 | 规范正文 |
| 可捕获集 | [04 §2.1](../dsl/04-pipeline-errors.md) L41-L52 | 规范正文 |
