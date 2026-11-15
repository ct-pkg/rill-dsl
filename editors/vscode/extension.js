'use strict';

const vscode = require('vscode');
const {
  buildFileIndex,
  findNameAt,
  resolveDefinitions,
  collectCallSites,
} = require('./lib/symbols');
const { WorkspaceIndex } = require('./lib/workspace-index');

const workspaceIndex = new WorkspaceIndex();

function toLocation(entry) {
  const range = new vscode.Range(
    entry.line,
    entry.character,
    entry.line,
    entry.character + entry.length,
  );
  return new vscode.Location(vscode.Uri.parse(entry.uri), range);
}

async function provideDefinition(document, position) {
  const local = buildFileIndex(document.uri.toString(), document.getText());
  const hit = findNameAt(local, position);
  if (!hit || hit.kind !== 'call') {
    return null;
  }
  try {
    const index = await workspaceIndex.getIndex();
    const targets = resolveDefinitions(
      index.files,
      hit.name,
      document.uri.toString(),
    );
    if (targets.length === 0) {
      return null;
    }
    return targets.map(toLocation);
  } catch (error) {
    console.error('[rill] definition failed:', error);
    return null;
  }
}

async function provideReferences(document, position, context) {
  const local = buildFileIndex(document.uri.toString(), document.getText());
  const hit = findNameAt(local, position);
  if (!hit) {
    return null;
  }
  try {
    const index = await workspaceIndex.getIndex();
    const locations = collectCallSites(
      index.files,
      hit.name,
      document.uri.toString(),
    ).map(toLocation);
    if (context && context.includeDeclaration) {
      locations.push(
        ...resolveDefinitions(index.files, hit.name, document.uri.toString()).map(
          toLocation,
        ),
      );
    }
    return locations;
  } catch (error) {
    console.error('[rill] references failed:', error);
    return null;
  }
}

function activate(context) {
  context.subscriptions.push(
    vscode.languages.registerDefinitionProvider(
      { language: 'rill' },
      { provideDefinition },
    ),
    vscode.languages.registerReferenceProvider(
      { language: 'rill' },
      { provideReferences },
    ),
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
