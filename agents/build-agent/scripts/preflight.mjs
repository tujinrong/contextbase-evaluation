// AG-BUILD: dependency-free, read-only input inspection; writes project/report only.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const args = process.argv.slice(2);
const profiles = ['VB.NET_WinForms', 'CSharp_WPF', 'CSharp_ASPNET', 'Vue_CSharpAPI', 'COBOL', 'AS400_RPG', 'Access'];
let project, runId, profile;
if (args.length % 2) throw new Error('Every option requires a value.');
for (let i = 0; i < args.length; i += 2) {
  if (args[i] === '--project' && !project) project = args[i + 1];
  else if (args[i] === '--run-id' && !runId) runId = args[i + 1];
  else if (args[i] === '--profile' && !profile) profile = args[i + 1];
  else throw new Error('Usage: preflight.mjs --project test-projectN --run-id <unique-id> [--profile <profile-id>]');
}
if (!/^test-project[1-9]\d*$/.test(project ?? '') || !/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(runId ?? '') || (profile !== undefined && !profiles.includes(profile))) {
  throw new Error('Explicit project and safe unique run-id are required.');
}
const projectRoot = path.join(root, project);
const reportRoot = path.join(projectRoot, 'report');
function assertRegular(target, directory = false) {
  const info = fs.lstatSync(target);
  if (info.isSymbolicLink() || (directory ? !info.isDirectory() : !info.isFile())) {
    throw new Error(`Not a regular ${directory ? 'directory' : 'file'}: ${target}`);
  }
}
assertRegular(projectRoot, true);
if (fs.existsSync(reportRoot)) assertRegular(reportRoot, true);
for (const name of [`${runId}-inputs.json`, `${runId}-structure.json`, `${runId}-structure.md`]) {
  if (fs.existsSync(path.join(reportRoot, name))) throw new Error(`Run-id already used: ${runId}`);
}
const relative = target => path.relative(root, target).split(path.sep).join('/');
const files = [];
function walk(directory) {
  assertRegular(directory, true);
  for (const entry of fs.readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name, 'en'))) {
    const target = path.join(directory, entry.name);
    if (entry.name === 'spec-eval') continue;
    if (entry.isSymbolicLink()) throw new Error(`Symlink input is not allowed: ${target}`);
    if (entry.isDirectory()) walk(target);
    else if (/\.(md|html|json|png|jpe?g|gif|webp|svg)$/i.test(entry.name)) { assertRegular(target); files.push(target); }
  }
}
const fixed = [
  'AGENTS.md', 'agents/README.md', 'agents/spec-agent/AGENT.md',
  'agents/build-agent/AGENT.md', 'agents/build-agent/PROMPT.md', 'agents/build-agent/README.md', 'agents/reverse-agent/AGENT.md',
  'docs/リポジトリ構成.md', 'docs/開発規約.md', 'docs/仕様書作成ルール.md',
  'docs/評価規約.md', 'docs/MD構造・Excel変換規約.md', 'docs/テーブル仕様書記述規約.md',
  `${project}/README.md`, `${project}/プロジェクト情報.md`, `${project}/docs/開発規約.md`,
];
for (const name of fixed) { const target = path.join(root, name); assertRegular(target); files.push(target); }
const selectedSpecPrefix = profile ? `${project}/srcs/${profile}/spec/` : null;
if (profile) {
  // An independent profile is the complete business input; do not inspect peers.
  walk(path.join(projectRoot, 'srcs', profile, 'spec'));
} else {
  walk(path.join(projectRoot, 'docs/開発規約'));
  walk(path.join(projectRoot, 'spec'));
  for (const isolatedProfile of profiles) {
    const localSpec = path.join(projectRoot, 'srcs', isolatedProfile, 'spec');
    if (fs.existsSync(localSpec)) walk(localSpec);
  }
}
const findings = [], records = [], ids = new Map();
const add = (file, line, code, detail) => findings.push({ file, line, code, detail });
function visibleLines(text) {
  let fence;
  return text.split(/\r?\n/).map((text, index) => {
    const marker = text.match(/^\s*(`{3,}|~{3,})/);
    if (marker) {
      if (!fence) fence = marker[1];
      else if (marker[1][0] === fence[0] && marker[1].length >= fence.length) fence = undefined;
      return { text: '', line: index + 1 };
    }
    return { text: fence ? '' : text, line: index + 1 };
  });
}
function inspectTable(file, section, declared) {
  const rows = section.filter(row => row.text.trim());
  if (rows.length < 2 || rows.some(row => !/^\s*\|.*\|\s*$/.test(row.text))) {
    add(file, rows[0]?.line ?? 1, 'LIST_CONTENT', `${declared.heading}: a single rectangular pipe table is required.`);
    return;
  }
  const cells = row => row.text.trim().slice(1, -1).split('|').map(cell => cell.trim());
  const headers = cells(rows[0]);
  if (headers.some(cell => !cell) || new Set(headers).size !== headers.length) add(file, rows[0].line, 'TABLE_HEADER', 'Empty or duplicate column names.');
  const divider = cells(rows[1]);
  if (divider.length !== headers.length || divider.some(cell => !/^:?-{3,}:?$/.test(cell))) add(file, rows[1].line, 'TABLE_DIVIDER', 'Invalid table separator.');
  if (declared.columns && JSON.stringify(headers) !== JSON.stringify(declared.columns)) add(file, rows[0].line, 'TABLE_COLUMNS', 'columns declaration and actual header differ.');
  const key = declared.key ?? [headers[0]];
  const indexes = key.map(name => headers.indexOf(name));
  if (indexes.some(index => index < 0)) add(file, rows[0].line, 'TABLE_KEY', `Key is not in table: ${key.join(', ')}`);
  const keys = new Set();
  for (const row of rows.slice(2)) {
    const values = cells(row);
    if (values.length !== headers.length) { add(file, row.line, 'TABLE_RECTANGLE', `Expected ${headers.length} columns, got ${values.length}.`); continue; }
    const value = JSON.stringify(indexes.map(index => values[index]));
    if (indexes.some(index => !values[index]) || keys.has(value)) add(file, row.line, 'TABLE_KEY', `Empty or duplicate key: ${value}`);
    keys.add(value);
    if (values.some(value => /<(?!br\s*\/?>)[a-z][^>]*>/i.test(value))) add(file, row.line, 'LIST_HTML', 'HTML other than br in LIST.');
  }
  return { headers, rows: rows.slice(2).map(cells) };
}
for (const target of files.sort()) {
  const file = relative(target), bytes = fs.readFileSync(target);
  const record = { file, sha256: crypto.createHash('sha256').update(bytes).digest('hex'), bytes: bytes.length };
  records.push(record);
  if (!file.endsWith('.md')) continue;
  // These operational entrypoints are frozen verbatim but are not spec-md documents.
  if (file === 'agents/build-agent/PROMPT.md' || file === 'agents/build-agent/README.md') continue;
  const source = bytes.toString('utf8');
  const match = source.match(/^\uFEFF?<!-- spec-meta: (\{[^\r\n]*\}) -->/);
  let meta;
  try { meta = JSON.parse(match?.[1] ?? ''); } catch { add(file, 1, 'META_JSON', 'Missing or invalid leading spec-meta.'); continue; }
  record.documentId = meta.documentId; record.version = meta.version;
  if (meta.path !== file) add(file, 1, 'META_PATH', `Declared path ${meta.path} differs from ${file}.`);
  if (!meta.version || !meta.documentId) add(file, 1, 'META_ID', 'Missing documentId/version.');
  if (ids.has(meta.documentId)) add(file, 1, 'META_DUPLICATE_ID', `Same documentId as ${ids.get(meta.documentId)}.`);
  ids.set(meta.documentId, file);
  const lines = visibleLines(source);
  const chapters = lines.filter(row => /^## /.test(row.text));
  const sheets = meta.sheets ?? [];
  const tableLayout = meta.layout === 'TABLE';
  if (meta.schema !== (tableLayout ? 'spec-md/1.1' : 'spec-md/1.0')) add(file, 1, 'META_SCHEMA', 'Unsupported schema/layout combination.');
  if (tableLayout && (sheets.length !== 1 || sheets[0].kind !== 'TABLE')) add(file, 1, 'TABLE_LAYOUT', 'TABLE requires exactly one TABLE sheet.');
  const sections = tableLayout ? sheets[0]?.sections ?? [] : sheets;
  if (JSON.stringify(chapters.map(row => row.text.slice(3))) !== JSON.stringify(sections.map(row => row.heading))) add(file, 1, 'CHAPTER_MAPPING', 'Actual chapter names/order differ from sheets/sections.');
  const names = new Set();
  for (const sheet of sheets) {
    if (typeof sheet.sheet !== 'string' || !sheet.sheet || [...sheet.sheet].length > 31 || /[\/\\?*:\[\]]/.test(sheet.sheet) || /^'|'$/.test(sheet.sheet) || sheet.sheet.toLowerCase() === 'history' || names.has(sheet.sheet.toLowerCase())) add(file, 1, 'SHEET_NAME', `Invalid/duplicate Excel sheet name: ${sheet.sheet}`);
    names.add(sheet.sheet?.toLowerCase());
  }
  for (let i = 0; i < chapters.length; i++) {
    const chapter = chapters[i], declared = sections.find(section => section.heading === chapter.text.slice(3));
    if (declared?.kind === 'LIST' || declared?.kind === 'HEADER') {
      const end = chapters[i + 1]?.line ?? lines.length + 1;
      const result = inspectTable(file, lines.filter(row => row.line > chapter.line && row.line < end), declared);
      if (tableLayout && declared.kind === 'LIST' && result) {
        const expected = ['No', '論理名', '物理名', 'PK', 'NOT NULL', 'タイプ', '長さ', '初期値', '説明'];
        if (JSON.stringify(result.headers) !== JSON.stringify(expected)) add(file, chapter.line, 'TABLE_NINE_COLUMNS', 'TABLE requires nine specified columns.');
        const physical = result.rows.map(row => row[2]);
        if (JSON.stringify(physical) !== JSON.stringify(Object.keys(meta.table?.fieldIds ?? {}))) add(file, chapter.line, 'TABLE_FIELD_IDS', 'Physical field order differs from fieldIds.');
        if (result.rows.some((row, index) => row[0] !== String(index + 1))) add(file, chapter.line, 'TABLE_SEQUENCE', 'No must be consecutive from 1.');
        const actualPk = result.rows.filter(row => row[3] === '〇').map(row => row[2]);
        const declaredPk = meta.table?.primaryKey ?? [];
        if (actualPk.length !== declaredPk.length || actualPk.some(name => !declaredPk.includes(name))) add(file, chapter.line, 'TABLE_PK', 'PK columns differ from metadata.');
      }
    }
  }
  if ((file.startsWith(`${project}/spec/詳細仕様書/`) || new RegExp(`^${project}/srcs/[^/]+/spec/詳細仕様書/`).test(file)) && /\/0[12]_/.test(file)) {
    const required = ['処理概要', '処理手順', '処理フロー', 'SQL・テーブル関連（ER図）', 'DB操作の詳細', '結果・例外時の扱い'];
    for (let i = 0; i < lines.length; i++) {
      if (!/^### EV-/.test(lines[i].text)) continue;
      const event = lines[i]; let end = i + 1;
      while (end < lines.length && !/^#{1,3} /.test(lines[end].text)) end++;
      const subheads = lines.slice(i + 1, end).filter(row => /^#### /.test(row.text)).map(row => row.text.slice(5));
      for (const heading of required) if (subheads.filter(value => value === heading).length !== 1) add(file, event.line, 'EVENT_SECTIONS', `${event.text}: missing/duplicate ${heading}.`);
    }
  }
  for (const row of lines) {
    const links = [...row.text.matchAll(/!?\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)/g)];
    for (const link of links) {
      const href = link[1];
      if (/^[a-z][a-z\d+.-]*:/i.test(href) || href.startsWith('#')) continue;
      const destination = path.resolve(path.dirname(target), decodeURIComponent(href.split('#')[0]));
      const local = relative(destination);
      const isolatedPrefix=file.match(new RegExp(`^(${project}/srcs/[^/]+/spec/)`))?.[1];
      if (isolatedPrefix && !local.startsWith(isolatedPrefix)) { add(file,row.line,'LINK_ISOLATION',`Reference leaves independent specification package: ${href}`); continue; }
      if (local.split('/').includes('spec-eval')) continue; // Do not inspect evaluation inputs.
      // Shared entrypoints can list every profile; their unselected targets are not inputs.
      if (profile && local.startsWith(`${project}/`) && !fixed.includes(local) && !local.startsWith(selectedSpecPrefix)) continue;
      const allowed = local === 'AGENTS.md' || /^(docs|agents)\//.test(local) || local.startsWith(`${project}/`);
      if (!allowed) { add(file, row.line, 'LINK_SCOPE', `Link outside allowed inputs: ${href}`); continue; }
      if (!fs.existsSync(destination)) add(file, row.line, 'LINK_MISSING', `Missing local reference: ${href}`);
    }
  }
}
let commit = null;
try { commit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); } catch { /* Non-Git inputs still have file hashes. */ }
const context = { agent: 'AG-BUILD', agentVersion: records.find(record=>record.documentId==='AG-BUILD')?.version, projectId: project, ...(profile ? { profileId: profile } : {}), stage: 'build-preflight', runId, recordedAt: new Date().toISOString(), inputCommit: commit, workingTreeHashes: true, excluded: ['spec-eval', 'other projects', 'past reports', ...(profile ? ['other profiles', 'shared business specifications'] : [])], files: records };
const result = { projectId: project, ...(profile ? { profileId: profile } : {}), runId, status: findings.length ? 'interrupted-structure' : 'structure-check-passed', findings, checked: ['metadata', 'chapter/sheet mapping', 'LIST shape/keys', 'TABLE columns/fieldIds/PK', 'event sections', 'local reference existence within input scope'], notChecked: ['semantic consistency', 'external URLs', 'rendering/Excel conversion', 'application generation/build/tests', 'reverse generation/scoring', ...(profile ? ['shared entrypoint references outside the selected input scope'] : [])] };
const output = [
  `# build-agent 構造検査 ${runId}`, '', `対象：${project}${profile ? ` / ${profile}` : ''}。Agent版${context.agentVersion}。入力版・SHA-256は同実行IDのinputs.jsonを参照。`, '',
  `判定：${result.status}。現行入力${records.length}ファイルを検査。問題${findings.length}件。`, '',
  ...findings.flatMap((finding, index) => [`- STR-${String(index + 1).padStart(3, '0')}：${finding.file}:${finding.line} / ${finding.code} / ${finding.detail}`]), '',
  '検査範囲：メタ情報、章/シート対応、LIST矩形・キー、TABLE列/項目ID/PK、イベント6節、入力範囲内のローカル参照先の存在。', '',
  ...(profile ? ['方式指定時は方式内specと固定の全体規則・Agent・project入口だけを入力とし、共有入口から範囲外への参照先は検査しない。', ''] : []),
  '未実施：意味上の整合性検査、外部URL確認、画面描画・Excel変換、アプリ生成・コンパイル・業務試験、逆生成・採点。', '',
  '構造検査通過は生成/ビルド/試験合格を意味しない。構造問題は別Agentが修正し、新しい実行IDで再検査してから再開する。', '',
].join('\n');
fs.mkdirSync(reportRoot, { recursive: true });
fs.writeFileSync(path.join(reportRoot, `${runId}-inputs.json`), JSON.stringify(context, null, 2) + '\n', { flag: 'wx' });
fs.writeFileSync(path.join(reportRoot, `${runId}-structure.json`), JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
fs.writeFileSync(path.join(reportRoot, `${runId}-structure.md`), output, { flag: 'wx' });
console.log(JSON.stringify({ status: result.status, ...(profile ? { profileId: profile } : {}), inputs: records.length, findings: findings.length, report: relative(path.join(reportRoot, `${runId}-structure.md`)) }));
process.exitCode = findings.length ? 2 : 0;
