'use strict';

const vscode = require('vscode');
const { buildFileIndex } = require('./symbols');

const EXCLUDE = '**/{.git,node_modules,.ctbuild,dist,out,build,.venv}/**';
const MAX_FILES = 5000;

class WorkspaceIndex {
  constructor() {
    this.cache = new Map();
    this.pending = null;
  }

  getIndex() {
    if (!this.pending) {
      this.pending = this._build().finally(() => {
        this.pending = null;
      });
    }
    return this.pending;
  }

  async _build() {
    const files = new Map();
    const seen = new Set();
    const open = new Map();
    for (const document of vscode.workspace.textDocuments) {
      if (document.languageId === 'rill') {
        open.set(document.uri.toString(), document);
      }
    }

    let uris = [];
    try {
      uris = await vscode.workspace.findFiles('**/*.rill', EXCLUDE, MAX_FILES);
    } catch (error) {
      console.error('[rill] findFiles failed:', error);
    }

    for (const uri of uris) {
      const key = uri.toString();
      if (seen.has(key)) {
        continue;
      }
      seen.add(key);
      const document = open.get(key);
      if (document) {
        files.set(key, buildFileIndex(key, document.getText()));
        continue;
      }
      const entry = await this._readCached(uri);
      if (entry) {
        files.set(key, entry);
      }
    }

    // 未保存的 RILL 文档（untitled 或不在 findFiles 结果内）也要参与当前文件解析。
    for (const [key, document] of open) {
      if (!files.has(key)) {
        files.set(key, buildFileIndex(key, document.getText()));
      }
    }

    for (const key of Array.from(this.cache.keys())) {
      if (!files.has(key)) {
        this.cache.delete(key);
      }
    }
    return { files };
  }

  async _readCached(uri) {
    const key = uri.toString();
    let stat;
    try {
      stat = await vscode.workspace.fs.stat(uri);
    } catch (error) {
      return null;
    }
    const cached = this.cache.get(key);
    if (cached && cached.mtime === stat.mtime && cached.size === stat.size) {
      return cached.entry;
    }
    try {
      const bytes = await vscode.workspace.fs.readFile(uri);
      const entry = buildFileIndex(key, Buffer.from(bytes).toString('utf8'));
      this.cache.set(key, { mtime: stat.mtime, size: stat.size, entry });
      return entry;
    } catch (error) {
      console.error('[rill] read failed:', key, error);
      return null;
    }
  }
}

module.exports = { WorkspaceIndex };
