DSL 规范 v0.1

> 历史输入：本文是 v0.1 原文，保留不改写。规范正文已由 [docs/spec/dsl/](../spec/dsl/README.md) 的 `v0.1 rev.1` 承载；两者冲突时以新正文为准。

本文档定义 Agent 内核使用的工具编排 DSL。设计目标是用最少的 token 让 LLM 表达工具调用与流程编排，语法边界由内核严格控制，安全性由三层白名单保证。

---

1. 设计原则

1. 省 token 优先于语法完备。每个语法特性必须证明它能压缩 LLM 最常写的模式。
2. 复用 CT 已有语义：|> 管道、into scope、Vec/Map、own/Drop 直接映射，不重新发明。
3. 隐式规则少且可预测：只保留三条隐式规则——隐式 await、隐式管道传参、$ 指代 into 当前对象。
4. 错误信息给 LLM 看：位置（行列号）+ 原因 + 修正建议，三要素齐备。
5. DSL 语法轻，内核机制重：事件总线、状态快照、白名单引擎、调度器全部在内核，DSL 只暴露最薄的语句接口。

---

2. 词法规范

```
标识符    [a-zA-Z_][a-zA-Z0-9_]*        工具名、变量名、函数名、字段名
字符串    "..." 或 '...'                 转义 \n \t \" \\ \$
数字      -?[0-9]+(\.[0-9]+)?            整数、浮点
布尔      true / false
空值      null
管道      |>
赋值      =
当前对象  $
比较      == != < > <= >=
算术      + - * / %
逻辑      and or not
字段      .
索引      [ ]
注释      # 到行尾                       单行注释
块界定    { }                            if / for / into / fn 的作用域
```

刻意不引入：;、()（函数调用参数用空格分隔）、=>、链式方法调用、尾随 lambda。这些是 JS 里最占 token 的样板。

为什么用 {} 而不是缩进：缩进错误在 LLM 输出里极常见且难以定位；{} 能让 parser 精确报错“第 N 行缺少 }”。

---

3. 语法规范

3.1 程序结构

```
program     := header? statement*
header      := header_line*
header_line := ("# allow:" IDENT ("," IDENT)*)
             | ("# deny:"  IDENT ("," IDENT)*)
             | ("# emit:"  IDENT ("," IDENT)*)
```

头部元数据在脚本开头，可选。缺省时继承内核默认策略。

3.2 语句

```
statement   := let_stmt | if_stmt | for_stmt | into_stmt
             | fn_def | return_stmt | emit_stmt | expr_stmt

let_stmt    := "let" IDENT "=" expr
if_stmt     := "if" expr "{" statement* "}" ("else" "{" statement* "}")?
for_stmt    := "for" IDENT "in" expr "{" statement* "}"
into_stmt   := expr "into" "{" statement* "}"
fn_def      := "fn" IDENT "(" param_list? ")" "{" statement* "}"
param_list  := IDENT ("," IDENT)*
return_stmt := "return" expr?
emit_stmt   := "emit" STRING expr
expr_stmt   := expr
```

3.3 表达式

```
expr        := pipe_expr
pipe_expr   := or_expr ("|>" or_expr)*      # 唯一的数据流语法
or_expr     := and_expr ("or" and_expr)*
and_expr    := cmp_expr ("and" cmp_expr)*
cmp_expr    := add_expr (("=="|"!="|"<"|">"|"<="|">=") add_expr)?
add_expr    := mul_expr (("+"|"-") mul_expr)*
mul_expr    := unary_expr (("*"|"/"|"%") mul_expr)*
unary_expr  := ("not"|"-") unary_expr | postfix_expr
postfix_expr:= primary ("." IDENT | "[" expr "]" | "(" arg_list? ")")*
arg_list    := expr ("," expr)*
primary     := IDENT (" " arg)*             # 工具调用：name arg1 arg2
             | IDENT "(" arg_list? ")"      # 用户函数调用：f(a, b)
             | IDENT                        # 变量引用
             | STRING | NUMBER | BOOL | NULL | "$"
             | "(" expr ")"
arg         := primary
```

两种调用语法的区分：

· 工具调用：read "path"、grep "foo" "file" —— 参数空格分隔，最省 token。
· 用户函数调用：analyze_file("a.c") —— 括号 + 逗号，因为函数参数可能含复杂表达式，空格分隔会有歧义。

这条规则写进 few-shot，LLM 需要区分工具（空格）和函数（括号）。

---

4. 语义规则

R1：隐式 await

所有工具调用默认异步，DSL 不写 await。管道和变量绑定自动等待前一步完成。MVP 全串行，无并行语法。

R2：隐式管道传参

a |> f b c 等价于 f b c a——隐式参数追加到末尾。

```
read "src/main.c" |> grep "malloc" |> write "report.txt"
# 等价于：
# let r1 = read("src/main.c")
# let r2 = grep("malloc", r1)
# write("report.txt", r2)
```

R3：into 与 $

expr into { ... } 进入一个词法作用域，$ 指代 expr 的结果。

```
read "config.json" |> json_parse into {
    let port = $.server.port
    let host = $.server.host
    write "out.txt" $
}
```

$ 的规则：

· $ 在 into 块内只读，指向 into 的绑定值。
· 工具调用声明了 accepts_context: true 时，$ 自动作为隐式参数追加到参数列表末尾，不需要显式写。

```
read "config.json" into {
    get "server.port"           # 等价于 get("server.port", $)
    get "server.host"           # 等价于 get("server.host", $)
    write "out.txt" $           # 显式引用 $，因为 write 不声明 accepts_context
}
```

· 嵌套 into 时，内层 $ 覆盖外层，内层块结束后恢复外层 $。
· into 块外引用 $ 报编译期错误。

into 与 CT 的映射：DSL 的 into 直接复用 CT 的 into scope 语义和 $ 绑定，parser 和 scope resolution 共享同一套逻辑。

R4：错误传播

工具调用失败时，默认中止当前 block 并向上传播（类似 Rust ?）。if/for/into/fn 块内失败，整个块中止。MVP 不做 try/catch。

R5：类型

DSL 无类型注解。值是动态的：null / bool / number / string / json_object / json_array。工具 schema 做浅校验（参数个数、字符串/数字区分），不做深类型检查。

R6：fn 定义与调用

fn 定义用户函数，在脚本内复用：

```
fn analyze_file(path) {
    let content = read path
    let matches = content |> grep "malloc"
    if matches != null {
        return matches
    }
    return null
}

let result = analyze_file("src/main.c")
```

规则：

· 函数参数在函数内是局部变量，支持闭包读取外层变量（只读）。
· 函数内可以调用工具和管道。
· 函数无递归（避免栈溢出风险，MVP 不做）。
· 函数名与工具名共享命名空间，冲突时工具优先（内核注册的工具不可被脚本覆盖）。

R7：emit 事件（fire-and-forget）

emit "event_name" payload 把事件发送到内核事件总线，不阻塞、不等待、不关心监听方。

```
emit "file_analyzed" { "path": "src/main.c", "count": 3 }
```

语义：

· payload 在 emit 时序列化为 JSON 字符串（深拷贝），监听方拿到独立快照。
· 事件总线无监听方时，事件被丢弃并记日志，脚本不受影响。
· 总线队列满时丢弃并记日志（“通知”语义，失败不拖垮主流程）。
· 事件名必须在脚本头部 # emit: 列表中声明。

对象字面量：{ "key": value } 仅作为 emit 的 payload 语法糖，不作为通用表达式。其他场景需要构造 JSON 时，用 json_build 工具。

---

5. 三层白名单

5.1 第一层：注册表级（内核启动时确定）

只有注册进 DSL 可见 ToolRegistry 的工具，脚本才能调用。不在注册表的工具，脚本里写出来会报 unknown tool。

```ct
tool_registry_add(&dsl_reg, &read_tool);
tool_registry_add(&dsl_reg, &grep_tool);
tool_registry_add(&dsl_reg, &write_tool);
// delete_tool 不注册 → DSL 脚本无法调用
```

5.2 第二层：脚本级（脚本头部声明）

```
# allow: read, grep, write
# deny: http_post, exec
# emit: file_analyzed, task_done
```

· # allow: 缺省时继承注册表级白名单。
· 声明 # allow: 后，只有列表里的工具对脚本可见。
· # deny: 优先级高于 allow。
· # emit: 声明脚本能发的事件名，emit 未声明的事件加载时报错。

加载时校验：AST 里调用的工具 ⊆ allow 列表，AST 里 emit 的事件 ⊆ emit 列表。不通过则拒绝加载。

5.3 第三层：参数级（工具 schema 定义）

每个工具可声明参数约束，解释器在调用 handler 前检查：

```ct
ParamConstraint read_constraints[] = {
    { .param = "path", .type = CONSTRAINT_PATH_PREFIX, .value = "/workspace/" },
    { .param = "path", .type = CONSTRAINT_DENY_PATTERN, .value = "*.key" },
    { NULL }
};
```

约束类型：路径前缀、命令白名单、域名白名单、正则黑名单、数值范围。不通过则拒绝调用，handler 不执行。

5.4 三层关系

```
加载时：第一层（工具存在）+ 第二层（脚本有权用）+ 事件名合规
执行时：每次工具调用 → 第三层（参数合规）→ 调 handler
```

---

6. 内核接口

6.1 工具注册

```ct
struct ToolDef {
    char *name;
    char *description;         // 给 LLM 看的自然语言描述
    char *params_schema;       // JSON schema
    int   accepts_context;     // 是否接受 into 的 $ 作为隐式参数
    ParamConstraint *constraints;
    ToolResult (*handler)(char *args_json, char *ctx_json);
};
```

6.2 DSL 执行入口

```ct
struct DslResult {
    int   ok;
    char *value_json;          // 最后表达式的值
    char *error_msg;           // LLM 可读的错误信息
    int   error_line;
    int   error_col;
};

DslResult dsl_exec(char *source, int len, ToolRegistry *reg,
                   EventBus *bus, ExecLimits *limits);
```

6.3 执行限制

```ct
struct ExecLimits {
    int max_steps;             // 最大语句执行数
    int max_tool_calls;        // 最大工具调用次数
    int max_fn_depth;          // 最大函数嵌套深度
    int max_emit_count;        // 最大 emit 次数
    int max_output_bytes;      // 单次工具结果最大字节数
    int timeout_ms;            // 总超时
};
```

6.4 事件总线

```ct
struct EventSubscriber {
    char *event_pattern;       // "file_analyzed" / "task_*" / "*"
    void (*handler)(char *event_name, char *payload_json, void *ud);
    void *ud;
};

void event_bus_subscribe(EventBus *bus, EventSubscriber *sub);
void event_bus_publish(EventBus *bus, char *event_name, char *payload_json);
```

监听方可以是：C 函数（同步调用）、DSL 脚本（异步 dsl_exec，独立上下文）、外部 webhook。监听方注册由内核配置控制，不在 DSL 脚本里。

---

7. 完整语法骨架

```
program     := header? statement*
header      := ("# allow:" IDENT_LIST)?
               ("# deny:"  IDENT_LIST)?
               ("# emit:"  IDENT_LIST)?
IDENT_LIST  := IDENT ("," IDENT)*

statement   := let_stmt | if_stmt | for_stmt | into_stmt
             | fn_def | return_stmt | emit_stmt | expr_stmt

let_stmt    := "let" IDENT "=" expr
if_stmt     := "if" expr "{" statement* "}" ("else" "{" statement* "}")?
for_stmt    := "for" IDENT "in" expr "{" statement* "}"
into_stmt   := expr "into" "{" statement* "}"
fn_def      := "fn" IDENT "(" param_list? ")" "{" statement* "}"
return_stmt := "return" expr?
emit_stmt   := "emit" STRING expr

expr        := pipe_expr
pipe_expr   := or_expr ("|>" or_expr)*
or_expr     := and_expr ("or" and_expr)*
and_expr    := cmp_expr ("and" cmp_expr)*
cmp_expr    := add_expr (("=="|"!="|"<"|">"|"<="|">=") add_expr)?
add_expr    := mul_expr (("+"|"-") mul_expr)*
mul_expr    := unary_expr (("*"|"/"|"%") mul_expr)*
unary_expr  := ("not"|"-") unary_expr | postfix_expr
postfix_expr:= primary ("." IDENT | "[" expr "]" | "(" arg_list? ")")*
primary     := IDENT (" " arg)* | IDENT "(" arg_list? ")"
             | STRING | NUMBER | BOOL | NULL | "$" | "(" expr ")"
arg_list    := expr ("," expr)*
arg         := primary
```

---

8. 示例

示例 1：读→搜→条件写

```
# allow: read, grep, write

let content = read "src/main.c"
let matches = content |> grep "malloc"
if matches != null {
    write "report.txt" matches
}
```

示例 2：into + $

```
# allow: read, json_parse, get, write

read "config.json" |> json_parse into {
    let port = $.server.port
    let host = $.server.host
    write "out.txt" $
}
```

示例 3：fn 复用

```
# allow: read, grep, write

fn find_issues(path) {
    let content = read path
    let matches = content |> grep "TODO"
    if matches != null {
        return matches
    }
    return null
}

let a = find_issues("src/a.c")
let b = find_issues("src/b.c")
write "issues.txt" a + b
```

示例 4：emit 事件

```
# allow: read, grep
# emit: analysis_done

let matches = read "src/main.c" |> grep "malloc"
if matches != null {
    emit "analysis_done" { "file": "src/main.c", "count": 3 }
}
```

示例 5：嵌套 into

```
# allow: read, json_parse, get, write

read "pkg.json" |> json_parse into {
    let name = $.name
    $.dependencies into {
        let dep_count = $.length
        write "summary.txt" name + ":" + dep_count
    }
}
```

---

9. 明确不做的

· 类型系统：不做类型注解、不做类型推断。
· 模块/import：单文件脚本，不支持 import。
· 异常处理：MVP 不做 try/catch，错误直接冒泡。
· 并行：MVP 全串行，par { } 留关键字位置。
· 链式调用 / 尾随 lambda：管道是唯一数据流语法。
· 通用对象字面量：{ } 仅用于 emit payload 和块界定。
· 正则字面量：用字符串 + grep 工具处理。
· 递归：fn 不支持递归。
· 触发器/调度：由内核调度器配置，不进 DSL。

---

10. 与 CT 的映射

DSL 构造 CT 实现
工具调用 name args 查 ToolRegistry → 跑 ParamConstraint → 调 handler
管道 a |> f b 解释器求值 a，追加到 f 参数末尾
into { ... } + $ 复用 CT into scope 语义，$ 绑定到块内只读变量
fn 定义/调用 CT 函数 + 局部作用域
emit 序列化 payload → event_bus_publish
let / if / for CT 的 let / if / foreach
字段访问 x.a.b 调 ct-json 的 json_get，返回 borrow 或 null
错误传播 解释器维护 error 标志，失败跳到 block 末尾
白名单校验 加载时（第一、二层）+ 执行时（第三层）

---

11. 错误信息格式

加载时（工具不在 allow 列表）：

```
Error at line 5, col 10: tool 'write' is not allowed by script header.
  Allowed tools: read, grep
  Hint: add 'write' to '# allow:' or use an allowed tool.
```

加载时（emit 未声明）：

```
Error at line 8, col 5: event 'task_done' not declared in '# emit:'.
  Declared events: analysis_done
  Hint: add 'task_done' to '# emit:' header.
```

执行时（参数越界）：

```
Error at line 8, col 5: tool 'read' rejected path '/etc/passwd'.
  Constraint: path must start with '/workspace/'
  Hint: use a path under '/workspace/'.
```

执行时（$ 在 into 外使用）：

```
Error at line 3, col 10: '$' used outside 'into' block.
  Hint: wrap the expression in 'into { ... }' to bind '$'.
```

---

12. 实现优先级

阶段 内容 代码量 周期（AI 辅助）
M1 Lexer + Parser（工具调用、let、字符串/数字、字段访问） 1500 1–2 周
M2 Interpreter（工具调用、变量、错误传播、ExecLimits） 1400 1–2 周
M3 管道 + $ 隐式绑定 800 1 周
M4 if/for + {} 块 800 1 周
M5 into + $ 隐式参数注入 700 1–2 周
M6 fn 定义/调用 700 1 周
M7 emit + 事件总线接口 400 3–5 天
M8 三层白名单引擎 900 1–2 周
M9 错误报告（三要素） 700 1 周
合计  约 7900 行 2–3 个月

M1–M5 是核心闭环，跑通后即可用真实 LLM 任务验证。M6–M9 是完备性和安全性。

验证方法：M5 完成后，给 LLM 10 个真实任务（读文件、搜索、条件写、多文件处理、配置解析），统计 token 消耗和语法错误率。目标：token 比裸 JS 低 60% 以上、错误率低于 20%。否则根据错误模式调整语法。

---

13. 版本策略

· 向后兼容是硬约束：新语法增量添加，旧脚本不写新语法照常跑。
· 脚本可声明版本：# dsl-version: 2，内核按版本选解析器。MVP 可省略，设计留位置。
· 热更新：脚本文件监听 + 加载校验 + 原子替换 + 自动回滚。白名单配置热更新需人工审批或审计日志。

---

这份规范的取舍是：语法只覆盖“工具调用 + 数据流 + 条件 + 上下文 + 函数 + 事件”六件事，其余全部由内核机制兜底。管道和 $ 是 token 压缩的主力，但它们是“可选的快捷方式”——LLM 写不出来时可以退回 let + 显式参数，保证表达力下限。三层白名单是安全底线，不可省略。
