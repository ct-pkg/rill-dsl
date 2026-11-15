# RILL DSL for VS Code

为 RILL 0.1.x 提供：

- `.ri` 语法高亮（关键字、动词、介词、字符串、变量、`//map{}`、`//fn{}`）；
- `F12` / `Ctrl+Click` 跳转到函数定义（支持跨文件工作区索引）；
- `Shift+F12` 查看函数的全部调用点。

选型理由、语法来源、已知局限见 [DESIGN.md](DESIGN.md)。

## 1. 安装（使用已打包的 .vsix）

仓库内已生成可离线安装的包：

```text
editors/vscode/dist/rill-dsl-0.1.2.vsix
```

VS Code 命令行安装：

```console
$ code --install-extension editors/vscode/dist/rill-dsl-0.1.2.vsix
$ # 安装后 Reload Window
```

图形界面安装：扩展视图右上角 `...` → **Install from VSIX...** → 选择上面的文件。
VS Code 兼容编辑器（如 Trae CN）同样走“从 VSIX 安装”。

> 文件关联与配色都写在扩展清单/语法文件里，**只重载窗口不会让已安装的旧版本生效**；
> 需要重新安装 0.1.2 的 VSIX，再 Reload Window。

安装不需要 node/npm；插件本身没有 npm 运行期依赖。

## 2. 试用跳转

用 VS Code 打开**仓库根目录**（这样工作区索引能扫到 `examples/` 下的全部 `.ri`）。

### 同文件

1. 打开 `examples/vscode/demo.ri`；
2. 把光标放到调用语句里的 `"greet-user"` 上（第 8 行）；
3. 按 `F12` 或 `Ctrl+Click`，应跳到 `//fn{}` 里的同名定义；
4. 在定义处按 `Shift+F12`，应列出调用点。

### 跨文件

1. 打开 `examples/vscode/cross-file/main.ri`；
2. 在 `"format-report"` 上按 `F12`，应跳到
   `examples/vscode/cross-file/shared.ri` 的定义；
3. 在未定义的函数名上按 `F12`，不应发生跳转。

> `cross-file/main.ri` 单独 `check` 会报“未声明的函数”：RILL 0.1.x 没有
> import/模块机制，跨文件只是编辑器的导航索引，不改变语言加载期语义。

## 3. 语法配色

插件自带四组默认 TextMate 颜色，不依赖当前主题碰巧覆盖这些作用域：

| 元素 | 示例 | 颜色 | 字重 |
| --- | --- | --- | --- |
| 注释 | `// 行注释`、`//map{ ... }` 区块 | 灰色 `#8B949E` | 常规 |
| 动词 | `<read>`、`<write>`、`<send>`、`<run>`、`<env>` | 蓝色 `#3B82F6` | 粗体 |
| 介词 | `[to]`、`[with]`、`[from]`、`[in]`、`[on]` | 紫色 `#BA68C8` | 常规 |
| 块标记 | `[into]`、`[ok]`、`[error]`、`[results]` | 橙色 `#EA580C` | 粗体 |

方括号 `[` `]` 本身保持主题标点色，只给括号内的词上色。深色主题下四组颜色
对比度均不低于 4.5:1；浅色主题下不低于 3.0:1（动词与块标记为粗体）。
`//map{ ... }` 从 header 到第一个行首 `}` 整段按 `comment.block.map.rill`
灰显，内部不再当代码上色；`//fn{ ... }` 仍是函数代码块，保留代码配色。

## 4. 重新打包

```console
$ cd editors/vscode
$ python3 tools/package_vsix.py
已生成 dist/rill-dsl-0.1.2.vsix
VSIX 校验通过：dist/rill-dsl-0.1.2.vsix（11 个条目，解压后 40152 字节）
```

只校验已有包：

```console
$ python3 tools/package_vsix.py --check dist/rill-dsl-0.1.2.vsix
```

## 5. 自测

```console
$ cd editors/vscode
$ bash test/run-tests.sh
oracle: 129 个文件对拍通过，10 个 lex 错误文件跳过
checks: 598, failed: 0
PASS

scopes: 34, failed: 0
PASS
```

测试优先用 `node`；本机没有 node 时会自动退到 Electron 的 Node 模式
（`/Applications/Trae CN.app`），也可用 `RILL_NODE=/path/to/node` 指定。

## 6. 目录

| 路径 | 作用 |
| --- | --- |
| `package.json` | 插件清单：语言、语法、激活事件 |
| `extension.js` | DefinitionProvider / ReferenceProvider 注册 |
| `lib/scanner.js` | 按 `src/rill/lexer.py` 复刻的函数符号扫描 |
| `lib/symbols.js` | 同文件/跨文件定义解析与调用点收集 |
| `lib/workspace-index.js` | 工作区 `.ri` 索引与 mtime 缓存 |
| `syntaxes/rill.tmLanguage.json` | TextMate 语法 |
| `language-configuration.json` | 注释、括号、自动闭合、缩进 |
| `test/oracle.py` | 用仓库 lexer/parser 产出对拍数据 |
| `test/run-tests.js` | 对拍 + 边界用例 + 清单/语法校验 |
| `tools/package_vsix.py` | 无 npm 依赖的 .vsix 打包与校验 |
