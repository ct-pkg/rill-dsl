'use strict';

const { scan } = require('./scanner');

// 把一个文档的扫描结果变成带 uri 的符号表。
function buildFileIndex(uri, text) {
  const result = scan(text);
  const tag = (entry) => ({
    name: entry.name,
    uri,
    line: entry.line,
    character: entry.character,
    length: entry.length,
  });
  return {
    uri,
    definitions: result.definitions.map(tag),
    calls: result.calls.map(tag),
    aborted: result.aborted,
  };
}

function within(entry, position) {
  if (entry.line !== position.line) {
    return false;
  }
  const start = entry.character;
  const end = entry.character + entry.length;
  return position.character >= start && position.character <= end;
}

// 光标落在函数名的字符串内容上时返回 {kind, name, ...}；否则 null。
function findNameAt(fileIndex, position) {
  const definition = fileIndex.definitions.find((entry) => within(entry, position));
  if (definition) {
    return Object.assign({ kind: 'definition' }, definition);
  }
  const call = fileIndex.calls.find((entry) => within(entry, position));
  if (call) {
    return Object.assign({ kind: 'call' }, call);
  }
  return null;
}

// 跨文件解析：同文件定义优先，其余按 uri 排序，保持结果稳定。
function resolveDefinitions(files, name, currentUri) {
  const found = [];
  const current = files.get(currentUri);
  if (current) {
    found.push(...current.definitions.filter((entry) => entry.name === name));
  }
  const keys = Array.from(files.keys()).filter((key) => key !== currentUri).sort();
  for (const key of keys) {
    const entry = files.get(key);
    found.push(...entry.definitions.filter((item) => item.name === name));
  }
  return dedupe(found);
}

// 引用/调用点：当前文件优先，其余按 uri 排序。
function collectCallSites(files, name, currentUri) {
  const found = [];
  const current = files.get(currentUri);
  if (current) {
    found.push(...current.calls.filter((entry) => entry.name === name));
  }
  const keys = Array.from(files.keys()).filter((key) => key !== currentUri).sort();
  for (const key of keys) {
    const entry = files.get(key);
    found.push(...entry.calls.filter((item) => item.name === name));
  }
  return dedupe(found);
}

function dedupe(entries) {
  const seen = new Set();
  const result = [];
  for (const entry of entries) {
    const key = `${entry.uri}|${entry.line}|${entry.character}|${entry.length}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    result.push(entry);
  }
  return result;
}

module.exports = {
  buildFileIndex,
  findNameAt,
  resolveDefinitions,
  collectCallSites,
};
