# RILL 样例

这里是可以**直接跑通**的 RILL 样例：每个 `.rill` 都配一份同名 `.md`，写清它演示什么能力、
需要知道哪条语法，并贴了实测输出。建议按编号从 01 跑到 16。

样例只使用当前实现真正支持的写法。清单来自 `ct/src/` 的 lexer / parser / loader / eval /
formatter 与 `testdata/0.1.0/` 的夹具，不是按规范想象出来的。

> 另有一套 `docs/examples/`，是 **实现之前**按 `v0.1 rev.1` 手工推导的评审稿（`let` / `fn` /
> `|?` / `# allow:` 那套旧语法），文件里自己标了 `unverified`。那一套和现在能跑的语言不是
> 一回事，请以本目录为准。

## 1. 准备

```console
$ cd <repo>
$ bash ct/build.sh          # 需要 ct-ast 主线 `ct`（v0.44.1+）与一个 C 编译器
$ ls ct/bin/rill_ct
$ cd examples/tour
```

下文所有命令都在 `examples/tour/` 下执行，所以脚本里的相对路径（`data/one.txt` 等）
正好落在当前目录。JSON 信封在 stdout，`send` 的文本在 stderr，退出码单独看。

## 2. 从第一个跑到最后一个

**A. 基础：一条句子怎么组成、管道怎么传值**

| # | 样例 | 一句话 | 跑法 |
| --- | --- | --- | --- |
| 01 | [send](tour/01-send.md) | 动词 `<send>` + 宾语 + `[to] user`，结果信封与 `host_meta` | `../../ct/bin/rill_ct run 01-send.rill` |
| 02 | [pipe](tour/02-pipe.md) | `\|>` 段间只传 `value`，下游用 `$` 取到 | `../../ct/bin/rill_ct run 02-pipe.rill` |
| 03 | [into-order](tour/03-into-order.md) | `[into]` 可叠加、按书写顺序执行、不改写段输出 | `../../ct/bin/rill_ct run 03-into-order.rill` |
| 04 | [map](tour/04-map.md) | `//map{}` 值映射与动词映射（`` `cfg` `` / `<r>`） | `../../ct/bin/rill_ct run 04-map.rill` |

**B. 控制流**

| # | 样例 | 一句话 | 跑法 |
| --- | --- | --- | --- |
| 05 | [if](tour/05-if.md) | `if` / `else-if` / `else`，truthy 规则，`if` 不产值 | `../../ct/bin/rill_ct run 05-if.rill` |
| 06 | [each](tour/06-each.md) | `each` 遍历，`[ok]` 的 `$` 是按源序结果数组 | `../../ct/bin/rill_ct run 06-each.rill --fakes fakes/each.json` |
| 07 | [break](tour/07-break.md) | `break <值>` 收口整个 program，后续语句不执行 | `../../ct/bin/rill_ct run 07-break.rill` |
| 08 | [parallel](tour/08-parallel.md) | `parallel` 三态分支 + `[results]` 结果数组（含失败态） | `../../ct/bin/rill_ct run 08-parallel.rill` |
| 09 | [fn](tour/09-fn.md) | `//fn{}` 定义、`@` 调用、尾部默认值、返回最后一句 | `../../ct/bin/rill_ct run 09-fn.rill` |

**C. 错误路径与格式化**

| # | 样例 | 一句话 | 跑法 |
| --- | --- | --- | --- |
| 10 | [error-lex](tour/10-error-lex.md) | 词法错误：`{"error": ...}` 诊断 + 退出码 2 | `../../ct/bin/rill_ct run 10-error-lex.rill` |
| 11 | [error-parse](tour/11-error-parse.md) | 解析错误：介词表外的 `[frobnicate]` | `../../ct/bin/rill_ct run 11-error-parse.rill` |
| 12 | [error-run](tour/12-error-run.md) | 运行期失败：管道中断、下游不执行、退出码 1 | `../../ct/bin/rill_ct run 12-error-run.rill` |
| 13 | [error-handled](tour/13-error-handled.md) | 有 `[error]` 继续 vs 没有就默认 break | `../../ct/bin/rill_ct run 13-error-handled.rill` |
| 14 | [fmt](tour/14-fmt.md) | `fmt --compress` / `--display` 把代码变成什么 | `../../ct/bin/rill_ct fmt --compress 14-fmt.rill` |

**D. 宿主与元数据**

| # | 样例 | 一句话 | 跑法 |
| --- | --- | --- | --- |
| 15 | [profile](tour/15-profile.md) | `--host-profile` 决定能不能写文件；拒绝是诊断不是失败 | `../../ct/bin/rill_ct run 15-profile.rill --host-profile profiles/min.json` |
| 16 | [host-meta](tour/16-host-meta.md) | 成功与失败都带 `host_meta`，失败记 `host_error.code` | `RILL_TOUR_SET=demo ../../ct/bin/rill_ct run 16-host-meta.rill` |

## 3. 怎么读输出

```console
$ ../../ct/bin/rill_ct run 01-send.rill
hello, rill
{"ok":true,"value":"hello, rill","error":null,"host_meta":{"stdio":{"channel":"stderr","text":"hello, rill"}},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
```

- 第一行是 `send` 写到 stderr 的文本；第二行是 stdout 上的结果信封。
- `ok` / `value` / `error` 是语句结果；`host_meta` 是宿主旁路信息。
- `host.principal.name` 是本机 OS 用户名，换机器会变；其余字段与机器无关。

退出码：

| 码 | 含义 |
| --- | --- |
| 0 | `ok=true`（含 `break` 收口） |
| 1 | 有未处理失败（`ok=false`） |
| 2 | 诊断：词法 / 解析 / 加载错误，或宿主能力被 profile 拒绝 |

## 4. 写样例时踩到的两个已知问题

样例本身都绕开了这两个写法，记在这里是为了不让下一个人把它们当成"能跑"：

1. **引号串在前的相邻拼接解析失败**。`<send> "n="$x` 报 `E-PARSE-UNEXPECTED`，Python
   参考实现与 CT 实现一致：相邻判定的宽度按 token 文本长度算，没把两端引号算进去，
   于是下一个 token 被判成"不相邻"。变量在前的写法 `$x"n="` 正常。样例里一律不用
   相邻拼接，要拼文本就分开写或者放进映射长词。
2. **`$"..."` 在 CT 与参考实现之间不一致**。`<send> $"-x"` 在 Python 参考实现里能解析
   成 `Self + String` 拼接，在 CT 实现里报解析错误：`ct/src/parser/parser.h.ct` 的
   `p_raw_len` 对 `$` 返回 `len("$") + 1`（多算 1 列），参考实现返回 1。因此这里不提供
   `$` 后紧跟字符串的样例。

遇到这类问题按"记录现象、不改实现"处理：样例宁可少写一条，也不给一个跑不通的写法。
