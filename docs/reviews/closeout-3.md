# PH-3 收口对照表（模板）

> 状态：**模板，未填写**。PH-3 为正常开卡：收口时本表必须逐条贴原始输出，
> 任一退出判据无证据即不得收口（§6.3 A-2）。口径见 `docs/phases/README.md`。

## 0. 基本信息

| 项 | 值 |
| --- | --- |
| phase | `PH-3`（语法与 AST） |
| 卡片 | `docs/phases/PH-3/card.md` |
| 收口提交 | `<sha>`（首个实现提交之后 `exit-criteria`/`tasks` 未被修改） |
| 产品版本 | 应为 `0.3.0`，实际：`<待填>` |
| tag | `<v0.3.0>`（annotated；指向收口提交；已推 tag） |
| 核对日期 | `<YYYY-MM-DD>` |
| 判定人 | EDITOR `<name>` |

## 1. 交付物对照

| 交付物（卡片 §2） | 路径 | 存在 | 证据（命令 / 文件） |
| --- | --- | --- | --- |
| AST 节点与序列化 | `src/rill/ast.py` | `<是/否>` | `test -s src/rill/ast.py` |
| 产生式与尾随块 | `src/rill/parser.py` | `<是/否>` | `test -s src/rill/parser.py` |
| `parse --dump-ast` | `src/rill/cli.py` | `<是/否>` | `PYTHONPATH=src python3 -m rill parse --dump-ast <fixture> --profile shell` |
| 正例 | `testdata/0.1.0/positive/` | `<是/否>` | `bash tools/check-0.1.0.sh --list` |
| 解析负例 | `testdata/0.1.0/negative/parse/` | `<是/否>` | `find testdata/0.1.0/negative/parse -name case.json \| wc -l` |
| AST golden | `testdata/0.1.0/expected/ast/` | `<是/否>` | `find testdata/0.1.0/expected/ast -name '*.json' \| wc -l` |

## 2. 退出判据逐条证据（卡片 §4）

| ID | 条件 | 命令 | 原始输出 / 退出码 | 结论 |
| --- | --- | --- | --- | --- |
| E-1 | 全部正例 AST golden 通过 | `bash tools/check-0.1.0.sh --kind ast --bucket positive` | `<贴原始输出>` | `<…>` |
| E-2 | 裸词在 value 位归约为字符串节点 | `bash tools/check-0.1.0.sh --show <case>` | `<贴原始输出>` | `<…>` |
| E-3 | 四类可归约（条件动词、调用实参、独立 `[into]`、`parallel`+`[results]`） | `bash tools/check-0.1.0.sh --kind ast --bucket positive` | `<贴四条 golden>` | `<…>` |
| E-4 | 四类解析负例有稳定错误码 | `bash tools/check-0.1.0.sh --bucket negative --kind error` | `<逐条 code/line/col>` | `<…>` |
| E-5 | 每个语句形态至少 1 个 AST golden | `bash tools/check-0.1.0.sh --list --kind ast` | `<贴输出>` | `<…>` |
| E-6 | 任务清单每项可独立验收（T-6） | 逐任务跑卡片 §3 的 `verify` | `<逐项贴输出>` | `<…>` |

## 3. 任务级红证与回滚（T-4 / T-7）

| 任务 | `test(...) 红` 提交 | 实现提交 | 红证 `baseline` | `git merge-base --is-ancestor` | 回滚验证 |
| --- | --- | --- | --- | --- | --- |
| `PH-3-T1` | `<sha>` | `<sha>` | `<sha>` | `<true/false>` | `git revert <sha>` 后其余任务门禁仍绿 |
| … | … | … | … | … | … |

## 4. issues 三去向

| issue id | 摘要 | 去向 | 理由 / 目标 |
| --- | --- | --- | --- |
| `<id>` | `<一句话>` | `<本 phase 修 / <PH-n> / 拒绝>` | `<理由；deferred 必须写目标 phase 或日期>` |

## 5. lessons（每条必须落地）

| lesson | landing | 落地位置 | 验证 |
| --- | --- | --- | --- |
| `<教训>` | `gate:<门禁>` / `spec:<节>` / `rejected:<理由>` | `<文件:行>` | `<命令或评审签字>` |

## 6. 版本与 tag 核对

| 项 | 期望 | 实际 | 结论 |
| --- | --- | --- | --- |
| `version-minor` | `3` | `<g1-phase-card 输出>` | `<…>` |
| 产品版本 | `0.3.0` | `<落点值>` | `<…>` |
| `PATCH` | 等于本 phase 的 fix 条目数 | `<n>` | `<…>` |
| tag 名 | `v0.3.0` | `<实际>` | `<…>` |
| annotated | `git cat-file -t v0.3.0` = `tag` | `<实际>` | `<…>` |
| 指向 | 收口提交 | `git rev-parse v0.3.0^{commit}` | `<…>` |
| 可追溯 | `git branch -r --contains <sha>` 非空 | `<实际>` | `<…>` |
| 推送 | `git push origin v0.3.0` 成功 | `<实际>` | `<…>` |

## 7. 门禁原始数字

```console
$ bash tools/check.sh all
<贴原始输出与 overall>
$ bash tools/check-0.1.0.sh --all
<贴原始输出与退出码>
```

## 8. 签字

| 角色 | 姓名 | 结论 | 日期 |
| --- | --- | --- | --- |
| EDITOR | `<name>` | `<收口 / 退回>` | `<date>` |
| VERIFY | `<name>` | `<红证认定>` | `<date>` |
| REVIEW | `<name>` | `<P0=0>` | `<date>` |
