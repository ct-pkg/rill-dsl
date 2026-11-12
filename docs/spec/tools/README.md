# 工具契约目录

> **状态**：`unverified`。本目录收录的 6 个工具**均无 handler、无 `ToolRegistry` 注册、无夹具**；所有验收命令一律写 `尚未落盘`。
> **规范正文**：[../dsl/README.md](../dsl/README.md)（`v0.1 rev.1`）。
> **决策锚点**：[D-002](../../decisions/D-002.md)、[D-007](../../decisions/D-007.md)、[D-008](../../decisions/D-008.md)、[D-014](../../decisions/D-014.md)。
> **编号**：`T-001..T-006`，工具契约独立命名空间（`T` = tool），不复用 `S-*` 规格条目号；状态格式沿用规格层。

本目录只回答“这些工具被调用时，输入是什么、输出是什么、失败归哪一类”。不定义 handler 实现、不定义注册表代码、不新增 DSL 语法。

## 1. 收录范围

| 工具 | 条目 | 正文引用 | 状态 |
| --- | --- | --- | --- |
| `read` | [T-001](T-001-tool-read.md) | [08 §1/§3/§4](../dsl/08-examples.md)、[07 §4](../dsl/07-runtime.md)、[S-017](../S-017-path-constraint.md) | `unverified` |
| `grep` | [T-002](T-002-tool-grep.md) | [08 §1/§3/§4](../dsl/08-examples.md)、[07 §4](../dsl/07-runtime.md) | `unverified` |
| `write` | [T-003](T-003-tool-write.md) | [08 §1/§2/§3/§5](../dsl/08-examples.md)、[07 §4](../dsl/07-runtime.md) | `unverified` |
| `json_parse` | [T-004](T-004-tool-json-parse.md) | [08 §2/§5](../dsl/08-examples.md)、[07 §4](../dsl/07-runtime.md) | `unverified` |
| `get` | [T-005](T-005-tool-get.md) | [05 §1.3](../dsl/05-data-metadata.md)、[D-008](../../decisions/D-008.md) | `unverified` |
| `json_build` | [T-006](T-006-tool-json-build.md) | `v0.1` §4 注（历史输入）、[D-006](../../decisions/D-006.md) 出证 | `unverified` |

`read`/`grep`/`write`/`json_parse`/`get` 五个出现在 [07 §4](../dsl/07-runtime.md) 的错误示例 `Available:` 行，是正文唯一一次成组列出的工具名；该行是示例，不是注册表定义，实际可见集合仍由内核 `ToolRegistry` 决定。`json_build` 只在 `docs/design/dsl-spec-v0.1.md` 出现，rev.1 正文未直接引用；收录理由：emit payload 之外没有通用对象字面量（[dsl/README §4](../dsl/README.md)），若内核不提供该工具，构造 JSON 就没有任何手段。

**不收录**：

| 名字 | 出现位置 | 不收录理由 |
| --- | --- | --- |
| `exec`、`http_post` | [06 §5.2](../dsl/06-security.md)、[S-013](../S-013-default-deny.md)、`v0.1` L222 | 作为“未注册/被 deny”的反例名出现，不是本期工具；M8 的 argv/域名约束没有宿主工具。 |
| `delete_tool` | `v0.1` §5.1 代码注释 | 注册表 API 的注释，不是工具名。 |
| `emit` | [05 §2](../dsl/05-data-metadata.md) | 语言语句，不是工具调用，不经过 `ToolDef` 与三层白名单（[05 §2.1](../dsl/05-data-metadata.md)）。 |

## 2. 契约字段

| 字段 | 本目录写法 | 依据 |
| --- | --- | --- |
| 名字 | 必须是 `IDENT` 且不是关键字（[01 §3](../dsl/01-lexical.md)） | 注册名即调用名 |
| 位置参数（arity） | 固定个数 `m`，按书写顺序编号；`params_schema` 非 NULL | [07 §1](../dsl/07-runtime.md) |
| required | 固定 arity 下**所有**位置参数都是 required | 见下 |
| `accepts_context` | 是否允许 `$` 作为隐式末参注入 | [03 §6](../dsl/03-semantics.md)、[D-007](../../decisions/D-007.md) |
| 返回值 | 六类 payload 之一；不返回 `meta` | [05 §1.1](../dsl/05-data-metadata.md) |
| 截断 | 是否产生 `truncated`/`original_size` | [D-008](../../decisions/D-008.md) |
| 错误 | 只列该工具可能产生的 `error_kind` | §5 |
| 约束 | 第三层 `ParamConstraint` 的类别与档位 | §6、[D-014](../../decisions/D-014.md) |

**required 的机械含义**：本规范没有可选参数、默认值、命名参数。一个参数“可以省略”只有两种来源——`|>` 追加或 `$` 注入；两者都只是把值补到末尾，不是默认值。补完之后个数仍不等于 `m` → 加载期 `arity`，脚本不执行到该调用。因此每个固定 arity 工具的所有参数都标 required。

**变长工具的例外**：`json_build` 的 `params_schema` 为 NULL（变长）。变长工具既没有固定 `m`，也不参与 `$` 注入（[03 §6](../dsl/03-semantics.md)）；它的逐位校验由 handler 承担，错误类别因此与固定 arity 工具不同（见 [T-006](T-006-tool-json-build.md)）。

### 2.1 arity 是加载期判定（已落正文）

- **记在哪**：`ToolDef.params_schema`。固定 arity 时，位置参数个数就是 `m`；`params_schema=NULL` 表示变长，不做固定个数校验，但工具可以另有静态形状规则（`json_build` 的键值成对/偶数），加载期同样按 `arity` 报错（[T-006](T-006-tool-json-build.md)）。
- **由谁校验**：加载器。每个调用点的 `n = 显式实参数 + 管道值数 + (在 into 内 && accepts_context && n<m ? 1 : 0)` 只由词法结构决定；`n ≠ m` → 加载期 `arity`（[07 §3.1](../dsl/07-runtime.md)），脚本不执行到该调用。
- **不属于三层**：`arity` 是静态属性，不是第三层 `constraint`；第三层只处理值（路径/命令/域名/大小/类型）。该改判已由 [03 §5/§6](../dsl/03-semantics.md)、[04 §1/§2.1](../dsl/04-pipeline-errors.md)、[06 §1](../dsl/06-security.md)、[07 §3.1](../dsl/07-runtime.md) 落定。
- **运行期 `constraint` 的职责**：仅值层——`ParamConstraint`、schema 浅校验；变长工具的键类型与重复键归 handler 的 `invalid_input`，不算 `constraint`。

## 3. 实参顺序与注入

最终实参的组装顺序由 [03 §6](../dsl/03-semantics.md) 与 [D-007](../../decisions/D-007.md) 固定，本目录不另立规则：

```
最终实参 = 显式实参（书写序） ++ 管道值（若有） ++ 隐式 $（若注入）
```

注入三条件同时成立才发生：① 位于 `into` 块内；② 工具声明 `accepts_context`；③ `n < m`（`n` = 显式实参数 + 管道值个数，`m` = 固定位置形参数）。`|?` 两侧各自独立计算。

| 调用 | 显式 | 管道 | 注入 | 最终 args | 结果 |
| --- | --- | --- | --- | --- | --- |
| `get "k"`（`into` 内） | 1 | 0 | 是（1<2） | `["k", $]` | 正常 |
| `get "k" $` | 2 | 0 | 否（2=m） | `["k", $]` | 正常 |
| `$ \|> get "k"` | 1 | 1 | 否（2=m） | `["k", $]` | 正常 |
| `get "k"`（`into` 外） | 1 | 0 | 否（无 `$`） | `["k"]` | `arity`（加载期） |
| `read`（裸名，零参调用） | 0 | 0 | 否 | `[]` | `arity`（加载期） |
| `x \|> read "p"` | 1 | 1 | 否 | `["p", x]` | `arity`（加载期，2≠1） |
| `content \|> grep "m"` | 1 | 1 | 否 | `["m", content]` | 正常 |
| `read p \|> json_parse` | 0 | 1 | 否 | `[text]` | 正常 |
| `$ \|> write "out"` | 1 | 1 | 否 | `["out", $]` | 正常 |
| `json_build "a" 1` | 2 | 0 | 否（变长不注入） | `["a", 1]` | 正常 |

只有 `get` 声明 `accepts_context: true`。`read`/`grep`/`write`/`json_parse` 声明 false；`json_build` 是变长，按规则即使声明 true 也不会注入，故声明 false 以免误导。表中标 `arity` 的三行都是**加载期**错误，脚本不会运行到该调用。

## 4. 截断语义（D-008）

- 截断**只由工具产生**，DSL 没有 `limit N` 语法；`read` 与 `grep` 可截断，其余四个不截断。
- handler 与工具参数只看到 `payload`，收不到带 `meta` 的包装值；截断事实通过 `ToolResult` 的 `truncated`/`original_size` 两个标量回传，`meta` 结构由运行时维护（[05 §1.2](../dsl/05-data-metadata.md)、[07 §1](../dsl/07-runtime.md)）。
- 截断结果**不加省略号或任何标记**：payload 是原始内容的前缀，`truncated` 只在侧车里。
- 切点按 UTF-8 字节，且不得把一个多字节序列切成两半；因此实际返回可能略少于 `max_output_bytes`。
- `original_size`：截断分支取**切前**完整结果的字节数，未截断分支取返回值的**序列化**字节数（[05 §1.4](../dsl/05-data-metadata.md)）。对 `string` 结果，前者是原始字节、后者含引号与转义，两者口径不同，不能互相反推。单位与 `ExecLimits.max_output_bytes` 同口径。
- 粘性由运行时归并，不由 handler 负责：`result.truncated = 本次截断 || 任一实参 truncated`；`original_size` 按 [05 §1.4](../dsl/05-data-metadata.md) 三条分支取值。所以 `read` 被截断后 `grep` 再返回空数组，结果仍是 `truncated=true`。
- 不能截断的构造型结果（`json_parse`、`get`、`json_build`）超限时返回 `limit`，不得返回半截 JSON。

### 4.1 空结果契约

“空”必须是合法 payload，`ok=1`；不能用 `null` 表示空集合，也不能用 `[]` 表示缺失。脚本判空按工具选形态：

| 工具 | 空/无结果 | 返回 | 是否错误 |
| --- | --- | --- | --- |
| `read` | 空文件 | `""`（`string`，0 字节） | 否 |
| `grep` | 无匹配、空输入串 | `[]`（`json_array`，0 元素） | 否 |
| `write` | 写入 0 字节 | `null` | 否 |
| `json_parse` | 空文本 `""` | — | **是**：`invalid_input`（不可解析，不是 `null`） |
| `get` | 缺键、`obj` 非对象 | `null` | 否 |
| `json_build` | 0 个实参 | `{}` | 否 |

`[]` 与 `null` 不等价（[03 §8](../dsl/03-semantics.md)）；`grep` 的空匹配固定是 `[]`，脚本应写 `matches.length > 0`，不能写 `matches != null`。

## 5. `error_kind` 归属表

这张表解决“工具错误归一到哪个 `error_kind`、由谁判定”的未定问题。`error_kind` 枚举以 [07 §3.2](../dsl/07-runtime.md) 为准；可捕获性以 [04 §2.1](../dsl/04-pipeline-errors.md) 为准，工具无权改动。

| `error_kind` | 归属 | 判定点 | `\|?` 捕获 | 本目录工具 |
| --- | --- | --- | --- | --- |
| `not_found` | handler | 目标不存在（文件、父目录） | 是 | `read`、`write` |
| `invalid_input` | handler | 拿到的数据本身不合法（编码、正则、JSON、键值对） | 是 | `read`、`grep`、`write`、`json_parse`、`json_build` |
| `transient` | handler | 可重试的 I/O 失败（含磁盘/配额耗尽 `ENOSPC`/`EDQUOT`） | 是 | `read`、`write` |
| `denied` | runtime（策略层）+ handler（仅 OS 权限 `EACCES`/`EPERM`） | 调用被拒绝执行 | 否 | `read`、`write`（仅 OS 侧） |
| `constraint` | runtime（第三层） | 参数值不符合值层声明（路径、标量类型、大小） | 否 | 全部固定 arity 工具 |
| `arity`（加载期） | loader | 实际实参个数（显式 + 管道 + `$`）≠ 固定形参数，或 `json_build` 的个数为奇数 | 否 | 全部固定 arity 工具；`json_build`（奇数个） |
| `dup_key_json`（运行期） | runtime | `args_json`/`ctx_json` 协议级重复键，解析即失败、handler 之前 | 否 | 不涉及（工具只收已解析参数） |
| `limit` | runtime（ExecLimits）+ handler（构造型不可截断） | 资源上限 | 否 | `json_parse`、`get`、`json_build` 的结果上限；`write` 的每次调用输入总量上限；全部工具的 `ExecLimits` |
| `internal` | runtime / handler | 未归类失败、未知 `error_kind` | 否 | 全部 |
| `type` | runtime（DSL 运算） | 运算/比较的类型不符 | 否 | 工具不得产生 |
| `for_not_array` | runtime | `for` 集合不是数组 | 否 | 工具不得产生 |
| `condition_not_bool` | runtime | 条件不是 `bool` | 否 | 工具不得产生 |
| `emit_schema` | runtime（emit） | 事件 payload 不符合 schema | 否 | 工具不涉及 |
| `approval_required` / `approval_denied` / `approval_stale` / `approval_reused` | runtime | 审批 | 否 | 工具只声明 `requires_approval`，不产生这些 kind |
| `revoked` | runtime | 策略快照在调用边界强杀 | 否 | 同上 |
| `unconstrained_arg` | runtime | 隐式 `$` 在 schema 中没有具名参数槽 | 否 | `get` 的 `$` 绑定到 `obj`，不触发 |
| 加载期全部 kind（[07 §3.1](../dsl/07-runtime.md)） | loader | 加载 | 否 | 不进入工具边界 |

规则：

1. **单一归属**：handler 只允许返回上表“归属”含 handler 的行；返回其他 kind 一律由运行时归一为 `internal`。
2. **未知字符串**：handler 返回枚举外的字符串 → `internal`，且不可捕获（沿用 [S-008 §3](../S-008-capturable-errors.md)）。
3. **`constraint` 与 `invalid_input` 的机械判据**：值层的约束失败（运行时 `ParamConstraint`、schema 浅校验）→ `constraint`；失败来自数据内容或运行期值（编码、JSON 语法、正则、键不是 `string`、业务 JSON 文本重复键）→ `invalid_input`。前者说明脚本传的参数值不对，不应被 `|?` 静默兜底；后者说明输入数据有问题，允许兜底。个数不符（含 `json_build` 的奇数个）不在两类中——加载期已报 `arity`；协议级重复键由 `dup_key_json` 单独承担。
4. **不得为可降级改类**：工具不能把 `denied`/`limit` 改写成可捕获类别来绕过 [04 §2.1](../dsl/04-pipeline-errors.md)。
5. **空结果不是错误**：缺键、空匹配、空文件都返回合法 payload，不产生任何 `error_kind`；空集合用 `[]`、缺失用 `null`，见 §4.1。
6. **一次调用一个类别**：失败只归一到一个 kind，不聚合、不带错误值回脚本。

### 5.1 失败现象 → `error_kind` 速查

| 失败现象 | `error_kind` | 判定者 |
| --- | --- | --- |
| 路径不在 root 内、symlink 越界、固定参数的标量类型不符 | `constraint` | runtime |
| 实际实参个数（含管道与 `$`）≠ 固定 arity，或 `json_build` 个数为奇数 | `arity`（加载期） | loader |
| 文件或父目录不存在 | `not_found` | handler |
| OS 拒绝（`EACCES`/`EPERM`） | `denied` | handler |
| 磁盘/配额耗尽（`ENOSPC`/`EDQUOT`） | `transient` | handler |
| 可重试 I/O（`EIO`/`EBUSY`/`EAGAIN`） | `transient` | handler |
| 参数协议（`args_json`/`ctx_json`）重复键 | `dup_key_json`（运行期） | runtime |
| 目标是目录、字节非 UTF-8、正则非法、JSON 非法、键不是 `string`、业务 JSON 文本重复键 | `invalid_input` | handler |
| 构造型结果超 `max_output_bytes`；`write` 的本次调用输入总量超 `max_input_bytes`；`ExecLimits` 任一超限 | `limit` | handler / runtime |
| handler 返回枚举外的字符串 | `internal` | runtime 归一 |

同一次失败只命中一行；若现象同时符合多行，按“判定者更早”的一行归一（runtime 先于 handler）。

`denied` 的双来源（策略层 / OS 权限）是已知的归类重叠：策略侧由运行时在 handler 之前判定，OS 侧由 handler 判定，两者共用同一 kind 与不可捕获性，靠错误详情行区分来源。是否拆分类别属于正文改动，本目录不主张。

## 6. 参数约束分档（D-014）

| 工具.参数 | 约束类 | 档位 | 本目录声明 |
| --- | --- | --- | --- |
| `read.path` | `CONSTRAINT_PATH_PREFIX` + canonical + 组件边界 + 打开同源 | 必做 | 声明 |
| `write.path` | 同上，另加父目录 realpath、basename 非 symlink | 必做 | 声明 |
| 固定 arity 工具与 `json_build` 的 arity | 加载期 `arity`，不属于第三层（§2.1） | 必做 | 声明 |
| 固定 arity 工具的标量类型 | 运行期 schema 浅校验（`string`） | 必做 | 声明 |
| `args_json` 单次解析、协议重复键 `dup_key_json`、约束与 handler 同源 | 双通道 | 必做 | 运行时统一执行 |
| 隐式 `$` 具名并进入同一套 schema | 双通道 | 必做 | `get.obj` |
| `read.path` 的 `DENY_PATTERN`（如 `*.key`） | 正则黑名单 | 本期不主张 | 不声明 |
| `grep.pattern` 长度/复杂度上限（ReDoS） | 正则黑名单类 | 本期不主张 | 不声明；风险另记 |
| `argv[0]` 绝对路径、`CONSTRAINT_ARGV_PREFIX` | 命令 | 本目录无 exec 工具 | 不适用 |
| 域名白名单、逐跳重定向、DNS 钉住 | 域名 | 本目录无网络工具 | 不适用 |
| `max_emit_bytes` / `max_payload_depth` / `external_egress` | emit | emit 不是工具 | 不适用 |

关于 `unconstrained_arg`：该错误只表示“隐式 `$` 在 schema 里找不到具名参数槽”，不表示“该参数没有第三层约束”。`get.obj` 在 schema 中具名、参与同一套校验，即使没有路径/域名类约束也不触发 `unconstrained_arg`。这是本目录对 [06 §5.4](../dsl/06-security.md) 的机械解释；若正文另有主张，以正文修订为准。

## 7. 门禁状态

- 命令：`尚未落盘`。仓库没有构建、没有 `tools/check.sh`、没有任何 `.rill` 夹具。
- 计划（M 落地后）：`tools/check.sh m2-load`（加载期 `arity`）、`m3-control`（值层 `constraint`）、`m4-pipeline`（可捕获性）、`m6-events`（截断与粘性）、`m8-constraints`（路径六例）。
- 在命令存在之前，本目录任何条目都不得标 `accepted`；每条目的“验收命令与阈值”一节同样写 `尚未落盘`。

## 8. 本目录已写死的规则与正文缺口

下列规则属于工具契约职责，本目录已给出可执行的判定；右侧是正文落点及其状态，本目录不修改正文。

| # | 已写死的规则 | 写在哪 | 正文落点 |
| --- | --- | --- | --- |
| 1 | 上游截断输入 `json_parse` → `limit`、handler 未执行；不得降为 `invalid_input` | [T-004](T-004-tool-json-parse.md) §3 | 已落 07 §1（`requires_complete_input`）、04 §2.1/07 §3.2（`limit` 覆盖上游截断） |
| 2 | `write` 的每次调用输入总量（`args_json` + `ctx_json`）超 `max_input_bytes`（默认 `262144`）→ `limit`、文件不动；两通道互斥：`args_json` = 显式 + 管道，`ctx_json` = 注入的 `$`（未注入计 0） | [T-003](T-003-tool-write.md) §2–§4 | 已落 07 §2（总量口径） |
| 3 | `max_payload_depth` 扩为“任何 JSON payload 的深度上限”，emit/parse/json_build 共用 | [T-004](T-004-tool-json-parse.md) §2、[T-006](T-006-tool-json-build.md) §2 | 已落 07 §2、05 §2.2 |
| 4 | `json_build` 属可选注册集；未注册调用报加载期 `unknown_tool`，不计入必过夹具 | [T-006](T-006-tool-json-build.md) §1 | 已落 07 §1（可选工具，未注册 `unknown_tool`） |
| 5 | `original_size` 截断分支取原始字节、未截断分支取序列化字节 | 本文件 §4、[T-001](T-001-tool-read.md) §2 | 已落 05 §1.4 |
| 6 | `denied` 仅覆盖策略拒绝与 OS 权限（`EACCES`/`EPERM`）；`ENOSPC`/`EDQUOT` 归可捕获的 `transient` | 本文件 §5、[T-001](T-001-tool-read.md) §3、[T-003](T-003-tool-write.md) §3 | 已落 04 §2.1；本目录已按裁定改齐 |
| 7 | 相对路径以 workspace root 为基准解析 | [T-001](T-001-tool-read.md) §1、[T-003](T-003-tool-write.md) §4 | 已落 06 §5.1 |
| 8 | `get` 只做单键查找，不提供点分路径 | [T-005](T-005-tool-get.md) §1 | 已落 05 §1.3 |
| 9 | `constraint` 只覆盖值层，按“值/内容”分界；个数不符归加载期 `arity` | 本文件 §5 规则 3 | 已落 04 §2.1（值层定义） |
| 10 | 空结果逐个工具写死：`read ""`、`grep []`、`get null`、`json_build {}`、`write null`、`json_parse "" → invalid_input` | 本文件 §4.1 与各条目 | 无需正文改动（05 §1.1/§1.4 已支撑） |
| 11 | arity 是静态属性（记在 `params_schema` 的长度），加载期校验，不属于三层 | 本文件 §2.1 | 已落 49f2e37：07 §3.1、03 §5/§6、04 §1/§2.1、06 §1 同步 |
| 12 | `json_build` 三个负例分层：奇数个 → 加载期 `arity`；键非 `string`、重复键 → handler `invalid_input` | [T-006](T-006-tool-json-build.md) §3–§4 | 已裁定，正文正在同步（03 §6「变长不做个数校验」需让位给偶数成对规则） |

已由正文线修复、不再列为缺口：08 示例的 `matches != null`（改为 `matches.length > 0`）、04/S-007 的 `parse` 占位（改为 `json_parse`）、04 §1 的 `x |> read "p"` 示例（改用 arity=2 的 `grep` 并写明管道不改 arity）。
