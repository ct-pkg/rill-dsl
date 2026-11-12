# 文档 snippet 目录

> 目录状态：已建立，当前 **0 个 snippet**。这是如实状态，不是遗漏。
> 门禁：`tools/check.sh g4` 中的 `snippets.py` 校验准入字段；渲染/编译检查在 Phase 1 后启用。

## 1. 用途

文档里的可执行代码必须来自本目录，并由门禁渲染/校验（`AGENTS.md` §0.3、§0.6、§7.5、DOC-S7、G4 `g4-snippets`）。本目录是文档代码块的唯一来源；正文不得手写“示意代码”。

## 2. 准入条件（全部满足才可加入）

1. 语法已被决策记录支撑：对应 `docs/decisions/D-<n>.md` 存在且 `status: accepted`。
2. 该决策已进入 `docs/spec/dsl/` 正文，且示例形态不被任何 `pending` 条目影响。
3. 文件能被门禁实际渲染/执行，声明的输出可复现；不得只写“预期”。
4. 文件头 frontmatter 至少包含：

       ---
       decision: D-<n>
       status: verified
       source: <正文落点，file:section>
       ---

5. 不得把 `pending` 语法或 `docs/design/` 里的历史示例直接搬进来。

## 3. 为什么当前为空

- S-001..S-024 与 T-001..T-006 全部是 `unverified`；仓库没有 lexer/parser/解释器，验收命令统一写“尚未落盘”。
- `docs/design/dsl-spec-v0.1.md` 与 `dsl-discussion.md` 中的代码块是历史输入或待定语法，不满足准入条件 1–3。
- 现在填充示例会把未实现、未定稿的语法固化成事实，违反“每条行为陈述要么映射到门禁，要么标 `unverified`”。

## 4. 何时启用

M1 落地 lexer/parser 后，把 `docs/spec/dsl/08-examples.md` 中已定稿的示例迁入本目录，并在 `tools/check.sh g4` 接入 `g4-snippets` 的渲染/编译。命令存在前，本目录任何文件都不得标 `verified`。
