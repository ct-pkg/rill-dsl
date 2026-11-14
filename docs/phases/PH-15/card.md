# PH-15 立项卡：CT 加载期校验（P3）

> 状态：正常开卡。CT 重写轨道第 3 层。体系见 `docs/phases/README.md`，
> 上游 `docs/planning/rill-0.1.0-ct-rewrite-roadmap.md`。语言规范 `docs/RILL-0.1.0.md`（0.1.1，只读）。
> **CT 缺陷命中点**：PH-46（`Map<K, 用户 struct>` 按值进共享头）——见 §1 与 §5 的实测绕法。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-15`，目录 `docs/phases/PH-15/` |
| 目标 | CT 版完成 map/fn/verb/profile 四张表的加载期校验，7 个 load 负例与 `W-01` 全绿，且不执行工具。 |
| 范围 | 做什么：稳定键表、四表校验、调用绑定/默认值、HostProfile、错误码、`W-01`、error 层对拍。不做什么：求值、段输出、真实宿主、函数执行。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-14 的 AST；PH-13 的构建；`testdata/0.1.0/negative/load/`、`profiles/`、`fakes/`。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `15`（目标产品版本 `0.15.0`）。 |
| 已知风险 | `Map` 缺陷命中四表；键生命周期；`W-01` 不得阻断；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| 稳定键表：字形保留、哈希/比较、插入期拒绝重复 | 不做值语义的 `Map<Str, Value>`（PH-46 未修） |
| `//map` 可见链、长词唯一/反向映射；`//fn` 去重参数/默认值；verb/type 表 | 不求值、不执行函数 |
| `HostProfile` 校验；Shell 的 role 可为空 | 不接真实权限/白名单 |
| 7 个 load 负例 + `W-01` 警告；error 层对拍 | 不改 golden；不改 Python loader |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `ct/src/tables.h.ct` | 稳定键表接口（`Map<char*, Value*>` 绕法） |
| `ct/src/tables.m.ct` | 插入/查找/释放与生命周期 |
| `ct/src/loader.h.ct` | 四表校验接口 |
| `ct/src/loader.m.ct` | map/fn/verb/profile 校验与错误码 |
| `docs/planning/rill-0.1.0-ct-defect-workarounds.md` | PH-46 绕法、实测命令与代价（本 phase 首次建立） |
| `docs/reviews/diff/PH-15.md` | 本阶段差异报告 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-15-T1 | `ct/src/tables.h.ct`、`ct/src/tables.m.ct` | `feat(ct): PH-15-T1 稳定键表` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --kind error --bucket negative` | M | E-1 |
| PH-15-T2 | `ct/src/loader.h.ct`、`ct/src/loader.m.ct` | `feat(ct): PH-15-T2 四表校验` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show negative/load/unknown-function` | M | E-1,E-3 |
| PH-15-T3 | `W-01` 与错误码接线 | `feat(ct): PH-15-T3 W-01 与错误码` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --kind warning` | S | E-2 |
| PH-15-T4 | `docs/planning/rill-0.1.0-ct-defect-workarounds.md` | `docs(ct): PH-15-T4 Map 绕法登记` | `git revert <sha>` | `test -s docs/planning/rill-0.1.0-ct-defect-workarounds.md` | S | E-5 |
| PH-15-T5 | `docs/reviews/diff/PH-15.md`（error 层） | `docs(diff): PH-15-T5 error 层差异报告` | `git revert <sha>` | `python3 tools/diff/diff.py --layer error` | M | E-4,E-6,E-7 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 7 个 load 负例的错误码/行列与 Python 一致 | 逐条 JSON 比对 |
| E-2 | `W-01` 在 `each $f [in] xs` 触发且不阻断（退出 0） | `--kind warning` 原始输出 |
| E-3 | 四张表以只读接口暴露给 PH-16，复制/改写为硬错 | 接口测试 + 断言 |
| E-4 | error 层对拍 7/7，0 未解释差异 | `docs/reviews/diff/PH-15.md` |
| E-5 | PH-46 绕法有实测命令、通过证据与代价 | workarounds 文档三节齐全 |
| E-6 | CT 二进制不链接 Python | `test -z "$(otool -L ct/bin/rill_ct \| grep -i python)"` |
| E-7 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-14 的 AST 与 span；PH-13 的 `--sut`；`profiles/shell.json`、`profiles/agent.json`；`fakes/tools.json`。 |
| 风险 1 | **PH-46**：`Map<char*, Value>` 因元素不完整构建失败。绕法：`Map<char*, Value*>` 或 `Map<char*, void*>`（`ct-lang/docs/proposals/ct-json-capability-blockers.md` 实测后者通过）。代价：每次查表多一次解引用、键值显式释放，约 +150–300 行与一轮生命周期审计。 |
| 风险 2 | 键生命周期：短词切片指向源缓冲，源释放后变悬垂。绕法：插入时复制键；代价：每键一次分配。 |
| 风险 3 | `W-01` 阻断：警告不得改退出码。触发信号：`--kind warning` 退出非 0。 |
| 风险 4 | 为省事把校验塞进 parser：会破坏 PH-14 的层界。触发信号：`parse` 路径出现表查询。 |

## 6. 收口与 tag

- 收口附 `docs/reviews/diff/PH-15.md` 与 `docs/reviews/closeout-15.md`。
- 版本 `0.15.0`；tag 按 `docs/phases/README.md` §4，本卡不自动打 tag、不 push。
- 收口后 PH-16/PH-17/PH-20 的表依赖才可用。
