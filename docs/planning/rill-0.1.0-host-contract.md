# RILL 0.1.0 宿主契约骨架（phase 1）

状态：骨架，只定**形状**与**加载入口**；不定义任何能力语义。
依据：[RILL 0.1.0](../RILL-0.1.0.md) §五、[roadmap](rill-0.1.0-roadmap.md) §3.3、
[阶段计划](rill-0.1.0-phase-plan.md) phase 1。

本文件不是 CR，也不修改 0.1.0 正文。规范里与双宿主冲突的条目（角色/退出码/错误串/二进制值）
继续按 roadmap §3.3.3 登记，phase 1 不擅自裁定。

## 1. 为什么先定形状

Parser 与 Runtime 只允许认 `HostCapabilities` 这一个接口；Shell 与 Agent 各自实现，
差异只出现在能力层。若先把某个宿主的行为写进形状，后面两个宿主就再也拆不开。
因此 phase 1 只冻结：

1. 五个能力槽位的名字；
2. profile 文件的声明形状；
3. 从 profile 到句柄的加载入口；
4. 一条硬规则：parser 不得反向依赖能力层。

## 2. 形状

### 2.1 `HostProfile`

profile 是**外部声明**，脚本无权声明（0.1.0 §五.1）。phase 1 只认四个字段：

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `schema` | string | 固定 `rill.host-profile/0` |
| `name` | string | 非空，且等于文件名（`shell.json` → `shell`） |
| `kind` | string | `shell` / `agent` |
| `capabilities` | object | 必须恰好五个槽位，见 §2.3 |
| `description` | string | 可选，只给人看 |

### 2.2 `CapabilityBinding`

每个槽位只声明“谁来提供、引用哪份配置”，不解释被引用内容的语义：

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `provider` | string | 非空；phase 1 固定写 `stub` |
| `ref` | string | 非空，不透明字符串；phase 1 指向 `fakes/host.json#<slot>` |

`ref` 的解析由调用方通过 resolver 完成；本契约不规定 URI、路径或加载顺序。

### 2.3 `HostCapabilities`

运行时只拿到五个句柄，槽位名固定：

| 槽位 | 语义归属 | phase 1 是否定义行为 |
| --- | --- | --- |
| `process` | 进程调用 | 否 |
| `fs` | 文件与路径 | 否 |
| `env` | 环境变量 | 否 |
| `stdio` | 标准输入输出 | 否 |
| `exit` | 退出码映射 | 否 |

```text
HostCapabilities
├── profile : HostProfile
├── process : object   # 句柄；怎么调用由 phase 10/11 定义
├── fs      : object
├── env     : object
├── stdio   : object
└── exit    : object
```

句柄的**类型**刻意写成不透明对象：phase 1 不冻结方法签名，避免把某一个宿主的能力形态
提前焊进接口。phase 4/10/11 在各自 phase 卡片里补签名时，必须只增不改槽位名。

## 3. 加载入口

实现位置：`tools/rill_harness/host.py`（phase 1 测试设施；产品实现若换语言，按同一形状重写）。

| 入口 | 行为 |
| --- | --- |
| `load_profile(path)` | 读一个 profile，校验 §2.1/§2.2，返回 `HostProfile` |
| `load_profiles(root)` | 读 `<root>/profiles/*.json`，按 name 去重 |
| `bind_capabilities(profile, resolver)` | 对五个槽位各调一次 `resolver(binding)`，返回 `HostCapabilities` |

校验只做形状：

- 未知字段直接报错（防止拼写错误被静默忽略）；
- 槽位缺一或多一都报错；
- `provider` / `ref` 只校验非空字符串，不校验内容；
- 不读取、不解释 `ref` 指向的文件。

`resolver` 是唯一注入点。phase 1 没有真实 resolver，所以 `HostCapabilities` 只被构造，
不被执行；phase 10/11 各自提供 resolver，不需要改用例或契约形状。

## 4. profile 文件

`testdata/0.1.0/profiles/shell.json` 与 `agent.json` 形状完全相同，只有 `name` / `kind` /
`description` 不同：

```json
{
  "schema": "rill.host-profile/0",
  "name": "shell",
  "kind": "shell",
  "capabilities": {
    "process": {"provider": "stub", "ref": "fakes/host.json#process"},
    "fs": {"provider": "stub", "ref": "fakes/host.json#fs"},
    "env": {"provider": "stub", "ref": "fakes/host.json#env"},
    "stdio": {"provider": "stub", "ref": "fakes/host.json#stdio"},
    "exit": {"provider": "stub", "ref": "fakes/host.json#exit"}
  }
}
```

**同形是硬要求**：两个 profile 只允许在 `name` / `kind` / `description` 与 `ref` 指向的
实现上不同。harness 用 `host/shared/` 下的同源 fixture 验证“换 profile 不换 AST”。

## 5. phase 1 明确不定义的东西

| 项 | 为什么不在 phase 1 定 | 归属 |
| --- | --- | --- |
| `principal`（角色 vs OS 用户） | 0.1.0 §4.1 的“角色 + 权限”是 Agent 形态，Shell 没有角色；抽象方式未裁定 | phase 4 |
| 角色表 / 权限 / 白名单 | 属内核配置，0.1.0 已声明为边界 | phase 4/11 |
| `ExecLimits` | steps/time/bytes 的具体字段与截断语义未裁定 | phase 11 |
| `process` 的 argv/cwd/timeout/信号行为 | Shell 能力实现细节，phase 1 不预写 | phase 10 |
| `fs` 的路径策略、符号链接、workspace root | 同上 | phase 10 |
| `env` / `stdio` 的读写形态 | 同上 | phase 10 |
| 退出码数字与映射表 | roadmap 明确“只留钩子，不写死数字” | phase 10（钩子） |
| `ExecOutcome{value, ok, error, host_meta?}` | 运行期数据结构，属值模型 | phase 6 |
| `Value::Opaque` / `Value::Bytes` | 运行期值模型必须从第一天预留 | phase 6 |
| `ProcessResult{code, stdout, stderr}` | 宿主值，不塞进 `$` 的错误串 | phase 6/10 |
| 脚本侧能力声明 | 0.1.0 §五.1 明确脚本无权声明 | 永不实现 |

这些项没有一项阻塞 phase 1 的形状：profile 的五个槽位已经能把它们全部挂在后面，
不需要现在选边。若后续发现某一项必须改变槽位名或 profile 顶层字段，先改本文件并开 CR，
不得在实现里静默加字段。

## 6. Parser 纯度

硬规则（roadmap §3.3.1 第 6 条）：

- `src/lexer`、`src/parser`（phase 2/3）不得 import `host` / `process` / `fs` / `role` 模块；
- parser 只产出 AST，主语槽保留语法形态，不判断“agent 角色还是 OS 用户”；
- `类型:值` 只作为裸词进 AST，拆分与校验放加载期；
- 同一条 import 检查在 phase 2 落地时加进 `tools/check-0.1.0.sh` 的 Parser 组。

phase 1 的 harness 本身可以 import `host.py`（它是测试设施），这条纯度规则只约束
`src/` 下的产品实现。

## 7. 变更规则

1. 槽位名、profile 顶层字段、binding 字段属于**契约形状**：改动必须同时改本文件、
   `profiles/*.json`、`tools/rill_harness/host.py` 的校验与 `testdata/0.1.0/README.md`。
2. 能力语义只允许写在对应 phase 的卡片/实现里，不得回写到本文件冒充“已定义”。
3. 任何“Shell 放宽、Agent 收紧”的语法差异都先回 0.1.0 正文重审，不写进 parser 分支。
4. 形状变更若影响已产出的 AST golden，先开 CR，再重生成 golden；不得用改 golden 代替裁定。
