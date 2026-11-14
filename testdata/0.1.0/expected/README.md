# 期望产物格式（Phase 0 空壳）

当前只有两类 golden：

- `expected/ast/<用例相对路径>.json`：`ast` 用例的 AST 快照；
- `expected/tokens/<用例相对路径>.json`：`tokens` 用例的 token 快照。

`error` / `run` / `host-ast-equal` 的期望写在用例自己的 `case.json` 里，不落 golden：
错误只断言 stage/位置/错误码，运行只断言可观察结果，二者都不适合整树快照。

## 1. AST golden

```json
{
  "schema": "rill-ast-golden/0",
  "case": "positive/simple/read-write",
  "ast": {
    "kind": "Program",
    "body": []
  }
}
```

- `schema` 固定为 `rill-ast-golden/0`。
- `case` 必须等于用例相对路径（harness 会核对，防止把 golden 挂错用例）。
- `ast` 是编译器 `parse --dump-ast` 输出的 `ast` 字段原样，**唯一允许的归一化是去掉 `span` 键**。
- 比较的是解析后的 JSON 结构，不是文本：键顺序、缩进、换行不影响结果。
- 节点名词汇表尚未冻结（P2 决定）；本文件只冻结信封与归一化规则。

## 2. token golden

```json
{
  "schema": "rill-tokens-golden/0",
  "case": "positive/tokens/compact",
  "tokens": []
}
```

- token 保留位置信息（行/列）；这是 P1 的错误定位契约，不做 `span` 剥离。
- token 的 `kind` 词汇表由 P1 冻结，见 `docs/planning/rill-0.1.0-lexer.md` §3。

## 3. 缺失即 DRAFT

ast / tokens 用例没有 golden 文件时，harness 不报“用例非法”，而是把该用例标为 `DRAFT`，
并在汇总里单列。这样 Phase 0 的 `--list` 可以绿，而 `--all` 仍以退出码 3 明确表示
“还要实现或补 golden”，不会静默通过。

## 4. 生成与核对

golden 只能来自被测命令的实际输出，不允许手写语义、也不允许为了让用例变绿而改 golden。

1. `tools/check-0.1.0.sh --show <case>` 查看实际输出；
2. 把输出里的 `ast` / `tokens` 字段原样放进对应信封；
3. 逐节点人工核对是否符合 `docs/RILL-0.1.0.md`；
4. 再跑 `tools/check-0.1.0.sh --kind <ast|tokens>` 确认转绿。

语义有争议时先开 CR，不改 golden 迁就实现。
