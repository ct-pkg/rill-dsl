'use strict';

const childProcess = require('child_process');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', '..', '..');
const { scan } = require('../lib/scanner');
const {
  buildFileIndex,
  findNameAt,
  resolveDefinitions,
  collectCallSites,
} = require('../lib/symbols');

let checks = 0;
let failures = 0;

function fail(message) {
  failures += 1;
  console.error('FAIL  ' + message);
}

function ok(condition, message) {
  checks += 1;
  if (!condition) {
    fail(message);
  }
}

function equal(actual, expected, message) {
  const left = JSON.stringify(actual);
  const right = JSON.stringify(expected);
  ok(left === right, `${message}\n  expected: ${right}\n  actual:   ${left}`);
}

function pick(entry) {
  return {
    name: entry.name,
    line: entry.line,
    character: entry.character,
    length: entry.length,
  };
}

function read(relative) {
  return fs.readFileSync(path.join(root, relative), 'utf8');
}

function uriOf(relative) {
  return 'file://' + path.join(root, relative);
}

// ---- 1. 与 Python lexer/parser 对拍 ---------------------------------
function runOracle() {
  const script = path.join(__dirname, 'oracle.py');
  const output = childProcess.execFileSync('python3', [script, root], {
    cwd: root,
    env: Object.assign({}, process.env, {
      PYTHONPATH: path.join(root, 'src'),
    }),
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
  });
  return JSON.parse(output);
}

const oracle = runOracle();
const workspace = new Map();
let compared = 0;
let skippedLexError = 0;

for (const relative of Object.keys(oracle.files)) {
  const expected = oracle.files[relative];
  const text = read(relative);
  const actual = scan(text);
  workspace.set(uriOf(relative), buildFileIndex(uriOf(relative), text));

  if (expected.lex_error) {
    skippedLexError += 1;
    continue;
  }

  compared += 1;
  equal(
    actual.definitions.map(pick),
    expected.definitions.map(pick),
    `${relative} 函数定义与 lexer token 流一致`,
  );
  equal(
    actual.calls.map(pick),
    expected.calls.map(pick),
    `${relative} 函数调用点与 lexer token 流一致`,
  );

  if (expected.ast) {
    ok(
      !expected.ast.definition_mismatch,
      `${relative} 定义列表与 parser AST 一致`,
    );
    ok(!expected.ast.call_mismatch, `${relative} 调用列表与 parser AST 一致`);
  }
}

// ---- 2. 跨文件解析用例 ----------------------------------------------
const demo = uriOf('examples/vscode/demo.rill');
const demoEntry = workspace.get(demo);
ok(Boolean(demoEntry), '示例 examples/vscode/demo.rill 已被索引');
if (demoEntry) {
  const call = demoEntry.calls.find((entry) => entry.name === 'greet-user');
  ok(Boolean(call), 'demo.rill 中存在 @ "greet-user" 调用点');
  if (call) {
    const hit = findNameAt(demoEntry, {
      line: call.line,
      character: call.character + 1,
    });
    ok(hit && hit.kind === 'call' && hit.name === 'greet-user', '调用点可定位到函数名');
  }
  const targets = resolveDefinitions(workspace, 'greet-user', demo);
  ok(targets.length === 1, '同文件 greet-user 定义只有一个候选');
  ok(targets.length === 1 && targets[0].uri === demo, '同文件调用解析到同文件定义');
  const sites = collectCallSites(workspace, 'greet-user', demo);
  ok(sites.length === 1, '同文件调用点只有一个');
}

const crossMain = uriOf('examples/vscode/cross-file/main.rill');
const crossShared = uriOf('examples/vscode/cross-file/shared.rill');
const crossTargets = resolveDefinitions(workspace, 'format-report', crossMain);
ok(crossTargets.length === 1, '跨文件 format-report 定义只有一个候选');
ok(
  crossTargets.length === 1 && crossTargets[0].uri === crossShared,
  '跨文件调用解析到 shared.rill 定义',
);
ok(
  resolveDefinitions(workspace, 'missing-function', crossMain).length === 0,
  '未定义函数不返回任何跳转目标',
);

// ---- 3. 扫描器边界用例 ----------------------------------------------
function inline(name, text) {
  return buildFileIndex('inmemory://' + name, text);
}

const sameFile = inline(
  'same-file',
  '//fn{\n@ "a" $x <read> $x {\n<read> $x\n}\n}\n@ "a" "f"\n',
);
equal(
  sameFile.definitions.map(pick),
  [{ name: 'a', line: 1, character: 3, length: 1 }],
  '同文件：定义位置只覆盖函数名内容',
);
equal(
  sameFile.calls.map(pick),
  [{ name: 'a', line: 5, character: 3, length: 1 }],
  '同文件：调用点位置只覆盖函数名内容',
);

const inComment = inline('comment', '// @ "ghost" "x"\n');
equal(inComment.calls, [], '注释里的 @ "name" 不算调用');
equal(inComment.definitions, [], '注释里的 @ "name" 不算定义');

const inString = inline('string', "<send> '@ \"ghost\"' [to] user\n");
equal(inString.calls, [], '字符串里的 @ "name" 不算调用');

const inMap = inline(
  'map',
  '//map{\nx\'@ "fake"\n}\n@ "real" "y"\n',
);
equal(inMap.calls.map((entry) => entry.name), ['real'], 'map 长词里的 @ 不算调用');

const spacedHeader = inline(
  'spaced-header',
  '// fn {\n@ "sp" $x <read> $x {\n<read> $x\n}\n}\n@ "sp" "y"\n',
);
equal(spacedHeader.definitions.map((entry) => entry.name), ['sp'], '// fn { 空格容忍');

const plainCommentHeader = inline('plain-header', '//fn\n@ "x" "y"\n');
equal(plainCommentHeader.definitions, [], '//fn 后没有 { 时仍是注释');
equal(plainCommentHeader.calls.map((entry) => entry.name), ['x'], '//fn 注释后的调用仍可识别');

const nestedAt = inline(
  'nested-at',
  '//fn{\n@ "outer" $x <read> $x {\n@ "inner" "z"\n}\n}\n',
);
equal(nestedAt.definitions.map((entry) => entry.name), ['outer'], '函数体内部的 @ 不登记为定义');
equal(nestedAt.calls, [], '函数体内部的 @ 不登记为调用');

const escapedName = inline(
  'escaped-name',
  '//fn{\n@ "a\\"b" $x <read> $x {\n<read> $x\n}\n}\n@ "a\\"b" "z"\n',
);
equal(escapedName.definitions.map((entry) => entry.name), ['a"b'], '双引号函数名按 lexer 规则解码');
equal(escapedName.calls.map((entry) => entry.name), ['a"b'], '双引号调用名按 lexer 规则解码');

const singleQuotedName = inline(
  'single-quoted-name',
  "//fn{\n@ 'single' $x <read> $x {\n<read> $x\n}\n}\n@ 'single' \"z\"\n",
);
equal(singleQuotedName.definitions.map((entry) => entry.name), ['single'], '单引号函数名可识别');
equal(singleQuotedName.calls.map((entry) => entry.name), ['single'], '单引号调用名可识别');

const unclosedString = scan('@ "oops\n@ "good" "x"\n');
equal(unclosedString.definitions, [], '未闭合字符串前没有定义');
equal(unclosedString.calls, [], '未闭合字符串后不再猜函数名');

const atThenNewline = scan('@\n"x"\n');
equal(atThenNewline.calls, [], '@ 与函数名跨行不构成调用');

const mapInsideFn = inline(
  'map-inside-fn',
  '//fn{\n@ "f" $x <read> $x {\n//map{\n<read> $x\n}\n}\n@ "f" "y"\n',
);
equal(mapInsideFn.definitions.map((entry) => entry.name), ['f'], '//fn 内的 //map{ 是注释');
equal(mapInsideFn.calls.map((entry) => entry.name), ['f'], '//fn 内注释不影响后续调用');

const headerInString = inline('header-in-string', "<send> '//fn{' [to] user\n@ \"x\" \"y\"\n");
equal(headerInString.definitions, [], '字符串里的 //fn{ 不开启区块');
equal(headerInString.calls.map((entry) => entry.name), ['x'], '字符串之后仍按正文扫描');

const headerInComment = inline('header-in-comment', '// //fn{\n@ "x" "y"\n');
equal(headerInComment.definitions, [], '注释里的 //fn{ 不开启区块');
equal(headerInComment.calls.map((entry) => entry.name), ['x'], '注释行之后仍按正文扫描');

// ---- 4. 插件清单与语法文件 ------------------------------------------
const packageJsonPath = path.join(__dirname, '..', 'package.json');
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
ok(packageJson.main === './extension.js', 'package.json main 指向 extension.js');
ok(fs.existsSync(path.join(__dirname, '..', 'extension.js')), 'extension.js 存在');
ok(packageJson.dependencies === undefined, '插件不依赖 npm 运行期包');

const language = packageJson.contributes.languages[0];
ok(language.id === 'rill', '语言 id 为 rill');
ok(language.extensions.includes('.rill'), '语言扩展名为 .rill');
ok(
  fs.existsSync(path.join(__dirname, '..', language.configuration)),
  'language-configuration.json 存在',
);
const grammarContribution = packageJson.contributes.grammars[0];
ok(grammarContribution.scopeName === 'source.rill', '文法语名为 source.rill');
const grammarPath = path.join(__dirname, '..', grammarContribution.path);
ok(fs.existsSync(grammarPath), 'TextMate 语法文件存在');
const grammar = JSON.parse(fs.readFileSync(grammarPath, 'utf8'));
ok(grammar.fileTypes.includes('rill'), '语法声明 .rill 文件类型');

function walkGrammar(node, visit) {
  if (Array.isArray(node)) {
    node.forEach((item) => walkGrammar(item, visit));
    return;
  }
  if (!node || typeof node !== 'object') {
    return;
  }
  visit(node);
  Object.keys(node).forEach((key) => walkGrammar(node[key], visit));
}

let regexCount = 0;
walkGrammar(grammar, (node) => {
  ['match', 'begin', 'end'].forEach((key) => {
    if (typeof node[key] === 'string') {
      regexCount += 1;
      try {
        new RegExp(node[key]);
      } catch (error) {
        fail(`语法正则无法编译（${key}=${node[key]}）：${error.message}`);
      }
    }
  });
  if (typeof node.include === 'string' && node.include.startsWith('#')) {
    const name = node.include.slice(1);
    ok(
      Object.prototype.hasOwnProperty.call(grammar.repository, name),
      `语法 include #${name} 在 repository 中存在`,
    );
  }
});
ok(regexCount >= 15, `语法包含足够多的匹配规则（实际 ${regexCount}）`);

// ---- 5. 扩展入口冒烟：用假 vscode 模块跑 activate --------------------
async function smokeExtension() {
  const Module = require('module');
  const registrations = [];
  class FakeRange {
    constructor(startLine, startCharacter, endLine, endCharacter) {
      this.start = { line: startLine, character: startCharacter };
      this.end = { line: endLine, character: endCharacter };
    }
  }
  class FakeLocation {
    constructor(uri, range) {
      this.uri = uri;
      this.range = range;
    }
  }
  const document = {
    uri: {
      scheme: 'file',
      toString: () => 'file:///tmp/rill-plugin-smoke.rill',
    },
    languageId: 'rill',
    version: 1,
    getText: () =>
      '//fn{\n@ "g" $x <read> $x {\n<read> $x\n}\n}\n@ "g" "y"\n',
  };
  const fakeVscode = {
    Range: FakeRange,
    Location: FakeLocation,
    Uri: {
      parse: (value) => ({ toString: () => value }),
    },
    languages: {
      registerDefinitionProvider(selector, provider) {
        registrations.push({ type: 'definition', selector, provider });
        return { dispose() {} };
      },
      registerReferenceProvider(selector, provider) {
        registrations.push({ type: 'references', selector, provider });
        return { dispose() {} };
      },
    },
    workspace: {
      textDocuments: [document],
      findFiles: async () => [],
      fs: {
        stat: async () => {
          throw new Error('not used in smoke test');
        },
        readFile: async () => {
          throw new Error('not used in smoke test');
        },
      },
    },
  };

  const originalLoad = Module._load;
  Module._load = function load(request) {
    if (request === 'vscode') {
      return fakeVscode;
    }
    return originalLoad.apply(this, arguments);
  };
  try {
    const extension = require('../extension.js');
    ok(typeof extension.activate === 'function', 'extension.js 导出 activate');
    extension.activate({ subscriptions: [] });
  } finally {
    Module._load = originalLoad;
  }

  ok(registrations.length === 2, 'activate 注册了定义与引用两个 Provider');
  const definition = registrations.find((item) => item.type === 'definition');
  const references = registrations.find((item) => item.type === 'references');
  ok(
    definition && definition.selector.language === 'rill',
    'DefinitionProvider 绑定 rill 语言',
  );
  if (definition) {
    const locations = await definition.provider.provideDefinition(document, {
      line: 5,
      character: 3,
    });
    ok(Array.isArray(locations) && locations.length === 1, '冒烟：调用点解析到一个定义');
    ok(
      Array.isArray(locations) &&
        locations.length === 1 &&
        locations[0].uri.toString() === document.uri.toString(),
      '冒烟：定义位置落在当前文档',
    );
  }
  if (references) {
    const locations = await references.provider.provideReferences(
      document,
      { line: 1, character: 3 },
      { includeDeclaration: true },
    );
    ok(Array.isArray(locations) && locations.length === 2, '冒烟：引用包含调用点与声明');
  }
}

// ---- 6. 汇总 --------------------------------------------------------
smokeExtension()
  .catch((error) => {
    fail('扩展入口冒烟异常：' + (error && error.stack ? error.stack : error));
  })
  .then(() => {
    console.log(
      `oracle: ${compared} 个文件对拍通过，${skippedLexError} 个 lex 错误文件跳过`,
    );
    console.log(`checks: ${checks}, failed: ${failures}`);
    if (failures > 0) {
      process.exit(1);
    }
    console.log('PASS');
  });
