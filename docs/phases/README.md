# phase 卡片与收口账体系（PH-1…PH-12）

本目录把 `docs/planning/rill-0.1.0-roadmap.md` 的 12 个阶段落成可冻结、可门禁的 phase 卡片。
体系依据：主规范 `ai-coding-workflow.md` 1.9.0 §6.2（phase 交付流程）、§6.3（三档流程）、
§6.4（门禁）、§6.6（任务切分）、§6.7（版本号）。本目录只记账，不改
`docs/RILL-0.1.0.md` 正文，也不改 roadmap / phase-plan 的阶段编号与并行结论。

## 1. 目录与编号

| 项 | 约定 |
| --- | --- |
| 卡片 | `docs/phases/PH-<n>/card.md`，`n` 与 roadmap 的 phase `n` 一一对应 |
| 收口对照表 | `docs/reviews/closeout-<n>.md`（阶段 2、3 的模板已建，其余收口时新建） |
| 门禁红证 | `docs/reviews/gate-evidence.md`（新增检查的负例原始输出） |
| 编号口径 | `PH-1`=基座、`PH-2`=词法、…、`PH-12`=双宿主集成，见 roadmap 附录新旧对照 |

`PH-1` 与 `PH-2` 的实物产出早于本体系，因此写「对照卡」：格式与正常卡一致，但明确标注
事后补记、判据与红证在该阶段未成立，并列出可还原证据与永久缺失项（见各自 §7）。
`PH-3`…`PH-12` 为正常开卡。

## 2. 开卡必填与冻结

每张卡 §0 必备十项：编号、目标、范围、交付物清单、任务清单、退出判据、依赖、规范版本、
`version-minor`、已知风险。缺一即 `g1-phase-card` 失败。

- 任务行四要素：一个交付物、一条 `verify`、一次实现提交、`git revert` 可单独回滚；
  `effort` 只允许 `S` / `M`，`L` 必须再拆。
- 退出判据必须显式含「任务清单每项可独立验收（T-6）」。
- `tasks` 与 `exit-criteria` 在**首个实现提交之后**不可改；要改只能关闭当前 phase 另开。
  由 `g8-phase-freeze` 对「首个实现提交的父提交」与工作树逐字比对。

## 3. 版本号口径

两套版本号不混用（§6.7 开篇）：

| 版本 | 载体 | 取值 |
| --- | --- | --- |
| 语言规范版本 | `docs/RILL-0.1.0.md`（标题 0.1.1） | 只读；卡片不引用它作为产品版本 |
| 方法论 pin | `AGENTS.md` 生成块头 `version` | 开卡快照 `1.9.0`，写进每张卡「规范版本」 |
| 产品版本 | `MAJOR.MINOR.PATCH`，落点待 `AGENTS.md`「版本落点」声明 | `PH-<n>` 收口时 `MINOR = n`、`PATCH` 归零，即 `0.<n>.0` |

`version-minor` 写 `n`，`g1-phase-card` 校验它等于 `PH-<n>`（该子检查输出前缀 `g1-version`）。
`PATCH` 由该 phase 内的 fix 数决定，**不写进卡片**。

现状：`AGENTS.md` 的「版本落点」已声明为 `src/rill/__init__.py#__version__`，
当前产品版本 `0.12.0`（PH-12 收口）。`g8-version` 在落点声明后按声明校验；
仓库仍为 0 个 tag（按用户指令本轮不打 tag）。

## 4. tag 口径

- phase 收口**必打 annotated tag** 并推送该 tag：名 `v0.<n>.<patch>`，指向收口提交，
  message 含 `PH-<n>` 与收口提交 sha 前 7 位；只在四项校验（名/annotated/指向/可追溯）全过后推。
- **只推 tag，不推分支，不对外发布**。分支推送与远端发布须用户显式指令（§6.5）。
- fix 不打 tag；fix 只进 CHANGELOG，由下一次 phase tag 覆盖。
- 现状：仓库 tag 数量为 **0**。`PH-1`、`PH-2` 的实物早于本体系，**不自动补打历史 tag**；
  是否回补由用户单独裁定，卡片只登记「未打」，不代替用户决定。
- `g8-version` 校验：tag 名、annotated 属性、message 里的 `PH-<n>`、`MINOR == n`、
  `PATCH == 0`、指向提交是 `HEAD` 祖先；以及已声明版本落点的一致性。

## 5. 门禁挂靠

| 检查 | 挂靠 | 守什么 | 失败处置 |
| --- | --- | --- | --- |
| `g1-phase-card` | G1 | 必填十项、任务四要素、`effort` 取值、退出判据含 T-6、任务不覆盖全部判据、`version-minor = n` | 退回立项，不得开工 |
| `g8-phase-freeze` | G8 | 首个实现提交后 `exit-criteria` 与 `tasks` 未被修改 | 关闭当前 phase，另开一个 |
| `g8-version` | G8 | phase tag 名/annotated/指向；`MINOR` 与 `PH-<n>` 对应；版本落点一致 | 不推送 tag，按 V-6 立案 |

未覆盖项（如实登记，不假装覆盖）：V-2/V-3/V-4/V-5 的提交级 PATCH 计数与同提交落点校验，
要等版本落点声明后才能机械执行；当前只在收口对照表里人工逐条核。T-7 的父子提交检查由
收口对照表逐任务核（`git log -2` + `git merge-base --is-ancestor`），尚未做成独立子检查。

## 6. 红证与提交节奏

每个实现任务先提交 `test(<scope>): PH-<n>-T<x> 红`（只含夹具、golden 与红证），再提交
`feat(<scope>): PH-<n>-T<x> <一句话>`；红证正文含 `baseline: <sha>`、命令、原始输出、退出码。
纯文档 / 纯配置 / 纯注释任务写 `no-test: <理由>`，由评审签字。DEV 不自签，VERIFY 认定。

## 7. 收口与回顾

收口对照表 `docs/reviews/closeout-<n>.md` 必须包含：交付物对照、退出判据逐条证据、
issues 三去向（本 phase 修 / 登记到某个未来 phase / 明确拒绝并写理由）、`lessons` 表。
`lessons` 每行 `landing` 只能取 `gate:<门禁>`、`spec:<节>`、`rejected:<理由>` 之一；
写成心得体会视为未完成。

## 8. 已知局限

1. `PH-1` / `PH-2` 无开卡提交、无判据冻结、无逐任务红证；只能还原「产出物存在」与「当前可复跑结果」。
2. 两个阶段产出的全部文件目前在 git 中**未跟踪**（`src/`、`testdata/`、`tools/rill_harness/`、
   `tools/check-0.1.0.sh` 等），因此没有提交 sha 可引，红证无从补造。
3. `tools/check-0.1.0.sh --list` 当前因 2 个 fixture 缺 `case.json` 退出 1；这是其他在途改动，
   本体系不改它，只在对照卡里如实登记状态。
