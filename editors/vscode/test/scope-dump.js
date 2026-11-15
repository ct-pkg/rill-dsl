'use strict';

// 用 VS Code 同款 vscode-textmate 逐 token 校验作用域。
// 依赖编辑器自带的 vscode-textmate / vscode-oniguruma；找不到时退出码 2（跳过）。

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', '..', '..');
const grammarPath = path.join(
  root,
  'editors/vscode/syntaxes/rill.tmLanguage.json',
);

const candidates = [
  process.env.RILL_TEXTMATE_ROOT,
  '/Applications/Trae CN.app/Contents/Resources/app/node_modules',
  '/Applications/Visual Studio Code.app/Contents/Resources/app/node_modules',
  '/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/node_modules',
].filter(Boolean);

function locateModules() {
  for (const base of candidates) {
    const textmate = path.join(base, 'vscode-textmate');
    const oniguruma = path.join(base, 'vscode-oniguruma');
    if (fs.existsSync(textmate) && fs.existsSync(oniguruma)) {
      return { textmate, oniguruma };
    }
  }
  return null;
}

const located = locateModules();
if (!located) {
  console.log(
    'SKIP 未找到 vscode-textmate/vscode-oniguruma；设置 RILL_TEXTMATE_ROOT 指向编辑器 node_modules 后重试',
  );
  process.exit(2);
}

const tm = require(located.textmate);
const onig = require(located.oniguruma);

const grammarJson = JSON.parse(fs.readFileSync(grammarPath, 'utf8'));
const scopeName = grammarJson.scopeName;
let grammar = null;
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

function tokenizeLines(lines) {
  const result = [];
  let stack = tm.INITIAL;
  for (const line of lines) {
    const tokenized = grammar.tokenizeLine(line, stack);
    result.push({ line, tokens: tokenized.tokens });
    stack = tokenized.ruleStack;
  }
  return result;
}

function expectScope(tokenized, lineIndex, fragment, scope, label) {
  const line = tokenized[lineIndex].line;
  const start = line.indexOf(fragment);
  if (start < 0) {
    fail(`${label}: 第 ${lineIndex + 1} 行找不到 ${JSON.stringify(fragment)}`);
    return;
  }
  const end = start + fragment.length;
  const candidatesInRange = tokenized[lineIndex].tokens.filter(
    (token) =>
      token.endIndex > start &&
      token.startIndex < end &&
      line.slice(token.startIndex, token.endIndex).trim(),
  );
  const hit = candidatesInRange.find((token) => token.scopes.includes(scope));
  const actual = candidatesInRange
    .map((token) => token.scopes[token.scopes.length - 1])
    .join(', ');
  ok(
    Boolean(hit),
    `${label}: ${JSON.stringify(fragment)} 应含 ${scope}，实际 ${actual || '(无 token)'}`,
  );
}

function expectAllScopes(tokenized, lineIndex, scope, label) {
  const line = tokenized[lineIndex].line;
  const tokens = tokenized[lineIndex].tokens.filter(
    (token) => line.slice(token.startIndex, token.endIndex).trim(),
  );
  const missing = tokens.filter((token) => !token.scopes.includes(scope));
  ok(
    tokens.length > 0 && missing.length === 0,
    `${label}: 第 ${lineIndex + 1} 行所有 token 应含 ${scope}，缺 ${missing.length} 个`,
  );
}

function expectNoScope(tokenized, lineIndex, scopes, label) {
  const line = tokenized[lineIndex].line;
  const hits = tokenized[lineIndex].tokens.filter(
    (token) =>
      line.slice(token.startIndex, token.endIndex).trim() &&
      token.scopes.some((scope) => scopes.includes(scope)),
  );
  ok(hits.length === 0, `${label}: 第 ${lineIndex + 1} 行不应出现代码作用域`);
}

function dump(tokenized, label) {
  console.log(`=== ${label}`);
  tokenized.forEach((item, index) => {
    console.log(`L${index + 1}: ${item.line}`);
    for (const token of item.tokens) {
      const text = item.line.slice(token.startIndex, token.endIndex);
      if (!text.trim()) {
        continue;
      }
      console.log(`  ${JSON.stringify(text)} -> ${token.scopes.join(' ')}`);
    }
  });
}

async function main() {
  const wasmCandidates = [
    path.join(located.oniguruma, 'release/onig.wasm'),
    path.join(located.oniguruma, 'onig.wasm'),
  ];
  const wasmPath = wasmCandidates.find((candidate) => fs.existsSync(candidate));
  if (!wasmPath) {
    console.log('SKIP 未找到 onig.wasm');
    process.exit(2);
  }
  const wasm = fs.readFileSync(wasmPath);
  await onig.loadWASM(
    wasm.buffer.slice(wasm.byteOffset, wasm.byteOffset + wasm.byteLength),
  );

  const registry = new tm.Registry({
    onigLib: Promise.resolve(onig),
    loadGrammar: async () =>
      tm.parseRawGrammar(JSON.stringify(grammarJson), grammarPath),
  });
  grammar = await registry.loadGrammar(scopeName);
  if (!grammar) {
    fail(`无法加载语法 ${scopeName}`);
    process.exit(1);
  }

  const fileNames = [
    'examples/tour/04-map.ri',
    'examples/tour/09-fn.ri',
    'examples/tour/06-each.ri',
  ];
  const tokenizedByFile = fileNames.map((fileName) =>
    tokenizeLines(
      fs.readFileSync(path.join(root, fileName), 'utf8').split(/\r?\n/),
    ),
  );
  tokenizedByFile.forEach((item, index) => dump(item, fileNames[index]));
  const tokenized = tokenizedByFile[0];
  const fnExample = tokenizedByFile[1];
  const eachExample = tokenizedByFile[2];

  // 词法把 //map{ ... } 识别为 MAP_HEADER + MAP_SHORT/MAP_LONG + RBRACE；
  // 高亮按用户口径把整段当区块注释灰显，内部不再嵌代码作用域。
  for (let lineIndex = 0; lineIndex < 4; lineIndex += 1) {
    expectAllScopes(
      tokenized,
      lineIndex,
      'comment.block.map.rill',
      'map 区块注释',
    );
    expectNoScope(
      tokenized,
      lineIndex,
      [
        'variable.other.mapping-key.rill',
        'variable.other.rill',
        'variable.other.identifier.rill',
        'keyword.operator.mapping-marker.rill',
        'string.quoted.other.mapping-reference.rill',
        'entity.name.function.verb.rill',
      ],
      'map 区块内不应当成代码上色',
    );
  }
  expectAllScopes(
    tokenized,
    4,
    'comment.line.double-slash.rill',
    '普通 // 行注释',
  );
  expectScope(tokenized, 5, '<r>', 'meta.verb.rill', '动词 <r>');
  expectScope(
    tokenized,
    5,
    '`cfg`',
    'string.quoted.other.mapping-reference.rill',
    '反引号引用',
  );
  expectScope(tokenized, 5, '|>', 'keyword.operator.pipe.rill', '管道');
  expectScope(tokenized, 5, '<send>', 'meta.verb.rill', '动词 <send>');
  expectScope(tokenized, 5, '$', 'variable.language.self.rill', '自身引用 $');
  expectScope(tokenized, 5, '[to]', 'support.type.preposition.rill', '介词 [to]');
  expectScope(
    tokenized,
    5,
    'user',
    'variable.other.identifier.rill',
    '裸词标识符',
  );

  // 09-fn：$ 后跟的名字是 VARIABLE；默认值/角色是 BARE。
  expectScope(
    fnExample,
    1,
    '$who',
    'variable.other.rill',
    '函数参数变量 $who',
  );
  expectScope(
    fnExample,
    1,
    'world',
    'variable.other.identifier.rill',
    '参数默认值裸词 world',
  );
  expectScope(
    fnExample,
    4,
    '$left',
    'variable.other.rill',
    '函数参数变量 $left',
  );
  expectScope(
    fnExample,
    4,
    '$right',
    'variable.other.rill',
    '函数参数变量 $right',
  );
  expectScope(
    fnExample,
    4,
    'right-default',
    'variable.other.identifier.rill',
    '参数默认值裸词 right-default',
  );

  // 06-each：循环绑定 $f 也是 VARIABLE，括号里的 data 是 BARE。
  expectScope(
    eachExample,
    3,
    '$f',
    'variable.other.rill',
    'each 绑定变量 $f',
  );
  expectScope(
    eachExample,
    3,
    'data',
    'variable.other.identifier.rill',
    '括号内裸词 data',
  );

  // 词法边界：//map 后没有 { 只到行尾；块内 { 只是长词数据，不嵌套；
  // 第一个行首 } 结束区块，同一行后面的内容恢复正文作用域。
  const boundaries = tokenizeLines([
    '//map',
    '<send> "still code" [to] user',
    '//map {',
    "a'{x",
    '}',
    '}',
    '// map{',
    "b'y",
    '} <send> "tail" [to] user',
  ]);
  expectAllScopes(
    boundaries,
    0,
    'comment.line.double-slash.rill',
    '//map 无花括号按行注释',
  );
  expectScope(boundaries, 1, '<send>', 'meta.verb.rill', '行注释后的正文');
  for (const lineIndex of [2, 3, 4]) {
    expectAllScopes(
      boundaries,
      lineIndex,
      'comment.block.map.rill',
      '带空格 header 与长词中的 {',
    );
  }
  expectNoScope(
    boundaries,
    5,
    ['comment.block.map.rill'],
    '第一个行首 } 已结束区块，第二个 } 不在注释里',
  );
  expectAllScopes(
    boundaries,
    6,
    'comment.block.map.rill',
    '// map{ 同样识别为区块',
  );
  expectScope(
    boundaries,
    8,
    '<send>',
    'meta.verb.rill',
    '同一行 } 后的内容恢复正文',
  );

  const extra = tokenizeLines([
    '[into] {',
    '[ok] $x {',
    '[error] {',
    '[results]',
    '<read> config.yml |> <parse> yaml',
  ]);
  expectScope(extra, 0, '[into]', 'keyword.control.block-marker.rill', '块标记 [into]');
  expectScope(extra, 1, '[ok]', 'keyword.control.block-marker.rill', '块标记 [ok]');
  expectScope(extra, 2, '[error]', 'keyword.control.block-marker.rill', '块标记 [error]');
  expectScope(
    extra,
    3,
    '[results]',
    'keyword.control.block-marker.rill',
    '块标记 [results]',
  );
  expectScope(extra, 4, 'config.yml', 'variable.other.identifier.rill', '裸词 config.yml');
  expectScope(extra, 4, '<parse>', 'meta.verb.rill', '动词 <parse>');

  // 函数区块内也要能吃到 common 的作用域。
  const fn = tokenizeLines([
    '//fn{',
    '@ "check" $path <read> $path {',
    '    <read> $path',
    '}',
    '}',
  ]);
  expectScope(
    fn,
    1,
    '"check"',
    'entity.name.function.definition.rill',
    '函数定义名',
  );
  expectScope(fn, 1, '$path', 'variable.other.rill', '函数参数变量');
  expectScope(fn, 1, '<read>', 'meta.verb.rill', '函数模板动词');
  expectScope(fn, 2, '<read>', 'meta.verb.rill', '函数体动词');

  console.log(`scopes: ${checks}, failed: ${failures}`);
  if (failures > 0) {
    process.exit(1);
  }
  console.log('PASS');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
