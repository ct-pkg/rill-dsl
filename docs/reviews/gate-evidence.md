# 新增门禁的负例红证（PH-1…PH-12 卡片体系）

记录 `g1-phase-card`、`g8-phase-freeze`、`g8-version` 三条检查的负例原始输出。
证据在 `/tmp` 下的独立棚屋生成，不污染仓库；复现命令逐条给出。

## 1. `g1-phase-card` 负例

构造：`/tmp/rill-g1-probe/docs/phases/PH-7/card.md` 故意缺 `version-minor`、任务 `effort=L`、
退出判据只有 1 条且不含 T-6，并且唯一任务覆盖全部判据。

```console
$ ROOT=/tmp/rill-g1-probe python3 tools/checks/phase_card.py
FAIL  docs/phases/PH-7/card.md:3 缺必填项「version-minor」
FAIL  docs/phases/PH-7/card.md:29 退出判据未显式包含「任务清单每项可独立验收」
FAIL  docs/phases/PH-7/card.md:29 退出判据未标注「T-6」
FAIL  docs/phases/PH-7/card.md:29 退出判据少于 2 条，无法证明 phase 被切开
FAIL  docs/phases/PH-7/card.md:27 任务 PH-7-T1 的 effort='L' 非法（只允许 S/M，L 必须再拆）
FAIL  docs/phases/PH-7/card.md:27 任务 PH-7-T1 覆盖全部退出判据，违反 T-5（phase 未被切开）

check g1-phase-card: 0 passed, 6 failed, 0 warnings, 0 skipped
rc=1
```

正向：真实仓库 12 张卡全部通过（`check g1-phase-card: 24 passed, 0 failed`）。

## 2. `g8-phase-freeze` 负例

构造：`/tmp/rill-freeze-probe` 初始化 git；先提交卡片，再提交
`feat(x): PH-7-T1 实现`（不动卡片），随后在工作树修改退出判据。

```console
$ ROOT=/tmp/rill-freeze-probe python3 tools/checks/g8_phase_freeze.py
FAIL  docs/phases/PH-7/card.md:9 「退出判据」在首个实现提交 cc6fdef 之后被修改；要改只能关闭当前 phase 另开

check g8-phase-freeze: 0 passed, 1 failed, 0 warnings, 0 skipped
rc=1
```

正向：真实仓库当前无 `PH-<n>` 实现提交，12 张卡均为 `SKIP`（冻结窗口未打开），不伪造通过。

## 3. `g8-version` 负例

### 3.1 轻量 tag

构造：`/tmp/rill-version-probe` 有 `VERSION=0.7.0` 与已声明的版本落点，`git tag v0.7.0`
创建的是轻量 tag（无 message）。

```console
$ ROOT=/tmp/rill-version-probe python3 tools/checks/g8_version.py
FAIL  tag v0.7.0:1 不是 annotated tag（git cat-file -t != tag）
FAIL  tag v0.7.0:1 message 未含 PH-<n>
PASS  版本落点一致：0.7.0

check g8-version: 1 passed, 2 failed, 0 warnings, 0 skipped
rc=1
```

### 3.2 正确形态（防“只会红”）

构造：`/tmp/rill-version-ok`，`git tag -a v0.7.0 -m "PH-7 收口 <sha>"`。

```console
$ ROOT=/tmp/rill-version-ok python3 tools/checks/g8_version.py
PASS  tag v0.7.0：annotated、PH-7、指向 efaa70c 且可追溯
PASS  版本落点一致：0.7.0

check g8-version: 2 passed, 0 failed, 0 warnings, 0 skipped
rc=0
```

## 4. 真实仓库当前状态（基线）

```console
$ bash tools/check.sh g8
SKIP  PH-1 无实现提交，冻结窗口未打开
...（PH-2…PH-12 同）
check g8-phase-freeze: 0 passed, 0 failed, 0 warnings, 12 skipped
WARN  AGENTS.md:268 版本落点仍为「缺失…」；落点声明前只校验 tag，不校验落点一致性
SKIP  仓库当前 0 个 tag；phase 收口前无 tag 可校验（V-7 只在收口时生效）
check g8-version: 0 passed, 0 failed, 1 warnings, 1 skipped
== overall: PASS ==
```

## 5. 未覆盖项（如实登记）

- `g8-version` 未做 V-2…V-5 的提交级检查：PATCH 逐 fix 计数、纯文档提交不动版本号、
  同提交落点一致，都要等 `AGENTS.md` 版本落点声明后才能机械执行；当前由收口对照表人工核。
- `g8-phase-freeze` 只认 subject 为 `feat|fix` 且含 `PH-<n>` 的提交；若实现提交命名不符，
  检查会 `SKIP` 而不是误判为通过。收口对照表需贴 `git log --oneline` 佐证命名。
- `g1-phase-card` 的 T-5 采用“任务 `覆盖` 列不得等于全部退出判据”的机械近似；
  判据是否真的写死、是否可核对，仍需 REVIEW 逐条读卡。

## 6. DOC-S2 豁免与版本措辞（2026-11-15）

`doc_size.py` 新增 `WAIVED` 表后，必须证明“仍会红、豁免只对登记路径生效”。
构造：`ROOT=<tmp>`，先放一份 302 行 `README.md`（未登记），再放一份 301 行
`docs/RILL-0.1.0.md`（已登记）。

```console
$ ROOT=/tmp/probe python3 tools/checks/doc_size.py   # README 302 行
FAIL  README.md:1 302 行 > 300（DOC-S2）
WARN  豁免 docs/RILL-0.1.0.md：语言规范正文，0.1.x 只读；拆分会破坏 PH 卡与决策引用的稳定锚点
check doc-size: 0 passed, 1 failed, 1 warnings, 0 skipped
rc=1

$ ROOT=/tmp/probe python3 tools/checks/doc_size.py   # README 改回 1 行
PASS  1 份文档均在 300 行以内（含 AGENTS.md 剔除生成块）
WARN  豁免 docs/RILL-0.1.0.md：语言规范正文，0.1.x 只读；拆分会破坏 PH 卡与决策引用的稳定锚点
check doc-size: 1 passed, 0 failed, 1 warnings, 0 skipped
rc=0
```

`version_wording.py` 跳过 sha256 锁定的主规范副本后，仍对项目措辞报错：

```console
$ printf 'v9.9.9\n' > /tmp/probe/docs/spec/x.md
$ ROOT=/tmp/probe python3 tools/checks/version_wording.py
FAIL  docs/spec/x.md:1 出现未定义版本 'v9.9.9'（允许：v0.1、v0.12.0、v1.7.0、v1.9.0）
check version-wording: 0 passed, 1 failed, 0 warnings, 0 skipped
rc=1
```

真实仓库当前：`bash tools/check.sh all` → 0 FAIL，7 份豁免逐份 `WARN`。
