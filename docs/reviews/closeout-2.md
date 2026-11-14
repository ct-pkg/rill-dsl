# PH-2 收口对照表（模板）

> 状态：**模板，未填写**。PH-2 是[对照卡](../phases/PH-2/card.md)，产出早于本体系：
> 本表只能做“追溯核对”，**不得据此宣称合规收口**，也不补打 tag。填写前先读
> `docs/phases/README.md` §7 的事后补记口径。

## 0. 基本信息

| 项 | 值 |
| --- | --- |
| phase | `PH-2`（词法） |
| 卡片 | `docs/phases/PH-2/card.md` |
| 被测提交 | `<sha>`（若仍无提交，写“工作树未跟踪”，不得编造） |
| 产品版本 | 应为 `0.2.0`，实际：`<待填>` |
| tag | 未打（仓库 tag 数 0；是否回补由用户裁定） |
| 核对日期 | `<YYYY-MM-DD>` |
| 判定人 | EDITOR `<name>` |

## 1. 交付物对照

| 交付物（卡片 §2） | 路径 | 存在 | 证据（命令 / 文件） |
| --- | --- | --- | --- |
| 词法切分 | `src/rill/lexer.py` | `<是/否>` | `test -s src/rill/lexer.py` |
| token 序列化 | `src/rill/tokens.py` | `<是/否>` | `test -s src/rill/tokens.py` |
| 错误码 | `src/rill/errors.py` | `<是/否>` | `test -s src/rill/errors.py` |
| tokenize CLI | `src/rill/cli.py` | `<是/否>` | `PYTHONPATH=src python3 -m rill --help` |
| token golden | `testdata/0.1.0/expected/tokens/` | `<是/否>` | `find testdata/0.1.0/expected/tokens -name '*.json' \| wc -l` |
| 词法负例 | `testdata/0.1.0/negative/tokenize/` | `<是/否>` | `find testdata/0.1.0/negative/tokenize -name case.json \| wc -l` |
| 词法约定 | `docs/planning/rill-0.1.0-lexer.md` | `<是/否>` | `test -s docs/planning/rill-0.1.0-lexer.md` |

## 2. 退出判据逐条证据（卡片 §4）

| ID | 条件 | 命令 | 原始输出 / 退出码 | 结论 |
| --- | --- | --- | --- | --- |
| E-1 | 全部 token golden 通过 | `bash tools/check-0.1.0.sh --kind tokens` | `<贴原始输出>` | `<通过/失败/无法复跑>` |
| E-2 | `//map {` 不当注释；`//map` 无 `{` 当注释 | `bash tools/check-0.1.0.sh --show positive/tokens/space-header` | `<贴原始输出>` | `<…>` |
| E-3 | 四类切分符合 §3.2 | `bash tools/check-0.1.0.sh --show positive/tokens/map-entries` | `<贴原始输出>` | `<…>` |
| E-4 | `E-01`/`E-02` 各 1 负例 | `bash tools/check-0.1.0.sh --show negative/tokenize/map-bad-marker` | `<贴原始输出>` | `<…>` |
| E-5 | 非法输入有稳定错误码与行列 | `bash tools/check-0.1.0.sh --bucket negative --kind error` | `<贴原始输出>` | `<…>` |
| E-6 | 任务清单每项可独立验收（T-6） | 逐任务跑卡片 §3 的 `verify` | `<逐项贴输出>` | `<…>` |

## 3. issues 三去向

| issue id | 摘要 | 去向 | 理由 / 目标 |
| --- | --- | --- | --- |
| `<id>` | `<一句话>` | `<本 phase 修 / <PH-n> / 拒绝>` | `<理由；deferred 必须写目标 phase 或日期>` |

规则：每个 id 有且只有一个去向，没有第四种“先放着”。

## 4. lessons（每条必须落地）

| lesson | landing | 落地位置 | 验证 |
| --- | --- | --- | --- |
| `<教训>` | `gate:<门禁>` / `spec:<节>` / `rejected:<理由>` | `<文件:行>` | `<命令或评审签字>` |

## 5. 版本与 tag 核对

| 项 | 期望 | 实际 | 结论 |
| --- | --- | --- | --- |
| `version-minor` | `2` | `<g1-phase-card 输出>` | `<…>` |
| 产品版本 | `0.2.0` | `<落点值>` | `<…>` |
| tag 名 | `v0.2.0` | 未打 | 不补打，除非用户指令 |
| annotated | `git cat-file -t v0.2.0` = `tag` | `<无>` | `<…>` |
| 指向 | 收口提交 | `<无>` | `<…>` |

## 6. 门禁原始数字

```console
$ bash tools/check.sh all
<贴原始输出与 overall>
```

## 7. 事后补记声明（不可省略）

- 本表不是合规收口记录：PH-2 无开卡提交、无判据冻结、无逐任务红证、无 tag。
- 已填内容只能来自可复跑命令与文件存在性；不得引用“历史记录里是这个值”。
- 永久缺失项见 `docs/phases/PH-2/card.md` §7，不得补造。

## 8. 签字

| 角色 | 姓名 | 结论 | 日期 |
| --- | --- | --- | --- |
| EDITOR | `<name>` | `<追溯核对完成 / 不可宣称收口>` | `<date>` |
| VERIFY | `<name>` | `<红证不可认定>` | `<date>` |
| REVIEW | `<name>` | `<无评审记录>` | `<date>` |
