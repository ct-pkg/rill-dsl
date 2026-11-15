/* bridge.h — 跨层类型别名（PH-20 两次 ct build 的边界，手写、非生成）
 *
 * 语言核心层（common/lexer/parser/loader/formatter）由 `ct build --lib` 编译成
 * librill_core.a，生成头把导出类型写成 `struct JVal` 这类带 tag 的拼写。
 * 宿主层不再 import 这些单元（否则会重复编译、g_fail_jmp 出现两份），只能在
 * C 侧补 typedef，让 ct 原样搬过去的 `JVal *` 仍是合法 C。
 *
 * 用法：宿主层单元写 `#include "bridge.h"`；构建时 `-I` 指到本目录与
 * `ct/build/gen-lib`。
 */
#ifndef RILL_BRIDGE_H
#define RILL_BRIDGE_H

#include "common.h"
#include "lexer.h"
#include "parser.h"
#include "loader.h"
#include "formatter.h"

typedef struct Diag Diag;
typedef struct JVal JVal;
typedef struct StdoutEmitter StdoutEmitter;
typedef struct Token Token;
typedef struct Lexer Lexer;
typedef struct MapPair MapPair;
typedef struct Parser Parser;
typedef struct FBuf FBuf;
typedef struct FLines FLines;
typedef struct FEntry FEntry;
typedef struct FEntries FEntries;
typedef struct FRev FRev;
typedef struct FUnit FUnit;
typedef struct FUnits FUnits;

#endif
