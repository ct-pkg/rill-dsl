# RILL DSL for VS Code

为 RILL 0.1.x 提供：

- `.rill` 语法高亮（关键字、动词、介词、字符串、变量、`//map{}`、`//fn{}`）；
- `F12` / `Ctrl+Click` 跳转到函数定义（支持跨文件工作区索引）；
- `Shift+F12` 查看函数的全部调用点。

选型理由、语法来源、已知局限见 [DESIGN.md](DESIGN.md)。

## 1. 安装（使用已打包的 .vsix）

仓库内已生成可离线安装的包：

```text
editors/vscode/dist/rill-dsl-0.1.0.vsix
```

VS Code 命令行安装：

```console
$ code --install-extension editors/vscode/dist/rill-dsl-0.1.0.vsix
$ # 安装后 Reload Window
```

图形界面安装：扩展视图右上角 `...` → **Install from VSIX...** → 选择上面的文件。
VS Code 兼容编辑器（如 Trae CN）同样走“从 VSIX 安装”。

安装不需要 node/npm；插件本身没有 npm 运行期依赖。

## 2. 试用跳转

用 VS Code 打开**仓库根目录**（这样工作区索引能扫到 `examples/` 下的全部 `.rill`）。

### 同文件

1. 打开 `examples/vscode/demo.rill`；
2. 把光标放到调用语句里的 `"greet-user"` 上（第 8 行）；
3. 按 `F12` 或 `Ctrl+Click`，应跳到 `//fn{}` 里的同名定义；
4. 在定义处按 `Shift+F12`，应列出调用点。

### 跨文件

1. 打开 `examples/vscode/cross-file/main.rill`；
2. 在 `"format-report"` 上按 `F12`，应跳到
   `examples/vscode/cross-file/shared.rill` 的定义；
3. 在未定义的函数名上按 `F12`，不应发生跳转。

> `cross-file/main.rill` 单独 `check` 会报“未声明的函数”：RILL 0.1.x 没有
> import/模块机制，跨文件只是编辑器的导航索引，不改变语言加载期语义。

## 3. 重新打包

```console
$ cd editors/vscode
$ python3 tools/package_vsix.py
已生成 dist/rill-dsl-0.1.0.vsix
VSIX 校验通过：dist/rill-dsl-0.1.0.vsix（11 个条目，解压后 35783 字节）
```

只校验已有包：

```console
$ python3 tools/package_vsix.py --check dist/rill-dsl-0.1.0.vsix
```

## 4. 自测

```console
$ cd editors/vscode
$ bash test/run-tests.sh
oracle: 128 个文件对拍通过，10 个 lex 错误文件跳过
checks: 550, failed: 0
PASS
```

测试优先用 `node`；本机没有 node 时会自动退到 Electron 的 Node 模式
（`/Applications/Trae CN.app`），也可用 `RILL_NODE=/path/to/node` 指定。

## 5. 目录

| 路径 | 作用 |
| --- | --- |
| `package.json` | 插件清单：语言、语法、激活事件 |
| `extension.js` | DefinitionProvider / ReferenceProvider 注册 |
| `lib/scanner.js` | 按 `src/rill/lexer.py` 复刻的函数符号扫描 |
| `lib/symbols.js` | 同文件/跨文件定义解析与调用点收集 |
| `lib/workspace-index.js` | 工作区 `.rill` 索引与 mtime 缓存 |
| `syntaxes/rill.tmLanguage.json` | TextMate 语法 |
| `language-configuration.json` | 注释、括号、自动闭合、缩进 |
| `test/oracle.py` | 用仓库 lexer/parser 产出对拍数据 |
| `test/run-tests.js` | 对拍 + 边界用例 + 清单/语法校验 |
| `tools/package_vsix.py` | 无 npm 依赖的 .vsix 打包与校验 |
