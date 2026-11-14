# PH-18 立项卡：CT 格式化与 round-trip（P6）

> 状态：正常开卡。CT 重写轨道第 6 层。体系见 `docs/phases/README.md`，
> 上游 `docs/planning/rill-0.1.0-ct-rewrite-roadmap.md`。语言规范 `docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-18`，目录 `docs/phases/PH-18/` |
| 目标 | CT 版实现压缩/展示双向转换，71 个 round-trip 输入全部通过，输出与 Python 参考实现一致。 |
| 范围 | 做什么：压缩、展示、缩进、按需引号/转义、map 展开/收缩、71 个 round-trip。不做什么：求值、宿主、二进制格式化、语法改动。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-14 的 AST；PH-13 的构建；`testdata/0.1.0` 的 71 个 round-trip 输入。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `18`（目标产品版本 `0.18.0`）。 |
| 已知风险 | 含空格长词、反向映射前缀歧义、`Bytes/Opaque` 有损；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| 压缩：去空白（引号内保留）、map 展开/收缩、值类映射归约 | 不改语义、不产生 `LongWord` 节点 |
| 展示：加空格、按块缩进、尾随块同行、按需双引号并转义 | 不做代码重排 |
| 长词唯一、可见链最近绑定、反向映射内到外首个命中 | 不处理二进制值（透传或 `cannot_format`） |
| 71 个 round-trip 输入与 Python 输出对拍 | 不改 Python formatter、不改 golden |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `ct/src/formatter.h.ct` | 压缩/展示接口 |
| `ct/src/formatter.m.ct` | 双向转换与转义 |
| `tools/diff/diff.py`（fmt 层） | 71 个 round-trip 对拍 |
| `docs/reviews/diff/PH-18.md` | 本阶段差异报告 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-18-T1 | `ct/src/formatter.h.ct`、`ct/src/formatter.m.ct`（压缩） | `feat(ct): PH-18-T1 压缩态` | `git revert <sha>` | `python3 tools/diff/diff.py --layer fmt --mode compress` | M | E-2,E-4 |
| PH-18-T2 | `ct/src/formatter.m.ct`（展示） | `feat(ct): PH-18-T2 展示态` | `git revert <sha>` | `python3 tools/diff/diff.py --layer fmt --mode display` | M | E-2,E-3 |
| PH-18-T3 | 长词/转义/反向映射补差 | `feat(ct): PH-18-T3 可逆性` | `git revert <sha>` | `python3 tools/diff/diff.py --layer fmt --mode roundtrip` | M | E-1,E-5 |
| PH-18-T4 | `docs/reviews/diff/PH-18.md` | `docs(diff): PH-18-T4 格式化差异报告` | `git revert <sha>` | `test -s docs/reviews/diff/PH-18.md` | S | E-6 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 71 个 round-trip 输入全部通过（压缩→展示→压缩 AST 等价） | `--mode roundtrip` 退出 0 |
| E-2 | 压缩态与展示态逐字节与 Python 一致（除允许的换行归一） | diff 报告 0 未解释差异 |
| E-3 | 含空格/含双引号/含单引号长词各有用例通过 | 3 个定向用例 |
| E-4 | `//map {` 与 `//map{` 空格容忍 | 两个 fixture 输出一致 |
| E-5 | `Bytes`/`Opaque` 不透传成文本、不报假成功 | 透传或 `cannot_format` |
| E-6 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-14 的 AST；71 个 round-trip 输入；`tools/diff` 的 fmt 层（本卡扩展）。 |
| 风险 1 | 含空格长词：先去空白会拆词。触发信号：回读 token 数变化。 |
| 风险 2 | 反向映射前缀歧义：`alpha`/`alphabet` 取错短词。触发信号：展示态短词与 Python 不同。 |
| 风险 3 | 二进制值有损：`Bytes` 被转文本。触发信号：E-5 红。 |
| 风险 4 | 与 PH-15/16/17 并行时改动 `Value`：fmt 只读 AST，不依赖求值。触发信号：formatter 引入 eval 头。 |

## 6. 收口与 tag

- 收口附 `docs/reviews/diff/PH-18.md` 与 `docs/reviews/closeout-18.md`。
- 版本 `0.18.0`；tag 按 `docs/phases/README.md` §4，本卡不自动打 tag、不 push。
- 本卡只依赖 PH-14，可与 PH-15/16/17 并行；收口后进入 PH-21 汇合。
