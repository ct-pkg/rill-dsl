# S-018 命令与域名约束

- **状态**：`unverified`
- **决策**：[D-014](../decisions/D-014.md)
- **规范**：[06 §5.2](dsl/06-security.md)、[06 §5.3](dsl/06-security.md)
- **里程碑**：M8

## 1. 输入

命令：`["/usr/bin/git", "status"]`、`["/usr/bin/git", "status;rm -rf /"]`、`["git", "status"]`、`["/bin/sh", "-c", "rm -rf /"]`。
域名：`https://api.example.com/v1`、`https://api.example.com.evil.com/`、`https://user@api.example.com/`、`http://api.example.com/`、`https://api.example.com:443/`、`https://api.example.com/` 302 到 `http://evil.com/`。

## 2. 输出

- 命令：第一条允许；第二条把 `;rm` 当普通 argv 元素（不执行 shell），若约束不允许该参数则 `constraint`；第三条 `argv[0]` 非绝对路径 → `constraint`；第四条 `sh -c` 只在声明 `requires_approval` 的高危工具中允许。
- 域名：第一条允许；第二条后缀伪造 → `constraint`；第三条 userinfo → `constraint`；第四条非 https → `constraint`；第五条显式端口允许；第六条重定向跨 scheme → `constraint`。
- 永不使用 shell 解释字符串；不经 shell 展开通配符。

## 3. 失败语义

- 任意一条被错误放行 → 验收失败（安全缺陷）。
- 调用 `system()` 字符串拼接执行 → 验收失败（实现约束）。
- 重定向未逐跳复核 → 验收失败。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M8 后 `tools/check.sh m8-constraints`）。
- **阈值**：命令 4 例 + 域名 6 例逐条通过；shell 调用计数 0；重定向跳数上限生效。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 命令规则 | [06 §5.2](dsl/06-security.md) | 规范正文 |
| 域名规则 | [06 §5.3](dsl/06-security.md) | 规范正文 |
| CT 反例 | `Pkg.h.ct:695,701-721`（字符串 `system()` + `sh_quote`） | 源码事实 |
