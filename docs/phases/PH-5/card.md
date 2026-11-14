# PH-5 立项卡：展示/压缩互转与回读（Parser 轨）

> 状态：**部分收口**。`E-3` 与 `E-5` 于 2026-11-15 经用户裁定**移出 0.1.0**，转入 0.1.1 backlog
> （`docs/planning/rill-0.1.1-backlog.md`）；其余判据收口。本卡**不计为全绿**，见 §7。
> 体系见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 5；roadmap phase 5「展示/压缩互转与回读」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-5`，目录 `docs/phases/PH-5/` |
| 目标 | 实现 §4.16–§4.17 的双向转换：AST → 压缩态/展示态文本，且回读 AST 等价。 |
| 范围 | 做什么：压缩、展示、缩进、按需加引号与转义、map 展开/收缩、round-trip 校验。不做什么：求值、宿主能力、二进制格式化。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-3 的 AST；PH-2 的 token 规则；PH-4 的长词唯一性（本阶段只消费）。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `5`（收口目标产品版本 `0.5.0`）。 |
| 已知风险 | 含空格长词与去空白冲突；反向映射前缀歧义；`Bytes/Opaque` 不得有损转 STRING；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| 压缩：去空白（引号内保留）、展开/收缩 map、值类映射归约为 STRING | 不改语义、不产生 `LongWord` 节点 |
| 展示：加空格、按块缩进、尾随块同行、按需加双引号并转义 | 不做语法美化之外的代码重排 |
| 可逆性：长词唯一、可见链最近绑定、反向映射内到外首个命中 | 不处理二进制值（透传或 `cannot_format`） |
| `//map` 头在展示态的位置与 `//map {` 空格容忍 | 不执行任何语句 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/formatter.py` | 压缩/展示双向转换 |
| `src/rill/cli.py` | `rill fmt --compress` / `--display` |
| `tools/check-fmt.sh` | round-trip 与 golden 门禁入口 |
| `testdata/0.1.0/positive/fmt/` | 长词/转义/三类标记用例 |
| `testdata/0.1.0/expected/fmt/` | 压缩态与展示态 golden |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-5-T1 | `src/rill/formatter.py`（压缩） | `feat(fmt): PH-5-T1 压缩态` | `git revert <sha>` | `bash tools/check-fmt.sh --compress` | M | E-1 |
| PH-5-T2 | `src/rill/formatter.py`（展示） | `feat(fmt): PH-5-T2 展示态` | `git revert <sha>` | `bash tools/check-fmt.sh --display` | M | E-2 |
| PH-5-T3 | `src/rill/formatter.py`（长词/转义/反向映射） | `feat(fmt): PH-5-T3 可逆性` | `git revert <sha>` | `bash tools/check-fmt.sh --roundtrip` | M | E-1,E-3 |
| PH-5-T4 | `tools/check-fmt.sh` 与 golden 接入 | `feat(fmt): PH-5-T4 门禁接入` | `git revert <sha>` | `bash tools/check-fmt.sh --all` | S | E-4,E-5,E-6 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 压缩→展示→压缩的 AST 忽略 `span` 后相等 | `bash tools/check-fmt.sh --roundtrip` 退出 0 |
| E-2 | 展示→压缩不改变语义，不产生 `LongWord` 节点 | golden 节点断言 |
| E-3 | 含空格长词、含 `"` 长词、含 `'` 长词、三类标记各有 golden | **已裁定移出 0.1.0（2026-11-15）→ 0.1.1 backlog `BL-001`；不计为通过** |
| E-4 | `//map {` 与 `//map{` 的空格容忍 | 两个 fixture 的展示/压缩结果一致 |
| E-5 | `Bytes`/`Opaque` 不做有损格式化 | **已裁定移出 0.1.0（2026-11-15）→ 0.1.1 backlog `BL-002`；不计为通过** |
| E-6 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-3 的 AST 节点与 span；PH-2 的引号/转义规则；PH-4 保证同一长词只对应一个短词。 |
| 风险 1 | 含空格长词与去空白冲突：`my application` 必须先按需加引号再删空白。触发信号：压缩后回读成两个 token。 |
| 风险 2 | 反向映射前缀歧义：`alpha`/`alphabet` 从内到外取首个命中。触发信号：展示态选了错误短词。 |
| 风险 3 | 二进制值有损转 STRING：会破坏 Shell 宿主的约束。触发信号：`Bytes` 用例被格式化成文本。 |

## 6. 收口与 tag

- 本卡**没有按原判据单独收口**：formatter 最终由 PH-12-T1 的最小 `fmt` 提供；
  `E-3`/`E-5` 已裁定移出，见 §7。
- 产品版本未按本卡目标 `0.5.0` 单独发布；tag 未打、不 push。
- 收口对照表：无独立 `closeout-5.md`；PH-5 的判定记录在
  `docs/reviews/rill-0.1.0-completion-audit.md` 与 §7。

## 7. 2026-11-15 裁定记录：E-3 / E-5 移出 0.1.0

- **裁定**：`E-3`（fmt golden，三类长词）与 `E-5`（`Bytes`/`Opaque` 格式化断言）
  **移出 0.1.0，记入 0.1.1 遗留**。这是已裁定移出，不是“暂缓”“待定”，也不是通过。
- **理由**：① PH-5 的 formatter 未按卡交付，`testdata/0.1.0/expected/fmt/` 从未建立；
  ② 0.1.0 实际只有 PH-12-T1 的最小 `fmt`，没有独立 golden 与二进制值断言；
  ③ `Bytes`/`Opaque` 的格式化口径可能需要在 0.1.1 修订规范正文，0.1.0 不扩语义。
- **账目**：0.1.0 的 PH-5 记 4/6（`E-1`、`E-2` 按替代/缩小锚点，`E-4`、`E-6`），
  `E-3`/`E-5` 记“移出”，**不计入通过数**；因此 0.1.0 不是 12 张卡全绿。
- **去向**：`docs/planning/rill-0.1.1-backlog.md` 的 `BL-001`、`BL-002`。
- **冻结说明**：PH-5 无 `PH-5` 实现提交，`g8-phase-freeze` 对该卡为 SKIP，
  本次修改不破坏已冻结的判据。
