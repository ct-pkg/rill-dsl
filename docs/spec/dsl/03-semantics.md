# 03 语义

> 规范版本 `v0.1 rev.1`；状态 `unverified`。本卷对应旧文 §4 R1–R7 与 §9 的语义部分。

## 1. 值模型

值为以下六类之一：`null`、`bool`、`number`、`string`、`json_object`、`json_array`。

- `number` 为 IEEE-754 双精度；±2^53 内的整数按整数语义比较、格式化为无小数点形式。
- 对象与数组是值，不是引用：`let` 绑定、`for` item、`fn` 参数、`fn` 返回值一律值拷贝（深拷贝）。项目已有的“item 值拷贝”硬约束在此沿用。
- 相等：`null == null` 为 `true`；跨类型 `==` 为 `false`（不隐式转换）；对象/数组按结构化深比较。`<`/`>` 只接受 `number` 或 `string`，其他类型 → 运行时 `E_TYPE`。
- 算术：`+` 支持 `number + number`（加）、`string` 与任意标量的拼接（**任一侧**为 `string` 即可，另一侧可为 `string`/`number`/`bool`/`null`；`null` 渲染为 `"null"`，数字无多余零）、`json_array + json_array`（连接）；`-` `*` `/` `%` 只接受 `number`；其他组合 → 运行时 `E_TYPE` [D-016]。
- 真值：条件位置只接受 `bool`；非 `bool` → 运行时 `condition_not_bool`（值是动态的，加载期无法判定类型；示例中一律写显式比较）。

## 2. 名字解析

加载期建立三张表：工具名（内核注册表）、`fn` 名、局部绑定（参数、`let`、`for` 变量）。

- 调用 `IDENT arg+`：按工具 → `fn` 顺序解析；都不存在 → `E_UNKNOWN_TOOL`（加载期唯一失败点；Hint 同时提示检查工具名或函数名）。
- 裸 `IDENT`：若命中工具 → 零参调用；若命中零参 `fn` → 零参调用；若有参数的 `fn` → `E_BARE_FN_REF`（提示加实参）；否则是局部变量引用；都不存在 → `E_UNDEFINED_NAME`。
- **工具名保留**：局部绑定、参数、`fn` 名不得与已注册工具同名 → `E_SHADOW_TOOL` [D-005]。这条替代旧文 R6 的“冲突时工具优先”：冲突被提前到加载期，运行期没有优先级问题。
- 同一作用域内重复 `let` 同名 → `E_DUP_DECL`；内层块可以用 `let` 声明与外层同名的**新**绑定（遮蔽合法），但不得遮蔽工具名。

## 3. 绑定与赋值

- `let x = expr`：新建不可变绑定。
- `let mut x = expr`：新建可变绑定 [D-009]。
- `x = expr`：只允许写入**当前函数帧内已存在且为 `mut`** 的绑定。
  - 目标未定义 → `E_ASSIGN_UNDEFINED`（提示 `let x = ...` 或 `let mut x = ...`）。
  - 目标存在但不可变 → `E_IMMUTABLE_ASSIGN`（提示 `let mut`）。
  - 目标是参数、`for` 变量、闭包捕获变量或 `$` → `E_IMMUTABLE_ASSIGN`，错误文案分别说明原因。
  - 赋值是语句，不是表达式：`if x = 1`、`f (x = 1)` → `E_SYNTAX`（提示 `==`）。
- 赋值只存不建名；不存在隐式声明。

## 4. 条件与循环

- `if`：条件必须 `bool`；`else` 可省略；块内失败按 [04 §3](04-pipeline-errors.md) 中止块。
- `for IDENT in expr`：`expr` 必须是 `json_array`，否则 `E_FOR_NOT_ARRAY`；空数组执行 0 次。
- 循环变量是每轮的**不可变值拷贝**：写 `item = ...` → `E_IMMUTABLE_ASSIGN`；要改就 `let mut v = item` [D-009]。
- `break` 结束最近一层 `for`；`continue` 进入下一轮。二者只能出现在 `for` 块内（可嵌套在 `if` 里），出现在其他位置 → 加载期 `E_LOOP_CONTROL`；不能跨 `fn` 边界。
- **没有 `while`** [D-009]。轮询/等待由工具参数（`timeout`、`interval`）或内核重试承担。
- 计步：每次循环迭代至少计 1 步（空体亦然）；`continue` 不重置步数；`break` 正常结束。超过 `ExecLimits.max_steps` → `error_kind=limit`。

## 5. 函数

```
fn name(p1, p2) { ... }
```

- 参数在函数内是不可变局部绑定（值拷贝）；要改先 `let mut v = p1`。
- 闭包只读：函数体内可以读取外层绑定，不能赋值给外层绑定（`E_IMMUTABLE_ASSIGN`）。
- 无递归：加载期构建调用图，出现环（含自调用、互调用）→ `E_RECURSION`。
- 无重载；同一脚本内 `fn` 同名 → `E_DUP_DECL`。`fn` 名不得与工具同名（§2）。
- 调用实参个数必须等于形参个数 → 加载期 `E_ARITY`；`fn` 与固定 arity 工具同此规则，工具见 §6。
- 执行到函数体末尾没有 `return` → 返回 `null`；`return` 在 `fn` 外 → 加载期 `E_RETURN_OUTSIDE_FN`。`return e` 返回 `e` 的完整 `(payload, meta)`，不剥侧车。

## 6. 调用与隐式参数

- 工具调用把显式实参（书写序）与管道值序列化为 `args_json`（JSON 数组）；注入的 `$` 单独序列化为 `ctx_json`，未注入时为 NULL（两通道互斥，见 [07 §2](07-runtime.md)）。`fn` 调用按位置绑定。
- 管道值（[04 §1](04-pipeline-errors.md)）与隐式 `$` 的追加顺序：

```
最终实参 = 显式实参（书写序） ++ 管道值（若有） ++ 隐式 $（若注入）
```

- `$` 注入条件（三条同时满足）[D-007]：
  1. 当前位于 `into` 块内；
  2. 被调用工具声明 `accepts_context`（`fn` 永不注入）；
  3. 显式实参数 + 管道值个数 `n` 小于该工具的固定位置形参数 `m`（`n < m`）。
- 工具 schema 未声明固定 arity 或为变长 → **不注入**，必须显式写 `$`。
- 个数校验在加载期：显式实参 + 管道值 + 注入之后，个数与固定位置形参数不符 → `arity`，脚本不执行。个数由 `params_schema` 长度与注入规则静态可算，因此不进运行时第三层；运行时 `constraint` 只处理参数值。变长工具不做固定 `m` 校验；契约要求成对的工具（`json_build`）在加载期按偶数校验，奇数 → `arity`；其余逐位**值**校验由 handler 承担，失败归 `invalid_input`。
- `|?` 两侧各自独立计算注入；右侧不接收左侧管道值。
- `fn` 调用不注入 `$`，也不接收管道值以外的隐式参数；管道值对 `fn` 按普通追加实参处理。

## 7. into 与 `$`

- `expr into { ... }` 是**语句**，不是表达式：块的值被丢弃（即使块内最后一条是 `expr_stmt`），不能写 `let x = e into { ... }`。求值 `expr`，在块内把 `$` 绑定为该值；`$` 携带完整的 `(payload, meta)`。
- `$` 在块内只读；`$ = ...` → `E_IMMUTABLE_ASSIGN`；块外使用 `$` → 加载期 `E_DOLLAR_OUTSIDE`。
- `into` 允许嵌套；内层 `$` 覆盖外层，内层块结束后恢复外层 [D-017]。`$` 是环境帧里的词法绑定，不做编译期脱糖；CT 的嵌套禁令来自其脱糖实现，不适用于本解释器。
- `expr` 为 `null` 时仍可进入块，`$.x` 返回 `null`（不报错）；对 `null` 调用字段访问返回 `null`，便于缺省处理。

## 8. 字段、索引与内建字段

- `x.k`：`json_object` 取键，缺键返回 `null`；`json_array` 支持内建字段 `length` 与侧车伪字段 `truncated`/`original_size`；其他类型 → `null`（不报错）。
- `x[i]`：`json_array` 取第 `i` 个元素（0 基），越界返回 `null`；`json_object` 用 `x["k"]` 取键；其他类型返回 `null`。
- `length`：唯一内建字段，只挂在 `json_array` 上，返回元素个数（`number`）。`json_object`、`string`、`null` 及其他值访问 `.length` → `null`；`string` 长度由工具取 [D-016]。
- 空数组与 `null` 不等价：搜索类工具“无匹配”返回空数组（如 `grep` 返回 `[]`），不是 `null`；因此 `x != null` 对空数组恒真，判断有无结果必须写 `x.length > 0`。
- `x.length` 与 `$.length` 是同一条规则：`$.length` 只在 `$` 持有数组时成立，不是特殊语法；数组绑定给变量后写 `deps.length` 等价。
- 字段名可以是关键字之外的任意 `IDENT`；`x.if` 是语法错误。

## 9. 执行顺序与副作用

- MVP 全串行：每个工具调用完成后才继续（隐式 await，见 [04 §1](04-pipeline-errors.md)）。
- 求值顺序：函数/工具实参从左到右；比较与算术从左到右；`and`/`or` 短路。
- `|?` 不回滚已发生的副作用；补偿由工具提供。

## 10. 验收锚点

- [S-005](../S-005-parens-zero-arg.md)、[S-009](../S-009-truncation.md)、[S-010](../S-010-assignment.md)、[S-011](../S-011-loops.md)。
- 加载期检查清单：名字解析 5 类错误、赋值 4 类错误、循环控制 2 类、函数 4 类。
