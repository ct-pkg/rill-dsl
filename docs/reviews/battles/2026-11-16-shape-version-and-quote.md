# 三席对抗存档：`shape_version` 落点与引号是否透明

| 项 | 值 |
| --- | --- |
| 日期 | 2026-11-16 |
| 议题 | P-025=B 之后的两项实现细节：① `shape_version` 放在哪里；② `file:x` 与 `"file:x"` 是否同值 |
| 参与席位 | 主张席、反证席、成本席 |
| 对应决策记录 | [D-024](../../decisions/D-024.md)（`upheld`，P-025=B） |
| 来源说明 | 2026-11-16 三席对抗会话（session `6af53a03cc783b31228d4c05`）的裁定建议原文，按用户要求原样落盘归档；只读分析，不含实现改动。D-024 已由提交 `35bd25e` 落盘，PH-23 卡由 `9b46740` 开卡。 |
| 状态 | 归档；D-024 已接受，PH-23 按 D-024 落地 |

---

## 一、先核事实

| 事项 | 事实 | 证据 |
| --- | --- | --- |
| `FnDef` 结构 | 字段是 `("shape", "template", "body")`，无 `name`、无任何版本字段 | [ast.py](file:///Users/samxx/trae-ws/rill-dsl/src/rill/ast.py#L19) |
| `shape` 结构 | `{verb, subject, object, preps[], adverbs[]}`；槽位为 `none/param/const(value)/value` | [shape.py](file:///Users/samxx/trae-ws/rill-dsl/src/rill/shape.py#L90-L104) |
| 谁生成 shape | Python 在解析期生成；CT 在 `p_parse_fn_def` 内同样生成 | [parser.py](file:///Users/samxx/trae-ws/rill-dsl/src/rill/parser.py#L472-L480)、[parser.h.ct](file:///Users/samxx/trae-ws/rill-dsl/ct/src/parser/parser.h.ct#L444-L471) |
| Python 加载表 | `LoadTables(maps, functions, verbs, profile)`，没有版本字段 | [loader.py](file:///Users/samxx/trae-ws/rill-dsl/src/rill/loader.py#L37-L44) |
| CT 加载表 | `load_shapes()` 用栈上 `FnList`，完成后丢弃，**没有可返回的加载表对象** | [loader.h.ct](file:///Users/samxx/trae-ws/rill-dsl/ct/src/loader/loader.h.ct#L270-L322) |
| 两侧如何共享 shape | 不是共享 schema，而是两份独立实现；靠 `diff.py` 的 AST 层逐字段对拍 | [shape.py](file:///Users/samxx/trae-ws/rill-dsl/src/rill/shape.py#L90-L104)、[common.h.ct](file:///Users/samxx/trae-ws/rill-dsl/ct/src/common/common.h.ct#L410-L433)、[diff.py](file:///Users/samxx/trae-ws/rill-dsl/tools/diff/diff.py#L164-L169) |
| 对拍比什么 | AST 层比“去掉 span 的完整 AST”；error 层只比 `stage/code/line/col` 与退出码；eval 层比 `ok/value/error/host_meta` | [diff.py](file:///Users/samxx/trae-ws/rill-dsl/tools/diff/diff.py#L389-L436) |
| golden 规模 | 51 份 AST golden；其中 **4 份含 `FnDef.shape`**：`basic`、`bareword-arg`、`shape-adverb`、`shape-prep-order`；另有 **2 份 run golden** 含轨迹 `shape`：`call-defaults`、`call-return-last` | [registry.md](file:///Users/samxx/trae-ws/rill-dsl/docs/reviews/diff/registry.md#L11-L19) |
| golden 重录方式 | 没有 `--record`；harness 只比较不写回。重录 = `--show`/`parse --dump-ast` 取输出，手写回 expected，再登记 registry | [cli.py](file:///Users/samxx/trae-ws/rill-dsl/tools/rill_harness/cli.py#L37-L54)、[runner.py](file:///Users/samxx/trae-ws/rill-dsl/tools/rill_harness/runner.py#L200-L226) |
| 编辑器 | `tmLanguage` 已匹配 `@ <verb>`；`scanner.js` 仍是旧 `@ "name"` 逻辑；两者都**不消费 AST 或 shape** | [test_editor_grammar.py](file:///Users/samxx/trae-ws/rill-dsl/tests/phase22/test_editor_grammar.py#L25-L35)、[scanner.js](file:///Users/samxx/trae-ws/rill-dsl/editors/vscode/lib/scanner.js#L280-L298) |

三个必须先说清的事实缺口：

1. **仓库里没有“签名键版本”的落点。** 只有 [D-022 L111](file:///Users/samxx/trae-ws/rill-dsl/docs/decisions/D-022.md#L108-L112) 一句条件句，以及 [PH-22 卡 E-26](file:///Users/samxx/trae-ws/rill-dsl/docs/phases/PH-22/card.md#L93)。没有字段、常量、测试、golden 或 CLI 输出消费它。
2. **D-022 的触发条件与 P-025=B 不完全对齐。** D-022 写的是“若 P-025 裁定类型前缀**参与**签名，签名键需递增版本”；B 是“**不**识别类型前缀”。但当前实现其实在签名层**剥离**了前缀：[shape.py](file:///Users/samxx/trae-ws/rill-dsl/src/rill/shape.py#L24-L36)、[common.h.ct](file:///Users/samxx/trae-ws/rill-dsl/ct/src/common/common.h.ct#L286-L298)。实测当前 `file:x`、`text:x`、`"file:x"` 三者的 `object.value` **都是 `"x"`**。所以 B 改变的是“现有实现口径”，不是 D-022 字面上的“类型前缀参与签名”。
3. **P-025=B 尚未落盘。** [PENDING.md L50](file:///Users/samxx/trae-ws/rill-dsl/docs/spec/PENDING.md#L50) 仍写 `pending`，[D-022 L147](file:///Users/samxx/trae-ws/rill-dsl/docs/decisions/D-022.md#L147) 也写 pending。签字前必须先补决策记录或更新 PENDING，否则“P-025 已裁定 B”在仓库里无证据。

另外，[PH-22 E-26 的测试](file:///Users/samxx/trae-ws/rill-dsl/tests/phase22/test_fn_shape_load.py#L56-L63) 断言 `file:x` 与 `text:x` 同形并报 `E-03`；B 下两者是不同常量值，该测试必红。PH-22 卡已收口，不能手改冻结卡面，只能以新决策/Issue 取代 E-26。

---

## 二、三席

### 主张席：版本应放进 `FnDef.shape`，钉在 AST 上

主张选 **①**，且只放**定义侧**：`FnDef.shape.shape_version = 2`，放在 `shape` 第一个键；调用侧形状不写版本。

理由不是“好看”，而是可核对面：

- AST 是 Python 与 CT **唯一共同产出、且已被对拍和 golden 消费**的工件。版本放这里，`--dump-ast` 直接可见，`diff.py --layer ast` 自动比对，4 份 FnDef golden 自动钉住；放加载表或模块常量都做不到这三件事。
- 每个 `FnDef` 一份，而不是每个 `FnBlock` 一份：E-05 已经防御“跨块合并/宿主注入”，逐定义带版本才能发现“同一表里混入旧版本形状”。
- 版本必须有消费者，否则就是装饰。消费者应放在 loader：收集 `FnDef` 时断言 `definition["shape"]["shape_version"] == SHAPE_VERSION`，不匹配报实现码 `E-LOAD-FN-SHAPE-VERSION`。这样宿主注入的旧形状不会静默参与匹配。
- 成本可接受：只影响 4 份 AST golden、1 条字段白名单测试、CT 的 `shape_of_call(..., 1)`；调用形状不带版本，所以 2 份 run golden 与 eval 轨迹不受影响。

可核对判据：

```bash
python3 -m rill parse --dump-ast <fn-fixture> --profile shell   # 定义侧含 shape_version=2，调用侧无
python3 tools/diff/diff.py --layer ast --filter fn              # 0 差异
grep -c '"shape_version": 2' testdata/0.1.0/expected/ast/positive/call/{basic,bareword-arg,shape-adverb,shape-prep-order}.json  # 4
```

### 反证席：版本若无人消费，加在哪里都是装饰；应把改动面压到最小

主张 **不把版本放进 AST**，最多放到加载期元数据或规范表；若必须留痕，用单点常量。

事实依据：

- 匹配逻辑从不读版本：`classify/find` 只看 `verb/subject/object/preps/adverbs`；`shape.describe` 不渲染版本；`eval_fn` 的轨迹用的是**调用形状**，不是 `FnDef.shape`。
- AST 不持久化，也没有跨版本读取路径。parser 与 loader 在同一次进程内完成，AST 不会以旧版本形态被新 loader 消费。版本在 AST 里没有运行时作用。
- 编辑器不消费 AST/shape；`diff.py` 是测试工具，不是运行时消费者。golden 是测试断言，不是生产消费者。
- 候选 **② 在 CT 侧事实上不成立**：CT 没有 `LoadTables`，`FnList` 是 `load_shapes()` 的栈变量，完成后丢弃；Python 的 `LoadTables` 也没有任何 CLI 序列化出口。所谓“加载期函数表元数据”在两侧不是同一个东西，无法对拍，也无法 grep。
- 真正的语义判据是行为夹具，不是版本号：`file:x` vs `text:x` 必须不同形，`file:x` vs `"file:x"` 必须同形。版本号无法自动发现语义漂移；加在 AST 只会让每个消费者永久多背一个字段。

因此：如果目标是“最小且不撒谎”，应选 **③：D-022/spec 里写一行 `shape_version = 2`，Python/CT 各一个 `SHAPE_VERSION` 常量，用两条行为夹具钉语义**。AST、golden、对拍、编辑器全部零改动。

### 成本席：逐项成本与将来反悔代价

| 选项 | golden 重录 | 双实现改动 | 对拍/编辑器 | 可观测性 | 将来移除 |
| --- | --- | --- | --- | --- | --- |
| ① `FnDef.shape` 内 | 4 份 AST golden；若调用侧也带版本再加 2 份 run golden | Python `shape.py` + CT `common.h.ct`；字段白名单测试；loader 断言 | `diff.py` 不改，但 AST 层自动纳入；编辑器 0 | `--dump-ast` 直接可见，golden/diff 可断言 | 再重录 4 份 + 再改白名单/CT |
| ② 加载表元数据 | 0 | Python `LoadTables` 加字段；CT 无对应表，只能退化成常量或新造表面 | 0 | **不可观测**：没有 CLI 输出加载表 | 低，但前提是它真的存在 |
| ③ 单点常量 + 规范行 | 0 | 两侧各一个常量；一条文本/单元测试比较 | 0 | 只能 grep 源码；不进 AST/diff | 一行即可 |

独立于版本字段，B 本身的成本：

- `test_type_prefix_does_not_change_shape` 必翻转；PH-22 E-26 需由新决策取代，不能静默改冻结卡面。
- 现有 FnDef golden 中没有带冒号的常量（我核对过 `basic`、`bareword-arg`、`shape-prep-order`），所以 B 本身**不需要重录 golden**，只改行为和测试。
- 若把“引号 vs 裸词”做成 `kind` 字段来区分 `file:x`/`"file:x"`，会连带让 `'ok'`/`"ok"`（String）与 `ok`（Bare）不同形，违反 D-022 与规范 §4.18 的常量同值规则；这是一次新的签名键语义变更，版本要再 +1。
- 双实现漂移：版本放 AST 时，`diff.py --layer ast` 会自动抓“一侧带、另一侧不带”；只放常量时，diff 抓不到，必须额外写一个读两份源码的文本测试，强度更弱。

---

## 三、裁定建议

### 问题一：选 ①，但必须带消费者

**裁定：`shape_version` 放进 `FnDef.shape`，作为第一个键，仅定义侧；调用侧不写。**

- 理由：AST 是两侧共同产出、且已有 golden 与 `diff.py` 消费的工件；① 让版本可被 `--dump-ast`、AST 对拍、golden 三处机械核对。② 在 CT 侧没有承载对象，事实上不成立；③ 的常量不进 AST，diff 抓不到漂移。
- 但反证席的条件成立：**必须有消费者**。否则退到 ③，不要在 AST 里加装饰字段。
- 消费者：loader 收集每个 `FnDef` 时断言版本等于当前 `SHAPE_VERSION`；不匹配报实现码 `E-LOAD-FN-SHAPE-VERSION`。这样宿主注入/合并的旧形状不能被静默匹配。
- 版本号定为 **2**：v1 = PH-22 收口时的“剥离类型前缀”实现口径；v2 = P-025=B 的“按 AST 字面原文”口径。不要定成 1，否则“相对上一版变化”没有记号。
- 调用侧不写版本的理由：调用形状由当前 parser 生成，恒为当前版本；写进去只会多改 2 份 run golden 和 eval 轨迹，换不到额外判据。若将来出现“宿主注入调用 AST”，再给调用侧加版本并升到 3。

可机械核对：

```bash
# 定义侧有、调用侧无
python3 -m rill parse --dump-ast <fixture> --profile shell | python3 -c '
import json,sys
ast=json.load(sys.stdin)["ast"]
defs=[d for h in ast["headers"] if h["kind"]=="FnBlock" for d in h["defs"]]
assert defs and all(d["shape"]["shape_version"]==2 for d in defs)
'
# 两侧一致
python3 tools/diff/diff.py --layer ast --filter fn
# golden 钉住
grep -c '"shape_version": 2' testdata/0.1.0/expected/ast/positive/call/{basic,bareword-arg,shape-adverb,shape-prep-order}.json
# 常量同值
grep -q 'SHAPE_VERSION = 2' src/rill/shape.py
grep -q 'SHAPE_VERSION 2' ct/src/common/common.h.ct
```

需要写进决策记录的字段：

| 字段 | 值 |
| --- | --- |
| `shape_version` | `2` |
| `v1` | PH-22 / 产品 0.22.0：常量位剥离 `类型:` 前缀（P-025 未裁定时的临时口径） |
| `v2` | P-025=B：常量位按 AST 字面原文，不查 TypeRegistry、不拆字段 |
| `landing` | `FnDef.shape.shape_version`（仅定义侧）；`src/rill/shape.py#SHAPE_VERSION`；`ct/src/common/common.h.ct#SHAPE_VERSION` |
| `consumer` | loader 版本断言（`E-LOAD-FN-SHAPE-VERSION`）+ AST 对拍 + 4 份 golden |
| `bump-trigger` | 形状键成分或常量比较口径变化 |
| `supersedes` | PH-22 E-26（`file:x`/`text:x` 同形的旧断言） |

### 问题二：接受同值，并在规范里写死

**裁定：`file:x` 与 `"file:x"` 同值，可接受，且必须写进规范。**

- B 下常量位比较的是 AST 里保存的字面量文本；`String.value` 与 `Bare.text` 都是 `"file:x"`，因此必然同值。
- 要区分二者，只能在常量槽里加节点种类（`kind`）。这会同时把 `'ok'`/`"ok"`（String）与 `ok`（Bare）分开，直接违反 D-022 与规范 §4.18 的“`'ok'`、`"ok"`、`ok` 同一个值”；若改为专门识别冒号，又等于把类型前缀解释重新引入签名层，违背 B。两条路都不可接受。
- 规范应补一句明确后果：引号只是词法形态，不参与签名；类型前缀在签名层不拆分，所以 `file:x` ≠ `text:x`。这句话把“为什么不是 bug”写死，避免后人用节点种类去“修”。

可机械核对：

```bash
# 同值：定义 file:x，调用 "file:x" → check 退出 0
# 不同值：同块定义 file:x 与 text:x → check 退出 0，且得到 2 个函数，不报 E-03
grep -q '类型前缀在签名层不拆分' docs/RILL-0.1.0.md
```

需要写进决策记录的字段：

| 字段 | 值 |
| --- | --- |
| `const_compare` | `ast_literal_text`（String.value / Bare.text / Number 的字符串形态） |
| `quote_transparent` | `true`；`file:x == "file:x"`，`'ok' == "ok" == ok` |
| `type_prefix_in_signature` | `false`；`file:x != text:x` |
| `node_kind_in_slot` | `false`（禁止用 String/Bare 区分常量） |
| `supersedes` | PH-22 E-26；同时更新 PENDING P-025 |
| `tests` | 同值正例、不同值正例、旧 E-26 测试翻转 |

### 签字前必须补的两件事

1. **把 P-025=B 落盘**：更新 [PENDING.md L50](file:///Users/samxx/trae-ws/rill-dsl/docs/spec/PENDING.md#L50)，新增决策记录（编号由 REQ 分配），否则本裁定引用的前提在仓库里不存在。
2. **以新条目取代 PH-22 E-26**：E-26 的现有测试断言 `file:x`/`text:x` 同形并报 `E-03`，与 B 直接冲突；PH-22 卡已收口，不能手改冻结卡面，应立 Issue/新 phase 卡登记“E-26 被 P-025=B 取代”，并翻转该测试。

本次只读分析，未修改任何文件。
