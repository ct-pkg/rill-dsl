# RILL 0.1.0 双实现 parity 总账

> 两套实现长期并存：`src/rill/`（Python 参考实现，冻结）与 `ct/`（CT 实现，正式入口）。
> 本文件登记两侧的能力矩阵、已知差异与不比较字段，供后续任何一相回归时对照。

## 1. 定位

| 项 | Python 参考实现 | CT 实现 |
| --- | --- | --- |
| 路径 | `src/rill/` | `ct/src/` + `ct/bin/rill` |
| 状态 | **冻结**（E-6：`git diff --quiet 4dd303d -- src/rill` 为 0） | 正式入口 |
| 用途 | 对拍基准、语义仲裁 | 交付物 |
| 启动 | `python3 -m rill` | `ct/bin/rill`（`~/.local/bin/rill` 软链） |

两侧不互相 import，不共享代码，只共享 `testdata/0.1.0` 语料与 golden。

## 2. 能力矩阵

| 能力 | Python | CT | 对拍面 |
| --- | --- | --- | --- |
| `tokenize` | ✅ | ✅ | token 层，82 源 |
| `parse --dump-ast` | ✅ | ✅ | ast 层，82 源 |
| `check` | ✅ | ✅ | error 层，26 负例 |
| `run`（fakes） | ✅ | ✅ | eval 层，19 源 |
| `run`（Shell 宿主） | ✅ | ✅ | host 层 shell，12 fixture + 5 定向 |
| `run`（Agent 宿主） | ✅ | ✅ | host 层 agent，14 fixture + 1 定向 |
| `fmt --compress` | ✅ | ✅ | fmt 层，71 语料 + 3 定向 + 2 header |
| `fmt --display` | ✅ | ✅ | 同上 |
| round-trip 守恒 | ✅ | ✅ | 同上（§4.16） |
| `--profile shell/agent` | ✅ | ✅ | 两个 profile 逐字段比 |

## 3. 已知差异

| # | 差异 | 归属 | 结论 |
| --- | --- | --- | --- |
| 1 | 非 ASCII 词边界：`a —b` 的 token 切分 | PH-13 首建 token 层时发现 | **CT 正确，Python 候选缺陷**。判据锚 §4.16（压缩→展示保持 token 序列）与 §1「符号即边界」；Python 把两个 `BARE` 并成一个，破坏了可逆性。不改参考实现，登记为已知偏差（`diff/PH-19.md` §10） |
| 2 | `host_meta.tool_meta.transport.pid` | PH-20 | 进程号不可比，比较时剔除，保留在输出里 |
| 3 | AST `span` | PH-14 | 既有 golden 口径不含 span；两侧都不比 |

除这 3 条外，全层为 0 差异（`docs/reviews/diff/PH-21.md` §1）。

## 4. 明确不承诺等价的部分

| 项 | 说明 |
| --- | --- |
| 并发/取消/超时调度 | 按源序串行模拟，不做真并发；规范允许 |
| 生产安全策略、真实审批 | 不在 0.1.0 范围 |
| 性能 | 未做基准，不承诺 |
| `Opaque` 值 | 两侧都没有运行期构造入口，无法验收（见 §5） |

## 5. 判据未闭环

| 判据 | 结果 |
| --- | --- |
| `Bytes` 的读取/透传/truthy | 过（Shell 真实入口） |
| `Opaque` 的透传/truthy | **不过**：0.1.0 没有构造入口，构造不出触发条件就不记通过 |

结论：**0.1.0 不满足**（按「判据不降、构造不出就不记通过」的口径）。
详见 `docs/reviews/0.1.0-verdict.md`。

## 6. 漂移防护

- 每次改动后跑 `python3 tools/diff/diff.py --layer all`，差异必须为 0。
- 禁止为让一侧过而改 `testdata/0.1.0`（golden 变更需单列 `golden-change:` 提交）。
- 禁止改 `src/rill/`；需要仲裁时以规范 §1 / §4.16 为准，两侧各自修。
