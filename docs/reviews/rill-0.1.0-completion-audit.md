# RILL 0.1.0 完成度对账

> 对账对象：`docs/phases/PH-1..PH-12/card.md` 的 §4 退出判据。证据在
> 2026-11-15 重跑，产品版本 `0.12.0`。本表只写真发生的事；替代锚点单列，
> 不把“用例通过”写成“能力可用”。

## 0. 证据缩写

| 缩写 | 命令 | 本次结果 |
| --- | --- | --- |
| H | `bash tools/check-0.1.0.sh --all` | 85 fixtures；83 compliance + 2 smoke passed；0 failed / 0 blocked / 0 draft；pending 0；exit 0 |
| T | `for f in tests/phase*/test_*.py; do python3 "$f" || exit 1; done` | 全部 PASS |
| F | `bash tools/check-fmt.sh --roundtrip` | 71 个 fixture；AST 等价；exit 0 |
| G | `bash tools/check.sh all` | 0 FAIL；`== overall: PASS ==` |
| D | `git diff --quiet d686ca3 -- src/rill/lexer.py src/rill/parser.py` | exit 0（PH-10 之后无改动） |
| A | `rill parse --dump-ast` 双 profile | `ef2d0db…` 与 `ef2d0db…` 相同 |

## 1. 逐卡对账

### PH-1 基座

| 判据 | 实际锚点 | 证据 | 判定 |
| --- | --- | --- | --- |
| E-1 `--list` 可枚举，正例≥12/负例≥10 | 85 个 fixture 全部发现；无缺 `case.json` | H | PASS |
| E-2 `case.json` 含 kind/phase/expect | 0 draft；负例全被识别 | H | PASS |
| E-3 同源 fixture 双 profile AST 相等 | `host/shared/read-send` 逐节点相等 | H、A | PASS |
| E-4 parse 未实现时退出 3 | **替代锚点**：parse 已在 PH-3 实现；当前 `parse` 退出 0，退出 3 只保留为历史桩 | PH-1 卡 §7、`parse` 实测 | PASS（锚点已过期） |
| E-5 T-6 | 本表逐项对应 | 本文件 | PASS |

### PH-2 词法

| 判据 | 实际锚点 | 证据 | 判定 |
| --- | --- | --- | --- |
| E-1 token golden 全过 | `--all` 的 p1 token 用例全绿 | H | PASS |
| E-2 `//map {` / `//map` 注释 | `positive/map/space-header` 含空格头 | H | PASS |
| E-3 引号/短词/`r<read` 切分 | `map-entries`、`map-verb-marker` | H | PASS |
| E-4 E-01/E-02 各 1 负例 | `negative/tokenize/*` | H | PASS |
| E-5 稳定错误码与行列 | harness 逐条断言 `stage/code/line/col` | H | PASS |
| E-6 T-6 | 本表 | 本文件 | PASS |

### PH-3 语法与 AST

| 判据 | 实际锚点 | 证据 | 判定 |
| --- | --- | --- | --- |
| E-1 AST 词汇/字段/span 可断言 | `test_ast_json.py` | T | PASS |
| E-2 map 头与映射展开 | `positive/map/*` AST 断言 | H | PASS |
| E-3 调用/介宾/`@`/`//fn` 模板 | `prep-phrases`、`call/basic`、`assign` 三条 AST 断言 | T、H | PASS |
| E-4 控制流与尾随块 | `if` 带主语、each、break 五分支、`[into]`、parallel results 六条 AST 断言 | T、H | PASS |
| E-5 非法位置稳定解析错误 | negative 桶逐条断言 code/line/col | H | PASS |
| E-6/E-7 正例 golden / 每形态 1 golden | positive ast 桶全部有 golden | H | PASS |
| E-8 T-6 | 本表 | 本文件 | PASS |

### PH-4 加载期

| 判据 | 实际锚点 | 证据 | 判定 |
| --- | --- | --- | --- |
| E-1 4 条 PH-4 用例 | `test_cases.py` + `--phase p4` | T、H | PASS |
| E-2 3 条 load 负例 | 逐条断言 code/line/col | H | PASS |
| E-3 `W-01` 不阻断 | `positive/check/each-bareword-w01` | H | PASS |
| E-4 双 profile 均通过，role 非必填 | `positive/check/host-profiles` | H | PASS |
| E-5 加载期不执行工具 | `test_no_exec.py` 结构断言 | T | PASS |
| E-6 T-6 | 本表 | 本文件 | PASS |

### PH-5 展示/压缩互转

| 判据 | 实际锚点 | 证据 | 判定 |
| --- | --- | --- | --- |
| E-1 压缩→展示→压缩 AST 相等 | **替代锚点**：PH-5 未交付 formatter；PH-12-T1 的最小 `fmt` + 本命令 | F | PASS（替代） |
| E-2 展示不改变语义、无 LongWord | 往返 AST 等价；没有 `expected/fmt/` golden | F | PASS（缩小） |
| E-3 三类长词各有 golden | **未满足**：`testdata/0.1.0/expected/fmt/` 不存在 | `ls` 实测 | **未满足** |
| E-4 `//map {`/`//map{` 空格容忍 | `space-header` 往返 | F | PASS |
| E-5 Bytes/Opaque 不有损格式化 | **未满足**：没有专门 fixture/断言 | 代码与 fixture 检索 | **未满足** |
| E-6 T-6 | 本表 | 本文件 | PASS |

### PH-6 值模型

| 判据 | 实际锚点 | 证据 | 判定 |
| --- | --- | --- | --- |
| E-1..E-5 falsy/`ok`/错误串/`$`/Bytes | `test_truthy`、`test_result`、`test_value` | T | PASS |
| E-6 `exit_code` 钩子 | `test_result` 接口断言 | T | PASS |
| E-7 T-6 | 本表 | 本文件 | PASS |
| E-8 `expr`/`simple_stmt` 两条管道 | `test_pipe.py` 两组独立用例 | T | PASS |
| E-9 each 失败记 null 并继续 | `test_pipe.py` 轮结果数组 | T | PASS |
| E-10 `\|>` 只传 value/短路 | `test_pipe.py` 下游计数 | T | PASS |
| E-11 fake 队列耗尽取 default | `test_verbs.py` | T | PASS |

### PH-7 简单语句与尾随块

| 判据 | 实际锚点 | 证据 | 判定 |
| --- | --- | --- | --- |
| E-1 四种段输出 golden | `expected/run/` 四文件 | `test_cases.py`、H | PASS |
| E-2 `[into]` 失败轨迹唯一 | 轨迹 golden | T | PASS |
| E-3 多 `[into]` 失败后续不执行 | 轨迹断言 | T | PASS |
| E-4 `[ok]`/`[error]` 的 `$` | 逐字断言 | T | PASS |
| E-5 下游只收 value | 段间 golden | T | PASS |
| E-6 T-6 | 本表 | 本文件 | PASS |

### PH-8 管道/if/each/break

| 判据 | 实际锚点 | 证据 | 判定 |
| --- | --- | --- | --- |
| E-1 3 段以上管道错误归属 | `control/pipe-three` | T、H | PASS |
| E-2 if truthy/falsy 与 ok 分离；四形态 | `test_if.py` 带主语条件已求值 | T | PASS |
| E-3 each null/空数组/非数组轮数 | `test_each.py` 三轮数 | T | PASS |
| E-4 失败轮 null 与 each 级块 | `test_each.py` 逐位 | T | PASS |
| E-5 break 三场域/失败后/裸词 | `test_break.py` | T | PASS |
| E-6 T-6 | 本表 | 本文件 | PASS |

### PH-9 parallel/`[results]`/`@fn`

| 判据 | 实际锚点 | 证据 | 判定 |
| --- | --- | --- | --- |
| E-1 分支三态数组 | `test_parallel.py` | T | PASS |
| E-2 `[results]` 四位置报错 | `test_results.py` | T | PASS |
| E-3 模板 3 处 `$path` 只收 1 个实参 | `test_fn.py` 参数计数与同名绑定 | T | PASS |
| E-4 默认值只允许尾部 | `test_fn.py` 两负一正 | T | PASS |
| E-5 未声明/参数个数错误 | `test_errors.py` | T | PASS |
| E-6 函数返回最后段 | `test_fn.py` | T | PASS |
| E-7 T-6 | 本表 | 本文件 | PASS |

### PH-10 Shell 宿主

| 判据 | 实际锚点 | 证据 | 判定 |
| --- | --- | --- | --- |
| E-1 五类能力成功/失败 | `test_host_fixtures.py` 12 例 | T | PASS |
| E-2 进程字段与二进制 stdin | `test_process.py` | T | PASS |
| E-3 失败退出码由清单给出 | `test_stdio_exit.py` 改为 7 | T | PASS |
| E-4 同源 AST 与 agent 相等 | 逐 fixture 比对 | T、H | PASS |
| E-5 无 parser/lexer 改动 | D | `LEXER_PARSER_DIFF=0` | PASS |
| E-6 T-6 | 本表 | 本文件 | PASS |

### PH-11 Agent 宿主

| 判据 | 实际锚点 | 证据 | 判定 |
| --- | --- | --- | --- |
| E-1 同源 fixture/AST | queue 桩与 canonical 两套 fixture | T、H | PASS |
| E-2 能力矩阵五类两列 | host-matrix 五节 + 差异表 | `test_matrix_doc.py` | PASS |
| E-3 `[error]` 只拿字符串 | `test_tools_process_stdio.py` | T | PASS |
| E-4 无 parser/lexer 改动 | D | exit 0 | PASS |
| E-5 T-6 | 本表 | 本文件 | PASS |
| E-8 工具真实走出进程 | **替代锚点**：原 T1–T5 只有队列桩；T6 改为 `command` 工具 + 真实 pid/日志 | `test_tool_transport.py`、closeout-11 §4 | PASS（补锚点） |
| E-9 fakes 失败退出码/错误码退役 | 未处理失败退出 1；`src/` 无 `E-RUN-HOST-UNAVAILABLE` | `test_host_contract.py` | PASS |
| E-10 共用核心/可识别 principal | 一处 `Interpreter(`；`payload.host.profile/principal` | `test_host_contract.py` | PASS |

### PH-12 集成

| 判据 | 实际锚点 | 证据 | 判定 |
| --- | --- | --- | --- |
| E-1 正例通过/负例按错误码失败 | 83 compliance + 2 smoke；0 failed | H | PASS |
| E-2 pending 为 0 | `pending 0`；retired 4 不计数 | H | PASS |
| E-3 round-trip 全绿 | 71 fixture | F | PASS |
| E-4 双 profile AST/差异入表 | host 桶 + 6 条 host-specific 差异 | H、host-matrix §9.2 | PASS |
| E-5 `--all` 退出 0 | `VERDICT: PASS (exit 0)` | H | PASS |
| E-6 不改 0.1.1 正文 | `git diff --quiet HEAD -- docs/RILL-0.1.0.md` 退出 0；无 CR | 实测 | PASS |
| E-7 T-6 | 6 项 verify 均 exit 0 | closeout-12 §3 | PASS |

## 2. 替代/缩小锚点

| # | 判据 | 原锚点 | 实际锚点 | 性质 |
| --- | --- | --- | --- | --- |
| 1 | PH-1 E-4 | parse 未实现退出 3 | parse 已实现，退出 0；退出 3 只作历史桩 | 锚点过期 |
| 2 | PH-5 E-1 | PH-5 自己的 formatter | PH-12-T1 最小 `fmt` + roundtrip | 依赖挪用 |
| 3 | PH-5 E-2 | `expected/fmt/` golden | 往返 AST 等价，无 golden | 缩小 |
| 4 | PH-5 E-3 | 三类长词 golden | 未交付 | 未满足 |
| 5 | PH-5 E-5 | Bytes/Opaque 专用断言 | 未交付 | 未满足 |
| 6 | PH-11 E-1 | 队列桩工具 | canonical `command` 工具 + 真实 pid | 补锚点 |
| 7 | PH-12 E-2 | 目录里 pending 计数 | harness pending 0 + retired 4 分开写 | 口径澄清 |

替代/缩小共 7 条，超过“少数几条”，说明立卡时对“最终可观察锚点”写得不够实。
对应的 lessons 见 §3；PH-5 的 E-3/E-5 不计为通过。

## 3. lessons

| # | 事实 | landing |
| --- | --- | --- |
| 1 | 判据写成“未实现状态”（如 parse 退出 3），实现后无法复跑 | `gate:g1-phase-card`：立卡必须写最终可观察锚点，过渡桩只能作为补充证据 |
| 2 | PH-5 依赖 formatter，但 formatter 到 PH-12 才以最小实现出现 | `gate:g1-phase-card`：依赖必须是物理存在的交付物，不能只写在卡片 §5 |
| 3 | PH-11 T1–T5 用队列桩也能“全绿”，但 Agent 仍不能真实跑 | `gate:g5`：宿主判据必须含 egress 见证（pid/日志/副作用），不接受纯 payload |
| 4 | 文档门禁 21 FAIL 被当作“既有基线”跨阶段保留 | `gate:g4`：收口必须逐项清或逐项登记豁免，基线数不能长期红着 |
| 5 | PH-12 收口后红证继续增长，导致 DOC-S2 基线漂移 | `gate:g4`：收口文档定稿后重跑门禁，新增证据用附录拆分 |
| 6 | 独立 `[ok]/[error]` 从 PH-7 漂到 PH-11 才给绕法 | `spec:§4.10`：首次命中的 phase 必须裁定或立 CR，不许“登记未实现”长期漂 |
| 7 | Agent `workspace` 相对 cwd 解析，manifest 位置不决定根 | `spec:§五.2`：在 manifest 规范里写明解析基准；当前 README 已注明 |

## 4. 仍不可用（按性质）

| 层 | 项 | 调用方会遇到什么 |
| --- | --- | --- |
| 语法层 | 独立 `[ok] $x {}` / `[error] $x {}` | 报 `E-RUN-UNSUPPORTED`（退出 2）；必须把块挂到产生 `$` 的语句后 |
| 动词层 | Shell 的 `parse`/`search`/`replace`/`contains`/`review` | 报 `E-RUN-VERB-UNREGISTERED`；当前只有 read/write/run/env/send 有真实映射 |
| 动词层 | Agent 的 `search`/`parse`/`replace`/`contains`/`review` | 默认 manifest 未注册这些工具，报 `E-HOST-TOOL-UNREGISTERED`；需在 tools.json 加 `command` |
| 宿主层 | Agent 读真实 OS 环境变量 | 只能读 manifest `context`；读 `$HOME` 等会 `E-HOST-ENV-MISSING` |
| 宿主层 | Agent 未处理失败的 OS 退出码 | 退出 0，调用方若只看 `$?` 会误判成功；必须读 `payload.ok` |
| 宿主层 | Shell 的 `类型:值` | Shell 不拆类型，`file:config.txt` 会被当字面路径 |
| 宿主层 | 远端工具传输 | `command` 工具只在本机起子进程；没有网络工具网关 |
| 限流与审批 | `limits` 只做 steps/time/bytes | 超限 `ok=false`；`parallel` 分支数与搜索深度未限流 |
| 限流与审批 | 审批/白名单/密钥注入 | 未接；任何危险操作只受宿主能力清单约束，没有人工审批环节 |

## 5. 版本与收口

- 产品版本：`0.12.0`，落点 `src/rill/__init__.py#__version__`；语言规范版本
  0.1.1 不参与产品版本核对。
- 本地提交，不打 tag、不 push（按用户指令）；tag 需另行授权。
- 第一次运行证据见 [closeout-12.md](closeout-12.md) §6 与 README §2/§3。
