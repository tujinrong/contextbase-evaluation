// Specification inputs live outside generated source trees; no legacy fallback.
import fs from 'node:fs';
import path from 'node:path';
import {selectedProfiles} from './project-scope.mjs';

// Layout family is separate from the native rendering technology (notably WPF).
const uiFamilies = Object.freeze({
  CSharp_ASPNET:'WEB', Vue_CSharpAPI:'WEB', CSharp_WPF:'WEB',
  'VB.NET_WinForms':'WINFORMS', Access:'WINFORMS', COBOL:'TEXT', AS400_RPG:'TEXT',
});
const uiQualityFiles = Object.freeze({WEB:'docs/WEB画面品質規約.md',WINFORMS:'docs/WinForms画面品質規約.md',TEXT:'docs/Text画面品質規約.md'});
const uiRenderers = Object.freeze({CSharp_ASPNET:'BROWSER',Vue_CSharpAPI:'BROWSER',CSharp_WPF:'WPF','VB.NET_WinForms':'WINFORMS',Access:'ACCESS',COBOL:'TERMINAL',AS400_RPG:'TERMINAL'});
const familyRenderers = Object.freeze({WEB:['BROWSER','WPF'],WINFORMS:['WINFORMS','ACCESS'],TEXT:['TERMINAL']});
export const uiFamilyForProfile = profile => Object.hasOwn(uiFamilies,profile) ? uiFamilies[profile] : null;

export function resolveUIFamily(root, project, profile) {
  selectedProfiles(root,project,profile);
  if(!profile) throw new Error('Exactly one profile is required to resolve its UI family.');
  const known=uiFamilyForProfile(profile), renderer=Object.hasOwn(uiRenderers,profile)?uiRenderers[profile]:null;
  const relative=`${project}/spec/${profile}/規約/UIパターン.json`,target=path.join(root,relative);
  // lstat also detects dangling links; existsSync would silently treat those as absent.
  let info;try{info=fs.lstatSync(target);}catch(error){if(error.code!=='ENOENT')throw error;}
  if(!info) return {family:known,renderer,source:null};
  assertRegular(target);
  const value=JSON.parse(fs.readFileSync(target,'utf8').replace(/^\uFEFF/,''));
  if(!value || typeof value!=='object' || Array.isArray(value) || value.schemaVersion!==1 ||
     !Object.hasOwn(familyRenderers,value.family) || !familyRenderers[value.family].includes(value.renderer) ||
     Object.keys(value).some(key=>!['schemaVersion','family','renderer'].includes(key))) throw new Error('Invalid UI pattern specification: '+relative);
  if(known && (value.family!==known || value.renderer!==renderer)) throw new Error('UI pattern specification contradicts the registered family/renderer: '+profile);
  return {family:value.family,renderer:value.renderer,source:relative};
}

export function fixedInputFiles(project, profile) {
  return [
    'AGENTS.md', 'agents/README.md',
    'agents/designs/detail-design-agent/AGENT.md',
    'agents/designs/detail-design-agent/rules/詳細設計書作成ルール.md',
    'agents/designs/detail-design-agent/workflows/詳細設計.md',
    'agents/builds/build-agent/AGENT.md', 'agents/builds/build-agent/PROMPT.md', 'agents/builds/build-agent/README.md', 'agents/reverses/reverse-agent/AGENT.md',
    'docs/リポジトリ構成.md', 'docs/開発規約.md', 'docs/仕様書作成ルール.md',
    'docs/評価規約.md', 'docs/MD構造・Excel変換規約.md', 'docs/テーブル仕様書記述規約.md',
    'docs/テストデータ整備規約.md', 'docs/UI適合検査.md', 'docs/UIパターン規約.md',
    'agents/builds/build-agent/docs/UIパターン生成チェック.md',
    ...(!profile ? Object.values(uiQualityFiles) : uiFamilyForProfile(profile) ? [uiQualityFiles[uiFamilyForProfile(profile)]] : []),
    ...(!profile || profile === 'Access' ? ['docs/Access画面品質規約.md', 'agents/builds/build-agent/docs/Access生成チェック.md'] : []),
    `${project}/README.md`, `${project}/プロジェクト情報.md`, `${project}/spec/README.md`,
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
  const methods = selectedProfiles(root, project, profile);
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
  for (const method of methods) {
    const ui=resolveUIFamily(root,project,method);
    if(ui.family) {const target=path.join(root,uiQualityFiles[ui.family]);assertRegular(target);files.push(target);}
    if(ui.renderer==='ACCESS') for(const name of ['docs/Access画面品質規約.md','agents/builds/build-agent/docs/Access生成チェック.md']) {const target=path.join(root,name);assertRegular(target);files.push(target);}
    const spec = specificationRoot(root, project, method);
    assertRegular(path.join(spec, '規約', '開発規約.md'));
    walk(spec);
  }
  return [...new Set(files)].sort();
}

export function independentSpecPrefix(file, project) {
  const prefix = `${project}/spec/`;
  if (!file.startsWith(prefix)) return null;
  const remainder = file.slice(prefix.length), slash = remainder.indexOf('/');
  return slash > 0 ? prefix + remainder.slice(0, slash + 1) : null;
}
