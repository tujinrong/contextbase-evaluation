// AG-BUILD: render verified, unchanged screenshot artifacts as a portable gallery.
// Usage: node agents/build-agent/scripts/write-test-evidence.mjs --project test-project1 --run-id <fresh-run-id>
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const workspace = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const args = process.argv.slice(2);
let project, runId;
for (let i = 0; i < args.length; i += 2) {
  if (args[i] === '--project' && !project) project = args[i + 1];
  else if (args[i] === '--run-id' && !runId) runId = args[i + 1];
  else throw new Error('Usage: write-test-evidence.mjs --project test-project1 --run-id <run-id>');
}
if (project !== 'test-project1' || !/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(runId ?? '')) {
  throw new Error('Explicit test-project1 and a safe run-id are required.');
}

const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const portable = file => file.split(path.sep).join('/');
const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const url = relative => relative.split('/').map(encodeURIComponent).join('/');
const mdText = value => String(value).replace(/[\\`*_[\]<>|]/g, '\\$&').replace(/\r?\n/g, ' ');
const profiles = [
  {id: 'VB.NET_WinForms', folder: 'VB.NET_WinForms', title: 'VB.NET WinForms', scope: '実フォーム・Presenterを独立した試験fixtureで実行。SQL接続はなく、SQL Server上の正常な保存・削除は未実施。'},
  {id: 'CSharp_WPF', folder: 'CSharp_WPF', title: 'C# WPF', scope: '実WPF画面を独立した試験fixtureで実行。SQL接続はなく、SQL Server上の正常な保存・削除は未実施。'},
  {id: 'CSharp_ASPNET', folder: 'CSharp_MVC', title: 'C# ASP.NET MVC', scope: '実Controller・Razor Viewを独立した試験fixtureで実行。SQL接続はなく、SQL Server上の正常な保存・削除は未実施。'},
  {id: 'Vue_CSharpAPI', folder: 'Vue', title: 'Vue + C# API', scope: '実Vue画面・APIを独立した試験fixtureで実行。SQL接続はなく、SQL Server上の正常な保存・削除は未実施。'},
  {id: 'COBOL', folder: 'COBOL', title: 'COBOL', scope: '実production CGIの401認証エラー・400不正要求エラーだけを撮影。認証済み正常CRUD画面はNOT_RUN。SQL接続・業務データ投入は未実施。'},
  {id: 'AS400_RPG', folder: 'AS400_RPG', title: 'AS400 RPG', scope: 'IBM i実機がないため5250画面撮影はNOT_RUN。C補助処理のホスト試験は別の試験報告に記録。5250画面画像は生成しない。'},
  {id: 'Access', folder: 'Access', title: 'Microsoft Access', scope: '原本と区別したローカルfixtureで実フォーム・DAOを試験。形式指定や初期表示の修正前・途中段階の画像も保持し、メモで区別。最終修正後は実ACE/accdb形式。SQL Server接続・共有DB移行は未実施。'}
];
const byFolder = new Map(profiles.map(profile => [profile.folder, profile]));

function inside(parent, target) {
  const relative = path.relative(parent, target);
  return relative === '' || (!path.isAbsolute(relative) && relative !== '..' && !relative.startsWith(`..${path.sep}`));
}

// Reject links at every traversed component, including the run directory itself.
function regularPath(base, relative, directory = false) {
  if (typeof relative !== 'string' || relative.length === 0 || relative.includes('\\') || relative.includes('\0') || relative.includes(':') || path.isAbsolute(relative)) {
    throw new Error(`An exact portable relative file path is required: ${String(relative)}`);
  }
  const components = relative.split('/');
  if (components.some(part => part === '' || part === '.' || part === '..' || /[\x00-\x1f]/.test(part) || /[. ]$/.test(part) || /^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)/i.test(part))) {
    throw new Error(`Noncanonical relative path refused: ${relative}`);
  }
  let target = base;
  for (let i = 0; i < components.length; i++) {
    if (!fs.readdirSync(target).includes(components[i])) throw new Error(`Path spelling must match the actual file exactly: ${relative}`);
    target = path.join(target, components[i]);
    const info = fs.lstatSync(target);
    if (info.isSymbolicLink() || (i < components.length - 1 && !info.isDirectory())) {
      throw new Error(`Linked or non-directory path refused: ${relative}`);
    }
    if (i === components.length - 1 && (directory ? !info.isDirectory() : !info.isFile())) {
      throw new Error(`Regular ${directory ? 'directory' : 'file'} required: ${relative}`);
    }
  }
  if (!inside(fs.realpathSync(base), fs.realpathSync(target))) throw new Error(`Path escapes its root: ${relative}`);
  if (portable(path.relative(base, target)) !== relative) throw new Error(`Relative file did not resolve exactly: ${relative}`);
  return target;
}

const runRelative = `${project}/test-evidence/${runId}`;
const runRoot = regularPath(workspace, runRelative, true);
const outputNames = ['test-evidence.html', 'test-evidence.md', 'capture-integrity.json'];
for (const name of outputNames) {
  if (fs.existsSync(path.join(runRoot, name))) throw new Error(`Existing evidence cannot be overwritten: ${name}`);
}
const reportReadme = '../../test-report/README.md';
regularPath(workspace, `${project}/test-report/README.md`);

// SOF dimensions are checked without installing a decoder or changing pixels.
// This verifies JPEG framing/header dimensions, not a complete image decode.
function jpegDimensions(bytes, file) {
  if (bytes.length < 12 || bytes[0] !== 0xff || bytes[1] !== 0xd8 || bytes.at(-2) !== 0xff || bytes.at(-1) !== 0xd9) {
    throw new Error(`JPEG SOI/EOI magic required: ${file}`);
  }
  const sof = new Set([0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf]);
  let cursor = 2;
  while (cursor < bytes.length - 2) {
    if (bytes[cursor++] !== 0xff) throw new Error(`Malformed JPEG marker: ${file}`);
    while (cursor < bytes.length && bytes[cursor] === 0xff) cursor++;
    const marker = bytes[cursor++];
    if (marker === 0x00 || marker === 0xd8 || marker === 0xd9 || marker === 0xda) break;
    if (marker === 0x01 || (marker >= 0xd0 && marker <= 0xd7)) continue;
    if (cursor + 2 > bytes.length) break;
    const length = bytes.readUInt16BE(cursor);
    if (length < 2 || cursor + length > bytes.length - 2) throw new Error(`Invalid JPEG segment length: ${file}`);
    if (sof.has(marker)) {
      if (length < 11) throw new Error(`Invalid JPEG SOF: ${file}`);
      const height = bytes.readUInt16BE(cursor + 3);
      const width = bytes.readUInt16BE(cursor + 5);
      const components = bytes[cursor + 7];
      if (!width || !height || !components || length !== 8 + 3 * components) throw new Error(`Invalid JPEG dimensions/components: ${file}`);
      return {width, height};
    }
    cursor += length;
  }
  throw new Error(`JPEG SOF dimensions not found: ${file}`);
}

const inputFiles = [], captures = [], filesSeen = new Set(), hashesSeen = new Map(), imageSources = new Map();
for (const inputName of ['native-captures.json', 'web-captures.json']) {
  const inputPath = regularPath(runRoot, inputName);
  const inputBytes = fs.readFileSync(inputPath);
  const rows = JSON.parse(inputBytes.toString('utf8').replace(/^\uFEFF/, ''));
  if (!Array.isArray(rows)) throw new Error(`Capture metadata must be an array: ${inputName}`);
  inputFiles.push({file: inputName, bytes: inputBytes.length, sha256: hash(inputBytes), records: rows.length});
  for (const [index, row] of rows.entries()) {
    if (!row || typeof row !== 'object' || Array.isArray(row)) throw new Error(`Invalid capture metadata: ${inputName}[${index}]`);
    const file = row.file;
    const target = regularPath(runRoot, file);
    const profile = byFolder.get(file.split('/')[0]);
    if (!profile || file.split('/').length !== 2 || !/\.jpe?g$/i.test(file)) throw new Error(`Unknown method or non-JPEG capture: ${file}`);
    if (profile.id === 'AS400_RPG') throw new Error('IBM i / 5250 is NOT_RUN; unexpected RPG screenshot metadata requires review.');
    if (filesSeen.has(file)) throw new Error(`A capture file is listed more than once: ${file}`);
    filesSeen.add(file);
    if (typeof row.sha256 !== 'string' || !/^[0-9a-f]{64}$/i.test(row.sha256)) throw new Error(`SHA-256 metadata required: ${file}`);
    if (typeof row.capturedAt !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:Z|[+-]\d{2}:\d{2})$/.test(row.capturedAt) || !Number.isFinite(Date.parse(row.capturedAt))) {
      throw new Error(`Unambiguous capture timestamp required: ${file}`);
    }
    if (typeof row.note !== 'string' || row.note.trim().length === 0) throw new Error(`Capture scope note required: ${file}`);
    const status = row.status ?? 'CAPTURED';
    if (!['CAPTURED', 'DUPLICATE_CAPTURE'].includes(status)) throw new Error(`Capture requires review before publication (${status}): ${file}`);
    const bytes = fs.readFileSync(target);
    const actualSha256 = hash(bytes);
    if (actualSha256 !== row.sha256.toLowerCase()) throw new Error(`SHA-256 mismatch: ${file}`);
    const dimensions = jpegDimensions(bytes, file);
    if (!imageSources.has(actualSha256)) imageSources.set(actualSha256, `data:image/jpeg;base64,${bytes.toString('base64')}`);
    const suppliedDimensionFields = ['width', 'height'].filter(key => row[key] !== undefined);
    for (const key of suppliedDimensionFields) {
      if (!Number.isInteger(row[key]) || row[key] < 1 || row[key] !== dimensions[key]) throw new Error(`JPEG ${key} disagrees with metadata: ${file}`);
    }
    const matchingFiles = hashesSeen.get(actualSha256) ?? [];
    matchingFiles.push(file);
    hashesSeen.set(actualSha256, matchingFiles);
    captures.push({file, profile: profile.id, status, capturedAt: row.capturedAt, note: row.note,
      windowTitle: typeof row.window?.title === 'string' ? row.window.title : null,
      sourceUrl: typeof row.url === 'string' ? row.url : null,
      metadataFile: inputName, metadataIndex: index, bytes: bytes.length, sha256: actualSha256,
      ...dimensions, metadataDimensionFields: suppliedDimensionFields,
      checks: {exactRelativePath: true, withinRunRoot: true, noSymlink: true, sha256Matched: true, jpegMagic: true, jpegDimensions: true}});
  }
}
for (const capture of captures) {
  capture.identicalFiles = hashesSeen.get(capture.sha256).filter(file => file !== capture.file);
  if (capture.status === 'DUPLICATE_CAPTURE' && capture.identicalFiles.length === 0) {
    throw new Error(`DUPLICATE_CAPTURE has no identical image in the metadata: ${capture.file}`);
  }
}
captures.sort((a, b) => a.file.localeCompare(b.file, 'en'));
const generatedAt = new Date().toISOString();
const counts = {
  metadataRecords: captures.length,
  verifiedImageFiles: captures.length,
  uniqueImageHashes: hashesSeen.size,
  explicitlyDuplicateCaptures: captures.filter(c => c.status === 'DUPLICATE_CAPTURE').length,
  additionalIdenticalImages: captures.length - hashesSeen.size,
  displayedImages: captures.length,
  invalidCaptures: 0,
  byProfile: Object.fromEntries(profiles.map(profile => [profile.id, {
    verifiedImageFiles: captures.filter(c => c.profile === profile.id).length,
    explicitlyDuplicateCaptures: captures.filter(c => c.profile === profile.id && c.status === 'DUPLICATE_CAPTURE').length,
    screenshotStatus: profile.id === 'AS400_RPG' ? 'NOT_RUN' : captures.some(c => c.profile === profile.id) ? 'CAPTURED_WITH_SCOPE_LIMITS' : 'NOT_CAPTURED'
  }]))
};
const intro = '実際に保存された画面画像の一覧です。画像の存在・ハッシュ一致は、正常CRUD・共有SQL Server接続・権限検証の合格を意味しません。方式ごとの実行範囲と各撮影メモを参照してください。';
const integrity = {
  schema: 'test-capture-integrity/1.0', projectId: project, runId, generatedAt, status: 'CAPTURE_INTEGRITY_PASSED',
  runRoot: runRelative, script: {file: 'agents/build-agent/scripts/write-test-evidence.mjs', sha256: hash(fs.readFileSync(fileURLToPath(import.meta.url)))},
  inputFiles, counts, originalImageBytesModified: false, completeImageDecodeVerified: false,
  integrityScope: ['exact relative file path', 'run-root containment and no symlinks', 'SHA-256', 'JPEG SOI/EOI framing', 'SOF width/height', 'supplied dimension metadata agreement'],
  applicationSuccessInferredFromScreenshots: false, sharedSqlBusinessTestDataInserted: false,
  limits: profiles.map(profile => ({profile: profile.id, scope: profile.scope})),
  duplicatePolicy: 'Display verified duplicate images with an explicit duplicate label; do not count identical bytes as additional unique evidence.',
  htmlImagesEmbedded: true, embeddedImageEncoding: 'unchanged original JPEG bytes, base64',
  reportReadme, captures
};

function captureHtml(capture) {
  const scope = profiles.find(profile => profile.id === capture.profile).scope;
  const duplicate = capture.status === 'DUPLICATE_CAPTURE' ? '重複撮影（DUPLICATE_CAPTURE）' : capture.identicalFiles.length ? '同一画像あり' : '撮影済み';
  const identical = capture.identicalFiles.length ? `<p>同一画像：${capture.identicalFiles.map(file => `<a href="${url(file)}">${escapeHtml(file)}</a>`).join('、')}</p>` : '';
  return `<figure><a class="image-link" href="${url(capture.file)}"><img src="${imageSources.get(capture.sha256)}" width="${capture.width}" height="${capture.height}" loading="lazy" alt="${escapeHtml(capture.file)}：${escapeHtml(capture.note)}"></a><figcaption><p class="capture-name"><a href="${url(capture.file)}">${escapeHtml(capture.file)}</a> <span class="badge">${escapeHtml(duplicate)}</span></p><p>撮影日時：<time datetime="${escapeHtml(capture.capturedAt)}">${escapeHtml(capture.capturedAt)}</time> ／ ${capture.width} × ${capture.height}px</p><p>${escapeHtml(capture.note)}</p><p>試験範囲：${escapeHtml(scope)}</p>${capture.windowTitle ? `<p>画面：${escapeHtml(capture.windowTitle)}</p>` : ''}<p class="hash">SHA-256：${capture.sha256}</p>${identical}</figcaption></figure>`;
}
const sections = profiles.map(profile => {
  const rows = captures.filter(capture => capture.profile === profile.id);
  return `<section id="${profile.id}"><h2>${escapeHtml(profile.title)} <small>（${rows.length}画像）</small></h2><p class="scope">${escapeHtml(profile.scope)}</p>${rows.length ? `<div class="gallery">${rows.map(captureHtml).join('\n')}</div>` : `<p class="no-image">${profile.id === 'AS400_RPG' ? 'NOT_RUN：IBM i / 5250の画像はありません。' : 'この方式の撮影画像はまだありません。'}</p>`}</section>`;
}).join('\n');
const html = `<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>試験画面エビデンス ${escapeHtml(runId)}</title>
<style>
:root{color-scheme:light dark}body{font-family:system-ui,"Yu Gothic",Meiryo,sans-serif;margin:0;line-height:1.65;color:#203047;background:#f3f5f8}main{max-width:1400px;margin:auto;padding:24px}h1{font-size:1.7rem}h2{border-bottom:2px solid #607c98;padding-bottom:.4rem;margin-top:2.5rem}h2 small{font-size:.8rem;font-weight:normal}a{color:#174f95}nav{display:flex;flex-wrap:wrap;gap:8px 18px}nav a{padding:3px 0}.summary,.scope,.no-image{background:#fff;padding:16px;border-radius:8px}.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:20px}figure{margin:0;background:#fff;border:1px solid #d5dce4;border-radius:8px;overflow:hidden}.image-link{display:block;background:#e9edf2;padding:8px}img{display:block;width:100%;height:auto;max-height:760px;object-fit:contain}figcaption{font-size:.82rem;padding:12px 16px;overflow-wrap:anywhere}figcaption p{margin:.4rem 0}.capture-name{font-weight:600}.badge{display:inline-block;background:#e6edf6;border-radius:4px;padding:1px 6px;font-size:.74rem}.hash{font-family:ui-monospace,Consolas,monospace;font-size:.72rem}footer{font-size:.8rem;margin-top:2rem}@media(prefers-color-scheme:dark){body{color:#e1e8f1;background:#17202c}.summary,.scope,.no-image,figure{background:#232f40}figure{border-color:#455368}a{color:#a8cdff}.image-link,.badge{background:#35445a}}
</style></head><body><main><h1>試験画面エビデンス</h1><p>${escapeHtml(project)} ／ ${escapeHtml(runId)}</p><div class="summary"><p>${escapeHtml(intro)}</p><p>検証済み画像：${counts.verifiedImageFiles} ／ 異なる画像ハッシュ：${counts.uniqueImageHashes} ／ 明示的な重複撮影：${counts.explicitlyDuplicateCaptures}</p><p>共有SQL Serverへの業務データ投入は移行停止のため未実施。画像原本のバイト列は変更していません。</p><p><a href="${reportReadme}">試験報告 README</a> · <a href="test-evidence.md">Markdown一覧</a> · <a href="capture-integrity.json">画像整合性・件数 JSON</a></p></div><nav aria-label="方式別目次">${profiles.map(profile => `<a href="#${profile.id}">${escapeHtml(profile.title)}</a>`).join('')}</nav>${sections}<footer>一覧生成日時：${escapeHtml(generatedAt)}。SHA-256・JPEGヘッダーの整合性を検証。画像全体のデコードと画面の機能合否は別の検査です。外部JS・CDNは使用していません。</footer></main></body></html>\n`;

const markdown = [
  '# 試験画面エビデンス', '', `${project} ／ ${runId}`, '', intro, '',
  `検証済み画像 ${counts.verifiedImageFiles}件、異なる画像ハッシュ ${counts.uniqueImageHashes}件、明示的な重複撮影 ${counts.explicitlyDuplicateCaptures}件。`, '',
  '共有SQL Serverへの業務データ投入は移行停止のため未実施。画像原本のバイト列は変更していません。', '',
  `[HTML一覧](test-evidence.html) · [画像整合性・件数 JSON](capture-integrity.json) · [試験報告 README](${reportReadme})`, ''
];
for (const profile of profiles) {
  const rows = captures.filter(capture => capture.profile === profile.id);
  markdown.push(`## ${profile.title}`, '', profile.scope, '');
  if (!rows.length) {
    markdown.push(profile.id === 'AS400_RPG' ? 'NOT_RUN：IBM i / 5250の画像はありません。' : 'この方式の撮影画像はまだありません。', '');
    continue;
  }
  for (const capture of rows) {
    const duplicate = capture.status === 'DUPLICATE_CAPTURE' ? '重複撮影（DUPLICATE_CAPTURE）' : capture.identicalFiles.length ? '同一画像あり' : '撮影済み';
    markdown.push(`- [${mdText(capture.file)}](${url(capture.file)}) — ${duplicate}。撮影日時 ${capture.capturedAt}、${capture.width} × ${capture.height}px。${mdText(capture.note)} SHA-256: \`${capture.sha256}\`${capture.identicalFiles.length ? `。同一画像: ${capture.identicalFiles.map(file => `[${mdText(file)}](${url(file)})`).join('、')}` : ''}`, '');
  }
}
markdown.push(`一覧生成日時：${generatedAt}。JPEGの完全デコードと機能合否は、この一覧生成の検査範囲に含みません。`, '');

// Refuse a capture/metadata race before publishing any of the three fresh outputs.
for (const input of inputFiles) {
  if (hash(fs.readFileSync(regularPath(runRoot, input.file))) !== input.sha256) throw new Error(`Capture metadata changed during generation: ${input.file}`);
}
for (const capture of captures) {
  if (hash(fs.readFileSync(regularPath(runRoot, capture.file))) !== capture.sha256) throw new Error(`Image changed during generation: ${capture.file}`);
}
const contents = [html, markdown.join('\n'), JSON.stringify(integrity, null, 2) + '\n'];
for (const [index, name] of outputNames.entries()) fs.writeFileSync(path.join(runRoot, name), contents[index], {encoding: 'utf8', flag: 'wx'});
console.log(JSON.stringify({projectId: project, runId, status: integrity.status, counts, outputs: outputNames.map(name => `${runRelative}/${name}`)}));
