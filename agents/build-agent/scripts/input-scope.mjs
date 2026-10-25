// Specification inputs live outside generated source trees; no legacy fallback.
import fs from 'node:fs';
import path from 'node:path';
import {profiles} from './output-layout.mjs';

export function fixedInputFiles(project, profile) {
  return [
    'AGENTS.md', 'agents/README.md', 'agents/spec-agent/AGENT.md',
    'agents/build-agent/AGENT.md', 'agents/build-agent/PROMPT.md', 'agents/build-agent/README.md', 'agents/reverse-agent/AGENT.md',
    'docs/リポジトリ構成.md', 'docs/開発規約.md', 'docs/仕様書作成ルール.md',
    'docs/評価規約.md', 'docs/MD構造・Excel変換規約.md', 'docs/テーブル仕様書記述規約.md',
    'docs/テストデータ整備規約.md',
    ...(!profile || profile === 'Access' ? ['agents/build-agent/docs/Access生成チェック.md'] : []),
    `${project}/README.md`, `${project}/プロジェクト情報.md`, `${project}/docs/開発規約.md`,
  ];
}

export function assertRegular(target, directory = false) {
  const info = fs.lstatSync(target);
  if (info.isSymbolicLink() || fs.realpathSync(target).toLowerCase() !== path.resolve(target).toLowerCase() || (directory ? !info.isDirectory() : !info.isFile())) {
    throw new Error(`Not a regular ${directory ? 'directory' : 'file'}: ${target}`);
  }
}

export const specificationRoot = (root, project, profile) => path.join(root, project, 'spec', profile);

export function collectInputFiles(root, project, profile) {
  if (!/^test-project[1-9]\d*$/.test(project) || (profile !== undefined && !profiles.includes(profile))) throw new Error('Invalid input scope.');
  const files = [];
  function walk(directory) {
    assertRegular(directory, true);
    for (const entry of fs.readdirSync(directory, {withFileTypes: true}).sort((a, b) => a.name.localeCompare(b.name, 'en'))) {
      if (['spec-eval', 'spec-analysis', '.tmp', 'build', '.git'].includes(entry.name)) continue;
      const target = path.join(directory, entry.name);
      if (entry.isSymbolicLink()) throw new Error(`Symlink input is not allowed: ${target}`);
      if (entry.isDirectory()) walk(target);
      else if (/\.(md|html|json|png|jpe?g|gif|webp|svg)$/i.test(entry.name)) {assertRegular(target); files.push(target);}
    }
  }
  assertRegular(path.join(root, project), true);
  for (const name of fixedInputFiles(project, profile)) {const target = path.join(root, name); assertRegular(target); files.push(target);}
  if (profile) walk(specificationRoot(root, project, profile));
  else {
    // The project index is routing only. Do not collect arbitrary sibling trees.
    const index = path.join(root, project, 'spec', 'README.md');
    assertRegular(index); files.push(index);
    for (const method of profiles) walk(specificationRoot(root, project, method));
  }
  return files.sort();
}

export function independentSpecPrefix(file, project) {
  for (const method of profiles) {
    const prefix = `${project}/spec/${method}/`;
    if (file.startsWith(prefix)) return prefix;
  }
  return null;
}
