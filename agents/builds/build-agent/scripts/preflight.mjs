// AG-BUILD: input inspection; one current generation record, scratch in .tmp.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import {layout, ensureDirectory, writeLatest, writeJson} from './output-layout.mjs';
import {assertRegular, collectInputFiles, fixedInputFiles, independentSpecPrefix} from './input-scope.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../..');
const args = process.argv.slice(2);
const profiles = ['VB.NET_WinForms', 'CSharp_WPF', 'CSharp_ASPNET', 'Vue_CSharpAPI', 'COBOL', 'AS400_RPG', 'Access'];
let project, runId, profile, inspectOnly = false, inspectionOption = false;
if (args.length % 2) throw new Error('Every option requires a value.');
for (let i = 0; i < args.length; i += 2) {
  if (args[i] === '--project' && !project) project = args[i + 1];
  else if (args[i] === '--run-id' && !runId) runId = args[i + 1];
  else if (args[i] === '--profile' && !profile) profile = args[i + 1];
  else if (args[i] === '--inspect-only' && !inspectionOption && ['true', 'false'].includes(args[i + 1])) {inspectOnly = args[i + 1] === 'true'; inspectionOption = true;}
  else throw new Error('Usage: preflight.mjs --project sample-projectN --run-id <unique-id> [--profile <profile-id>] [--inspect-only true]');
}
if (!/^(?:sample|test)-project[1-9]\d*$/.test(project ?? '') || !/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(runId ?? '') || (profile !== undefined && !profiles.includes(profile))) {
  throw new Error('Explicit project and safe unique run-id are required.');
}
const projectRoot = path.join(root, project);
const outputLayout = layout(root, project, profile);
const reportRoot = outputLayout.generation;
assertRegular(projectRoot, true);
if (!inspectOnly && fs.existsSync(reportRoot)) assertRegular(reportRoot, true);
const relative = target => path.relative(root, target).split(path.sep).join('/');
const fixed = fixedInputFiles(project, profile);
const files = collectInputFiles(root, project, profile);
const selectedSpecPrefix = profile ? `${project}/spec/${profile}/` : null;
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
  if (file === 'agents/builds/build-agent/PROMPT.md' || file === 'agents/builds/build-agent/README.md') continue;
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
  const isolatedPrefix = independentSpecPrefix(file, project);
  if (isolatedPrefix && file.startsWith(`${isolatedPrefix}詳細仕様書/`) && /\/0[12]_/.test(file)) {
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
const context = { agent: 'AG-BUILD', agentVersion: records.find(record=>record.documentId==='AG-BUILD')?.version, projectId: project, ...(profile ? { profileId: profile } : {}), stage: 'build-preflight', inspectionOnly: inspectOnly, specificationLayout: 'project/spec/profile', runId, recordedAt: new Date().toISOString(), inputCommit: commit, workingTreeHashes: true, excluded: ['spec-eval', 'spec-analysis', 'other projects', 'past reports', 'source trees', ...(profile ? ['other profiles', 'shared business specifications'] : [])], files: records };
const result = { projectId: project, ...(profile ? { profileId: profile } : {}), runId, inspectionOnly: inspectOnly, status: findings.length ? 'interrupted-structure' : 'structure-check-passed', findings, checked: ['metadata', 'chapter/sheet mapping', 'LIST shape/keys', 'TABLE columns/fieldIds/PK', 'event sections', 'local reference existence within input scope'], notChecked: ['semantic consistency', 'external URLs', 'rendering/Excel conversion', 'application generation/build/tests', 'reverse generation/scoring', ...(profile ? ['shared entrypoint references outside the selected input scope'] : [])] };
const output = [
  `# build-agent 構造検査 ${runId}`, '', `対象：${project}${profile ? ` / ${profile}` : ''}。Agent版${context.agentVersion}。入力版・SHA-256は同実行IDのinputs.jsonを参照。`, '',
  `判定：${result.status}。現行入力${records.length}ファイルを検査。問題${findings.length}件。`, '',
  ...findings.flatMap((finding, index) => [`- STR-${String(index + 1).padStart(3, '0')}：${finding.file}:${finding.line} / ${finding.code} / ${finding.detail}`]), '',
  '検査範囲：メタ情報、章/シート対応、LIST矩形・キー、TABLE列/項目ID/PK、イベント6節、入力範囲内のローカル参照先の存在。', '',
  ...(profile ? ['方式指定時はproject/spec/方式IDと固定の全体規則・Agent・project入口だけを入力とし、共有入口から範囲外への参照先は検査しない。', ''] : []),
  '未実施：意味上の整合性検査、外部URL確認、画面描画・Excel変換、アプリ生成・コンパイル・業務試験、逆生成・採点。', '',
  '構造検査通過は生成/ビルド/試験合格を意味しない。構造問題は別Agentが修正し、新しい実行IDで再検査してから再開する。', '',
].join('\n');
// A new preflight invalidates the preceding final manifest/package result.
if (inspectOnly) {
  // Inspection never creates directories, invalidates manifests or moves packages.
  console.log(JSON.stringify({status: result.status, inspectionOnly: true, inputs: context, structure: result}));
  process.exit(findings.length ? 2 : 0);
}
ensureDirectory(reportRoot);
for (const name of ['outputs.json', 'source-packages.json']) {
  const old = path.join(reportRoot, name);
  if (fs.existsSync(old)) { assertRegular(old); fs.unlinkSync(old); }
}
for (const method of profile ? [profile] : profiles) {
  const own = layout(root, project, method);
  ensureDirectory(own.build);
  const sourceZip = path.join(own.build, 'source.zip');
  if (fs.existsSync(sourceZip)) {
    assertRegular(sourceZip);
    ensureDirectory(own.scratch);
    fs.renameSync(sourceZip, path.join(own.scratch, 'stale-source.zip'));
  }
}
writeJson(path.join(reportRoot, 'inputs.json'), context, outputLayout.scratch);
writeJson(path.join(reportRoot, 'structure.json'), result, outputLayout.scratch);
writeLatest(path.join(reportRoot, 'structure.md'), output.replace('同実行IDのinputs.json', 'inputs.json'), outputLayout.scratch);
console.log(JSON.stringify({ status: result.status, ...(profile ? { profileId: profile } : {}), inputs: records.length, findings: findings.length, report: relative(path.join(reportRoot, 'structure.md')) }));
process.exitCode = findings.length ? 2 : 0;
