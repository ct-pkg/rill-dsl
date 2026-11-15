# RILL 样例

这里是可以**直接跑通**的 RILL 样例：每个 `.ri` 都配一份同名 `.md`，写清它演示什么能力、
需要知道哪条语法，并贴了实测输出。建议按编号从 01 跑到 17。

样例只使用当前实现真正支持的写法。清单来自 `ct/src/` 的 lexer / parser / loader / eval /
formatter 与 `testdata/0.1.0/` 的夹具，不是按规范想象出来的。

> 旧 `docs/examples/` 与 `docs/guides/dsl-tutorial/`（`v0.1 rev.1` 的 `let` / `# allow:`
> 那套语法，从未运行）已下线，两处只留一张迁移对照表指向本目录，避免两套语法并存。

## 1. 准备

```console
$ cd <repo>
$ bash ct/build.sh          # 需要 `ct` 工具链与一个 C 编译器
$ ls ct/bin/rill
$ cd examples/tour
```

下文所有命令都在 `examples/tour/` 下执行，所以脚本里的相对路径（`data/one.txt` 等）
正好落在当前目录。JSON 信封在 stdout，`send` 的文本在 stderr，退出码单独看。

## 2. 从第一个跑到最后一个

**A. 基础：一条句子怎么组成、管道怎么传值**

| # | 样例 | 一句话 | 跑法 |
| --- | --- | --- | --- |
| 01 | [send](tour/01-send.md) | 动词 `<send>` + 宾语 + `[to] user`，结果信封与 `host_meta` | `../../ct/bin/rill run 01-send.ri` |
| 02 | [pipe](tour/02-pipe.md) | `\|>` 段间只传 `value`，下游用 `$` 取到 | `../../ct/bin/rill run 02-pipe.ri` |
| 03 | [into-order](tour/03-into-order.md) | `[into]` 可叠加、按书写顺序执行、不改写段输出 | `../../ct/bin/rill run 03-into-order.ri` |
| 04 | [map](tour/04-map.md) | `//map{}` 值映射与动词映射（`` `cfg` `` / `<r>`） | `../../ct/bin/rill run 04-map.ri` |

**B. 控制流**

| # | 样例 | 一句话 | 跑法 |
| --- | --- | --- | --- |
| 05 | [if](tour/05-if.md) | `if` / `else-if` / `else`，truthy 规则，`if` 不产值 | `../../ct/bin/rill run 05-if.ri` |
| 06 | [each](tour/06-each.md) | `each` 遍历，`[ok]` 的 `$` 是按源序结果数组 | `../../ct/bin/rill run 06-each.ri --fakes fakes/each.json` |
| 07 | [break](tour/07-break.md) | `break <值>` 收口整个 program，后续语句不执行 | `../../ct/bin/rill run 07-break.ri` |
| 08 | [parallel](tour/08-parallel.md) | `parallel` 三态分支 + `[results]` 结果数组（含失败态） | `../../ct/bin/rill run 08-parallel.ri` |
| 09 | [fn](tour/09-fn.md) | `//fn{}` 定义、`@` 调用、尾部默认值、返回最后一句 | `../../ct/bin/rill run 09-fn.ri` |

**C. 错误路径与格式化**

| # | 样例 | 一句话 | 跑法 |
| --- | --- | --- | --- |
| 10 | [error-lex](tour/10-error-lex.md) | 词法错误：`{"error": ...}` 诊断 + 退出码 2 | `../../ct/bin/rill run 10-error-lex.ri` |
| 11 | [error-parse](tour/11-error-parse.md) | 解析错误：介词表外的 `[frobnicate]` | `../../ct/bin/rill run 11-error-parse.ri` |
| 12 | [error-run](tour/12-error-run.md) | 运行期失败：管道中断、下游不执行、退出码 1 | `../../ct/bin/rill run 12-error-run.ri` |
| 13 | [error-handled](tour/13-error-handled.md) | 有 `[error]` 继续 vs 没有就默认 break | `../../ct/bin/rill run 13-error-handled.ri` |
| 14 | [fmt](tour/14-fmt.md) | `fmt --compress` / `--display` 把代码变成什么 | `../../ct/bin/rill fmt --compress 14-fmt.ri` |

**D. 宿主与元数据**

| # | 样例 | 一句话 | 跑法 |
| --- | --- | --- | --- |
| 15 | [profile](tour/15-profile.md) | `--host-profile` 决定能不能写文件；拒绝是诊断不是失败 | `../../ct/bin/rill run 15-profile.ri --host-profile profiles/min.json` |
| 16 | [host-meta](tour/16-host-meta.md) | 成功与失败都带 `host_meta`，失败记 `host_error.code` | `RILL_TOUR_SET=demo ../../ct/bin/rill run 16-host-meta.ri` |

**E. 直接执行**

| # | 样例 | 一句话 | 跑法 |
| --- | --- | --- | --- |
| 17 | [shebang](tour/17-shebang.md) | 首行 `#!/usr/bin/env rill`，`chmod +x` 后直接跑；`fmt` 保留 shebang | `./17-shebang.ri` |

## 3. 怎么读输出

```console
$ ../../ct/bin/rill run 01-send.ri
hello, rill
{"ok":true,"value":"hello, rill","error":null,"host_meta":{"stdio":{"channel":"stderr","text":"hello, rill"}},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
```

- 第一行是 `send` 写到 stderr 的文本；第二行是 stdout 上的结果信封。
- `ok` / `value` / `error` 是语句结果；`host_meta` 是宿主旁路信息。
- `host.principal.name` 是本机 OS 用户名，换机器会变；其余字段与机器无关。

退出码（口径同 [README.md](../README.md) §5/§7、[known-limits](../docs/planning/rill-0.1.0-known-limits.md) §2、[acceptance](../docs/planning/rill-0.1.0-acceptance.md) §4）：

| 码 | 含义 |
| --- | --- |
| 0 | `ok=true`（含 `break` 收口）；**Agent 真实传输**的未处理失败也是 0，必须读 payload 的 `ok` |
| 1 | Shell / `--fakes`（含 Agent + `--fakes`）的未处理失败（`ok=false`） |
| 2 | 诊断：词法 / 解析 / 加载错误、CLI 参数错误、宿主能力被 profile 拒绝 |

harness 里出现的 `3`（BLOCK）是 SUT 适配层的"未实现"标记，不是 CLI 退出码。

## 4. 写样例时踩到的两个已知问题

样例本身都绕开了这两个写法，记在这里是为了不让下一个人把它们当成"能跑"。两条都已
单独记账到 [解析期缺陷登记](../docs/planning/rill-0.1.0-parser-defects.md)（PD-1 / PD-2），
含最小复现、实测输出与处理结论；修复不在样例这一摊，也不在本次提交里：

1. **引号串在前的相邻拼接解析失败**。`<send> "n="$x` 报 `E-PARSE-UNEXPECTED`：相邻判定
   的宽度按 token 文本长度算，没把两端引号算进去，于是下一个 token 被判成"不相邻"。
   变量在前的写法 `$x"n="` 正常。**已裁定走 A（修实现）**，但代码改动排在 PH-21 收口
   之后；在此之前不提供该写法的样例。
2. **`$"..."` 的宽度口径不一致**。`<send> $"-x"` 在内部对拍的 Python 侧能解析成
   `Self + String`，`ct/bin/rill` 侧报解析错误：`ct/src/parser/parser.h.ct` 的
   `p_raw_len` 对 `$` 多算了 1 列。因此这里不提供 `$` 后紧跟字符串的样例。

遇到这类问题按"记录现象、不改实现"处理：样例宁可少写一条，也不给一个跑不通的写法。
