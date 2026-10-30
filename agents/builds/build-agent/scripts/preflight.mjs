// AG-BUILD: input inspection; one current generation record, scratch in .tmp.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import {layout, ensureDirectory, writeLatest, writeJson} from './output-layout.mjs';
import {assertRegular, collectInputFiles, fixedInputFiles, independentSpecPrefix} from './input-scope.mjs';
import {selectedProfiles, validProfile} from './project-scope.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../..');
const args = process.argv.slice(2);
let project, runId, profile, inspectOnly = false, inspectionOption = false;
if (args.length % 2) throw new Error('Every option requires a value.');
for (let i = 0; i < args.length; i += 2) {
  if (args[i] === '--project' && !project) project = args[i + 1];
  else if (args[i] === '--run-id' && !runId) runId = args[i + 1];
  else if (args[i] === '--profile' && !profile) profile = args[i + 1];
  else if (args[i] === '--inspect-only' && !inspectionOption && ['true', 'false'].includes(args[i + 1])) {inspectOnly = args[i + 1] === 'true'; inspectionOption = true;}
  else throw new Error('Usage: preflight.mjs --project sample-projectN --run-id <unique-id> [--profile <profile-id>] [--inspect-only true]');
}
if (!/^(?:sample|test)-project[1-9]\d*$/.test(project ?? '') || !/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(runId ?? '') || (profile !== undefined && !validProfile(profile))) {
  throw new Error('Explicit project and safe unique run-id are required.');
}
const projectRoot = path.join(root, project);
const methods = selectedProfiles(root, project, profile);
const outputLayout = layout(root, project, profile);
const reportRoot = outputLayout.generation;
assertRegular(projectRoot, true);
if (!inspectOnly && fs.existsSync(reportRoot)) assertRegular(reportRoot, true);
const relative = target => path.relative(root, target).split(path.sep).join('/');
const fixed = fixedInputFiles(project, profile);
const files = collectInputFiles(root, project, profile);
const selectedSpecPrefix = profile ? `${project}/spec/${profile}/` : null;
const findings = [], records = [], ids = new Map(), referenceChecks = [];
const add = (file, line, code, detail) => findings.push({ file, line, code, detail });
const frozenInputs = new Set(files.map(relative));
// These are navigation to design rules, not additional implementation inputs.
// Exact names keep Agent build/.tmp/scripts and arbitrary documents out of the exception.
const designGuides = new Set(['requirement', 'basic-design', 'detail-design'].flatMap(agent => {
  const name = agent === 'requirement' ? '要件定義' : agent === 'basic-design' ? '基本設計' : '詳細設計';
  const base = `agents/designs/${agent}-agent`;
  return ['AGENT.md', 'PROMPT.md', 'README.md', `rules/${name}書作成ルール.md`, `workflows/${name}.md`, 'rules', 'workflows'].map(leaf => `${base}/${leaf}`);
}));
function referenceKind(file, local, isolatedPrefix) {
  if (isolatedPrefix && local === isolatedPrefix.slice(0, -1)) return 'specification-directory-existence';
  if (isolatedPrefix && local.startsWith(isolatedPrefix)) return frozenInputs.has(local) ? 'specification-input' : 'specification-directory-existence';
  const common = local === 'AGENTS.md' || local === 'agents/README.md' || /^(docs|agents)\//.test(local);
  if (common && frozenInputs.has(local)) return 'common-rule-input';
  if (isolatedPrefix && designGuides.has(local)) return 'design-rule-existence';
  if (isolatedPrefix) {
    const ownSource = isolatedPrefix.replace(`${project}/spec/`, `${project}/srcs/`);
    if (['basic-design', 'detail-design'].some(stage => local === `${ownSource}build/spec-generation/${stage}/report.md`)) return 'design-record-existence';
  }
  if (file.startsWith('docs/') && frozenInputs.has(file) && local === 'references/web-ui-standard/README.md') return 'reference-source-existence';
  return null;
}
function inspectReference(file, line, href, destination, local, kind) {
  // No reads/hashes or recursive traversal: only the target and every ancestor are
  // checked. realpath rejects a redirected parent as well as a linked leaf.
  try {
    const isGuideDirectory = kind === 'specification-directory-existence' || (kind === 'design-rule-existence' && /\/(rules|workflows)$/.test(local));
    const directory = kind === 'routing-guide-existence' ? fs.lstatSync(destination).isDirectory() : isGuideDirectory;
    assertRegular(destination, directory);
  } catch (error) {
    add(file, line, error.code === 'ENOENT' ? 'LINK_MISSING' : 'LINK_NONREGULAR', `Invalid ${kind} reference: ${href}`);
    return;
  }
  referenceChecks.push({file, line, href, target: local, kind, contentReadByReferenceCheck: false, frozenInput: frozenInputs.has(local)});
}
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
    if (values.some(value => {
      // Inline code and C# collection signatures are text, not rendered tags.
      const text = value.replace(/(`+)[^\r\n]*?\1/g, '').replace(/\b(?:IReadOnlyList|IReadOnlySet|IReadOnlyDictionary|IEnumerable|ICollection|IList|IDictionary|List|Collection|Dictionary|HashSet|Task|ValueTask|Nullable|Func|Action|PasswordHasher)<(?:[A-Z][A-Za-z0-9_.]*|string|int|long|short|bool|byte|decimal|double|float|object)\??(?:,\s*(?:[A-Z][A-Za-z0-9_.]*|string|int|long|short|bool|byte|decimal|double|float|object)\??)*>/g, '');
      return /<(?!br\s*\/?>)[a-z][^>]*>/i.test(text);
    })) add(file, row.line, 'LIST_HTML', 'HTML other than br in LIST.');
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
  if (isolatedPrefix && file.startsWith(`${isolatedPrefix}詳細仕様書/`)) {
    const required = ['処理概要', '処理手順', '処理フロー', 'SQL・テーブル関連（ER図）', 'DB操作の詳細', '結果・例外時の扱い'];
    for (let i = 0; i < lines.length; i++) {
      if (!/^### (?:EV-[A-Za-z0-9_-]+|F\d{2}-E\d{2})(?:\s|$)/.test(lines[i].text)) continue;
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
      let destination;
      try { destination = path.resolve(path.dirname(target), decodeURIComponent(href.split('#')[0])); }
      catch { add(file, row.line, 'LINK_SCOPE', `Invalid local reference encoding: ${href}`); continue; }
      const local = relative(destination);
      // Ignored subtrees remain forbidden even when nested in the selected root.
      // Never follow them just because their normalized path shares its prefix.
      if (isolatedPrefix && local.startsWith(isolatedPrefix) && local.slice(isolatedPrefix.length).split('/').some(part => ['spec-eval', 'spec-analysis', '.tmp', 'build', '.git'].includes(part.toLowerCase()))) {
        add(file, row.line, 'LINK_ISOLATION', `Reference enters an excluded specification subtree: ${href}`); continue;
      }
      // Existence-only guide exceptions never expand files/records or grant a
      // later reader access to their contents as normative business material.
      const kind = referenceKind(file, local, isolatedPrefix);
      if (kind && kind !== 'specification-input' && kind !== 'specification-directory-existence') {
        inspectReference(file, row.line, href, destination, local, kind);
        continue;
      }
      if (isolatedPrefix && !kind) { add(file,row.line,'LINK_ISOLATION',`Reference leaves independent specification package: ${href}`); continue; }
      // General routing documents may mention another project; never inspect it.
      if (!isolatedPrefix && /^(?:sample|test)-project[1-9]\d*\//.test(local) && !local.startsWith(`${project}/`)) continue;
      if (local.split('/').includes('spec-eval')) continue; // Do not inspect evaluation inputs.
      // Shared entrypoints can list every profile; their unselected targets are not inputs.
      if (!isolatedPrefix && profile && local.startsWith(`${project}/`) && !fixed.includes(local) && !local.startsWith(selectedSpecPrefix)) continue;
      const allowed = local === 'AGENTS.md' || /^(docs|agents)\//.test(local) || local.startsWith(`${project}/`);
      if (!allowed) { add(file, row.line, 'LINK_SCOPE', `Link outside allowed inputs: ${href}`); continue; }
      inspectReference(file, row.line, href, destination, local, kind ?? 'routing-guide-existence');
    }
  }
}
let commit = null;
try { commit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); } catch { /* Non-Git inputs still have file hashes. */ }
const context = { agent: 'AG-BUILD', agentVersion: records.find(record=>record.documentId==='AG-BUILD')?.version, projectId: project, ...(profile ? { profileId: profile } : {}), stage: 'build-preflight', inspectionOnly: inspectOnly, specificationLayout: 'project/spec/profile', runId, recordedAt: new Date().toISOString(), inputCommit: commit, workingTreeHashes: true, excluded: ['spec-eval', 'spec-analysis', 'other projects', 'past reports', 'source trees', ...(profile ? ['other profiles', 'shared business specifications'] : [])], files: records };
const result = { projectId: project, ...(profile ? { profileId: profile } : {}), runId, inspectionOnly: inspectOnly, status: findings.length ? 'interrupted-structure' : 'structure-check-passed', findings, referenceChecks, checked: ['metadata', 'chapter/sheet mapping', 'LIST shape/keys', 'TABLE columns/fieldIds/PK', 'event sections', 'classified local reference existence; guide exceptions require regular unredirected paths'], notChecked: ['semantic consistency', 'external URLs', 'contents of existence-only design rules, design records and raw-reference source guides; these are not input additions', 'rendering/Excel conversion', 'application generation/build/tests', 'reverse generation/scoring', ...(profile ? ['shared entrypoint references outside the selected input scope'] : [])] };
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
for (const method of methods) {
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
