# 08 示例

> 规范版本 `v0.1 rev.1`；状态 `unverified`。五个示例都必须在 [02](02-grammar.md) 的文法下解析；解析要点逐条给出。

## 1. 示例 1：读 → 搜 → 条件写

```
# allow: read, grep, write

let content = read "src/main.c"
let matches = content |> grep "malloc"
if matches != null {
    write "report.txt" matches
}
```

解析要点：`content |> grep "malloc"` → `grep("malloc", content)`（R2 追加末尾）；`write "report.txt" matches` 两个空格实参。

## 2. 示例 2：into + `$`

```
# allow: read, json_parse, write

read "config.json" |> json_parse into {
    let port = $.server.port
    let host = $.server.host
    write "out.txt" $
}
```

解析要点：`into_stmt := expr "into" block`，其中 `expr` 是整条管道；`$` 在块内只读；`write "out.txt" $` 显式写 `$`，因为 `write` 不声明 `accepts_context`。

## 3. 示例 3：fn 复用（已改写法）

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

let a = find_issues "src/a.c"
let b = find_issues "src/b.c"
write "issues.txt" (a + b)
```

改动与原因：

| 改动 | 原因 |
| --- | --- |
| `find_issues("src/a.c")` → `find_issues "src/a.c"` | D-001/D-002：括号只分组；统一空格形态，避免示例教两套写法 |
| `write "issues.txt" a + b` → `write "issues.txt" (a + b)` | 旧写法在新文法下是 `write("issues.txt", a)` 再 `+ b`，会先调用再相加；加括号才是“把 `a + b` 作为一个实参” [D-002] |

## 4. 示例 4：emit 事件

```
# allow: read, grep
# emit: analysis_done

let matches = read "src/main.c" |> grep "malloc"
if matches != null {
    emit "analysis_done" { "file": "src/main.c", "count": matches.length }
}
```

解析要点：payload 是受限 JSON 字面量，`matches.length` 是 `json_array` 的内建字段（[03 §8](03-semantics.md)）；`"count": 3` 的旧写法改为真实长度，避免示例给出硬编码假数据。

## 5. 示例 5：嵌套 into（已改写法）

```
# allow: read, json_parse, write

read "pkg.json" |> json_parse into {
    let name = $.name
    $.dependencies into {
        let dep_count = $.length
        write "summary.txt" (name + ":" + dep_count)
    }
}
```

改动与原因：

| 改动 | 原因 |
| --- | --- |
| `write "summary.txt" name + ":" + dep_count` → `write "summary.txt" (name + ":" + dep_count)` | 同示例 3：不加括号会先调用 `write` 再相加 |
| `# allow:` 去掉未使用的 `get` | 示例只用到 `read`/`json_parse`/`write`；allow 列表应是实际调用集 |

解析要点：`into` 嵌套按 [provisional: P-010] 允许，内层 `$` 覆盖外层；`name + ":" + dep_count` 依赖字符串拼接规则（[03 §1](03-semantics.md)）。

## 6. 自证矩阵

| 示例 | 覆盖决策 | 覆盖文法点 | 验收条目 |
| --- | --- | --- | --- |
| 1 | D-001/D-002 | 空格实参、管道、if/块、隐式 await | S-001、S-002、S-004 |
| 2 | D-005、D-007 | into、`$`、管道 + into 组合 | S-005、S-007 |
| 3 | D-002、D-005、D-009 | fn、return、分组实参、函数调用 | S-002、S-005、S-010 |
| 4 | D-006、D-008 | emit payload、数组内建字段 | S-006、S-009 |
| 5 | D-006、D-009 | 嵌套 into、字符串拼接、数组 `.length` | S-006、S-011 |

说明：`provisional: P-010` 的嵌套 `into` 若被否决，示例 5 需改为单层 `into` 或改用 `fn`；改动只影响本示例与 [03 §7](03-semantics.md)。
