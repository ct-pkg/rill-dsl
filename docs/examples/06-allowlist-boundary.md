# 样例 06：工具白名单与权限边界（越界调用被拒绝）

> 状态：`unverified`。本样例按 [规范 v0.1 rev.1](../spec/dsl/README.md) 手工推导，仓库没有解释器，**未运行**。
> 依赖工具：[`read`](../spec/tools/T-001-tool-read.md)、[`write`](../spec/tools/T-003-tool-write.md)；权限规则见 [06 安全](../spec/dsl/06-security.md)。

## 1. 场景一句话

脚本只申请 `read`，却试图把读到的内容 `write` 出去；`write` 虽然已在注册表中，但不在 `# allow:` 里，加载期直接拒绝，脚本一行都不执行。

## 2. DSL 源码（故意越界，加载失败）

```rill
# allow: read
# dsl-version: 1

let text = read "notes.txt"

# 反例：write 已注册，但不在 # allow: 中 → 加载期 tool_not_allowed。
write "copy.txt" text
```

期望错误（[07 §4](../spec/dsl/07-runtime.md)）：

```text
src/run.rill:7:1: error: tool 'write' is not allowed by script header.
  Allowed tools: read
  Hint: add 'write' to '# allow:' or use an allowed tool.
```

## 3. 逐步语义

**三层白名单（[06 §1](../spec/dsl/06-security.md)）**

| 层 | 时机 | 本样例 | 失败 |
| --- | --- | --- | --- |
| 第一层：注册表 | 加载 | `read`、`write` 都在内核注册表中 | 名字不在注册表 → `unknown_tool` |
| 第二层：脚本 header | 加载 | `# allow:` 只授权 `{read}` | 已注册但不在 allow → `tool_not_allowed` |
| 第三层：参数 | 每次调用前 | `read "notes.txt"` 的路径值约束 | 值不满足 → `constraint`，handler 不执行 |

- 本样例在**第二层**失败：`write` 在第一层存在，但第二层没有授权。失败发生在加载期，`let text = read "notes.txt"` 也不会执行。
- 如果 `write` 根本未注册，第一层先失败，报 `unknown_tool`，与 allow 是否为空无关。
- 如果 `write` 在 allow 中，但路径越界（例如 `write "../../etc/passwd" ...`），第三层在调用前报 `constraint`，handler 不执行，文件不会创建或截断。
- `# allow:` 缺失或列表为空 → `no_allow_header`；只写 `# deny:` → `deny_without_allow`；`# allow: *` → 继承注册表全集，但必须写审计记录（[D-011](../decisions/D-011.md)）。
- `# deny:` 优先于 `# allow:`；`# deny:` 里的名字即使不在 allow 也合法（冗余无副作用）。
- `# allow:` 中出现**未注册**的名字不报错（[P-023](../spec/PENDING.md)）：白名单只收窄、不校验；未注册名对有效集无贡献，调用时才会按 `unknown_tool` 失败。因此拼写错误不会在 header 处暴露。

**第三个变体：路径越界（运行期 `constraint`）**

```rill
# allow: read
# dsl-version: 1

let secret = read "../../etc/passwd"
```

期望错误：

```text
src/run.rill:4:14: error: tool 'read' rejected path '../../etc/passwd'.
  Constraint: path must resolve under '/workspace/'
  Hint: use a path under '/workspace/'.
```

- 相对路径以 workspace root 为基准解析，`..` 在打开前消解；解析后不在 root 内、或 symlink 指向界外，都报 `constraint`。
- `constraint` **不可捕获**：即使写成 `read "../../etc/passwd" |? read "ok.txt"`，右侧也不会执行；这是安全要求（[04 §2.1](../spec/dsl/04-pipeline-errors.md)）。
- `denied` 也覆盖策略拒绝与 OS 权限拒绝（`EACCES`/`EPERM`），同样不可捕获；`constraint` 与 `denied` 的区别是「参数值不合法」与「调用被拒绝」，但对脚本的可观察后果都是中止。

## 4. 如果由 LLM 生成：prompt 大意

```text
读取 notes.txt，把内容写到 copy.txt。
你只被授权使用 read 工具；不要使用未授权的工具，也不要用 # allow: * 绕过。
脚本开头写 # allow:，只列实际需要且被授权的工具。
如果权限不足，让加载期/调用前的检查失败，不要把越界调用包进 |? 试图兜底。
```

这个 prompt 故意与脚本 header 冲突：模型若真的只被授权 `read`，正确做法是报告「缺少 write 权限」，而不是改写 header 或伪造结果。样例保留这个冲突，用来演示第二层拒绝。

## 5. 这个样例暴露的空白

- **EX-05（高）**：`# allow:` 是脚本作者自声明，默认拒绝只阻止「无意识授权」，不阻止显式申请危险工具；没有外部授权主体（`principal_id`/`grant_set`）来约束自授权，P-020 仍 `undecidable`。
- **EX-05（高）**：`# allow:` 不校验未注册名，拼写错误延迟到调用点；header 看起来成功，实际有效集可能为空。
- **EX-15（中）**：路径约束的 workspace root 由内核配置提供，脚本里看不到；同一个脚本换一个 root 可能从允许变成 `constraint`，不利于可移植性。
