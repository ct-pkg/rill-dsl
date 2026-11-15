'use strict';

// RILL 0.1.x 的函数符号扫描器。
//
// 这里只复刻 src/rill/lexer.py 中与“找 @ "name"”有关的词法规则：
// 普通模式、//map{} 行模式、//fn{} 区块、注释、引号、动词、反引号引用。
// 不建 AST、不校验动词/介词；目的只是给出函数定义与调用点的原位信息。
//
// 与 lexer.py 的差异：
// - Python 的 col 按码点计数；VS Code 的 Position.character 按 UTF-16 码元计数。
//   这里用码元计数，位置可直接喂给 VS Code。
// - 遇到 lexer.py 会抛错的输入（未闭合引号/动词/反引号、非法双引号转义）时，
//   停止扫描并保留此前已确认的符号，避免把后续文本误判为函数名。

const WS = new Set([' ', '\t']);
const BARE_STOP = new Set('<>()[]{}|@?,"\'`$'.split(''));
const BARE_ESCAPABLE = new Set('[]()<>{}$\\'.split(''));
const NUMBER_RE = /-?[0-9]+/y;

function isAsciiAlnum(ch) {
  return (ch >= '0' && ch <= '9') || (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z');
}

function isShortChar(ch) {
  return isAsciiAlnum(ch) || ch === '_' || ch === '-';
}

function isIdentStart(ch) {
  return ch === '_' || (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z');
}

function isIdentChar(ch) {
  return ch === '_' || isAsciiAlnum(ch);
}

class Scanner {
  constructor(text) {
    this.src = String(text).replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    this.n = this.src.length;
    this.i = 0;
    this.line = 0;
    this.character = 0;
    this.prevChar = '';
    this.fnDepth = 0;
    this.mapMode = false;
    this.lastToken = null;
    this.definitions = [];
    this.calls = [];
    this.aborted = false;
  }

  peek(offset) {
    const index = this.i + (offset || 0);
    return index < this.n ? this.src[index] : '';
  }

  advance(count) {
    const steps = count === undefined ? 1 : count;
    for (let step = 0; step < steps && this.i < this.n; step += 1) {
      const ch = this.src[this.i];
      this.i += 1;
      this.prevChar = ch;
      if (ch === '\n') {
        this.line += 1;
        this.character = 0;
      } else {
        this.character += 1;
      }
    }
  }

  run() {
    while (this.i < this.n && !this.aborted) {
      if (this.mapMode) {
        this._lexMapLine();
      } else {
        this._lexNormal();
      }
    }
    return {
      definitions: this.definitions.slice(),
      calls: this.calls.slice(),
      aborted: this.aborted,
    };
  }

  _stop() {
    this.aborted = true;
    this.i = this.n;
    this.lastToken = null;
  }

  _wordishPrev() {
    const ch = this.prevChar;
    return Boolean(ch) && (isAsciiAlnum(ch) || '_-.:\'"`'.includes(ch));
  }

  _lexNormal() {
    const ch = this.peek();

    if (WS.has(ch)) {
      this.advance();
      return;
    }
    if (ch === '\n') {
      this.advance();
      this.lastToken = null;
      return;
    }
    if (ch === '/' && this.peek(1) === '/') {
      this._lexCommentOrHeader();
      return;
    }
    if ('()[]{}'.includes(ch)) {
      this.advance();
      if (this.fnDepth) {
        if (ch === '{') {
          this.fnDepth += 1;
        } else if (ch === '}') {
          this.fnDepth -= 1;
        }
      }
      this.lastToken = { kind: ch, line: this.line };
      return;
    }
    if (ch === '<') {
      this._lexVerb();
      return;
    }
    if (ch === '>') {
      this.advance();
      return;
    }
    if (ch === '-' && this.peek(1) === '>') {
      this.advance(2);
      this.lastToken = { kind: 'ARROW', line: this.line };
      return;
    }
    if (ch === '|' && this.peek(1) === '>') {
      this.advance(2);
      this.lastToken = { kind: 'PIPE', line: this.line };
      return;
    }
    if (ch === '@') {
      this.lastToken = { kind: 'AT', line: this.line };
      this.advance();
      return;
    }
    if (ch === '?' || ch === ',') {
      this.advance();
      this.lastToken = { kind: ch, line: this.line };
      return;
    }
    if (ch === '$') {
      this.advance();
      while (isIdentChar(this.peek())) {
        this.advance();
      }
      this.lastToken = { kind: 'DOLLAR', line: this.line };
      return;
    }
    if (ch === "'" || ch === '"') {
      this._lexString(ch);
      return;
    }
    if (ch === '`') {
      this._lexMapRef();
      return;
    }
    if (ch === '.' && isIdentStart(this.peek(1)) && !this._wordishPrev()) {
      this.advance();
      while (isIdentChar(this.peek())) {
        this.advance();
      }
      this.lastToken = { kind: 'FIELD', line: this.line };
      return;
    }
    if (!this._wordishPrev() && this._matchNumber()) {
      return;
    }
    this._lexBare();
  }

  _matchNumber() {
    NUMBER_RE.lastIndex = this.i;
    const match = NUMBER_RE.exec(this.src);
    if (!match) {
      return false;
    }
    const end = this.i + match[0].length;
    const next = this.src[end] || '';
    if (next && (isAsciiAlnum(next) || '_.:-'.includes(next) || next === '\\')) {
      return false;
    }
    this.advance(end - this.i);
    this.lastToken = { kind: 'NUMBER', line: this.line };
    return true;
  }

  _lexBare() {
    const start = this.i;
    const line = this.line;
    while (this.i < this.n) {
      const ch = this.peek();
      if (WS.has(ch) || ch === '\n') {
        break;
      }
      if (BARE_STOP.has(ch)) {
        break;
      }
      if (ch === '-' && this.peek(1) === '>') {
        break;
      }
      if (ch === '\\') {
        const next = this.peek(1);
        if (!next || !BARE_ESCAPABLE.has(next)) {
          this.advance();
          this._stop();
          return;
        }
        this.advance(2);
        continue;
      }
      this.advance();
    }
    if (this.i === start) {
      this.advance();
      this._stop();
      return;
    }
    this.lastToken = { kind: 'BARE', line };
  }

  _lexString(quote) {
    const previous = this.lastToken;
    const startLine = this.line;
    const startCharacter = this.character;
    this.advance();

    let decoded = '';
    let rawLength = 0;
    let closed = false;

    while (this.i < this.n) {
      const ch = this.peek();
      if (ch === '\n') {
        break;
      }
      if (ch === quote) {
        this.advance();
        closed = true;
        break;
      }
      if (quote === '"' && ch === '\\') {
        const next = this.peek(1);
        if (next !== '"' && next !== '\\') {
          this._stop();
          return;
        }
        decoded += next;
        rawLength += 2;
        this.advance(2);
        continue;
      }
      decoded += ch;
      rawLength += 1;
      this.advance();
    }

    if (!closed) {
      this._stop();
      return;
    }

    this.lastToken = { kind: 'STRING', line: startLine };

    if (!previous || previous.kind !== 'AT' || previous.line !== startLine) {
      return;
    }
    // `@ "name"`：//fn{} 顶层（depth 1）是定义，正文（depth 0）是调用；
    // 函数体内部（depth >= 2）的 @ 在 RILL 中非法，不登记，避免给出错误目标。
    if (this.fnDepth !== 0 && this.fnDepth !== 1) {
      return;
    }
    const entry = {
      name: decoded,
      line: startLine,
      character: startCharacter + 1,
      length: rawLength,
    };
    if (!decoded) {
      return;
    }
    if (this.fnDepth === 1) {
      this.definitions.push(entry);
    } else {
      this.calls.push(entry);
    }
  }

  _lexVerb() {
    this.advance();
    while (this.i < this.n && this.peek() !== '>' && this.peek() !== '\n') {
      this.advance();
    }
    if (this.i >= this.n || this.peek() === '\n') {
      this._stop();
      return;
    }
    this.advance();
    this.lastToken = { kind: 'VERB', line: this.line };
  }

  _lexMapRef() {
    this.advance();
    while (this.i < this.n && this.peek() !== '`' && this.peek() !== '\n') {
      this.advance();
    }
    if (this.i >= this.n || this.peek() === '\n') {
      this._stop();
      return;
    }
    this.advance();
    this.lastToken = { kind: 'MAP_REF', line: this.line };
  }

  _lexCommentOrHeader() {
    if (this.fnDepth) {
      // §4.18：//fn{} 内部不再产生区块头，`//` 一律是行注释。
      while (this.i < this.n && this.peek() !== '\n') {
        this.advance();
      }
      this.lastToken = null;
      return;
    }

    let probe = this.i + 2;
    while (probe < this.n && WS.has(this.src[probe])) {
      probe += 1;
    }

    let word = '';
    let brace = -1;
    for (const candidate of ['map', 'fn']) {
      if (this.src.startsWith(candidate, probe)) {
        let after = probe + candidate.length;
        while (after < this.n && WS.has(this.src[after])) {
          after += 1;
        }
        if (after < this.n && this.src[after] === '{') {
          word = candidate;
          brace = after;
          break;
        }
      }
    }

    if (word) {
      this.advance(brace + 1 - this.i);
      this.lastToken = null;
      if (word === 'map') {
        this.mapMode = true;
      } else {
        this.fnDepth = 1;
      }
      return;
    }

    while (this.i < this.n && this.peek() !== '\n') {
      this.advance();
    }
    this.lastToken = null;
  }

  _lexMapLine() {
    while (this.peek() && WS.has(this.peek())) {
      this.advance();
    }
    if (this.i >= this.n) {
      return;
    }
    if (this.peek() === '\n') {
      this.advance();
      this.lastToken = null;
      return;
    }
    if (this.peek() === '}') {
      this.advance();
      this.mapMode = false;
      this.lastToken = null;
      return;
    }

    const start = this.i;
    while (this.i < this.n && isShortChar(this.peek())) {
      this.advance();
    }
    if (this.i === start) {
      while (this.i < this.n && this.peek() !== '\n') {
        this.advance();
      }
      this.lastToken = null;
      return;
    }

    const marker = this.peek();
    if (marker !== "'" && marker !== '`' && marker !== '<') {
      while (this.i < this.n && this.peek() !== '\n') {
        this.advance();
      }
      this.lastToken = null;
      return;
    }
    this.advance();

    while (this.i < this.n && this.peek() !== '\n') {
      this.advance();
    }
    if (this.peek() === '\n') {
      this.advance();
    }
    this.lastToken = null;
  }
}

function scan(text) {
  return new Scanner(text).run();
}

module.exports = { scan };
