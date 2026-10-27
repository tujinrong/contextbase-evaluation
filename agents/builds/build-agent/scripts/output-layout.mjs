import fs from 'node:fs';
import path from 'node:path';

export const profiles = ['VB.NET_WinForms', 'CSharp_WPF', 'CSharp_ASPNET', 'Vue_CSharpAPI', 'COBOL', 'AS400_RPG', 'Access'];

export function layout(root, project, profile) {
  if (!/^test-project[1-9]\d*$/.test(project) || (profile !== undefined && !profiles.includes(profile))) throw new Error('Invalid output scope.');
  const base = path.join(root, project, ...(profile ? ['srcs', profile] : []));
  const build = path.join(base, 'build');
  const scratch = path.join(base, '.tmp', 'build-agent');
  return {base, build, scratch, generation: path.join(build, 'generation'), tests: path.join(build, 'test-results')};
}

// Every component is checked before writing, including existing junctions.
export function ensureDirectory(directory) {
  const absolute = path.resolve(directory);
  const parent = path.dirname(absolute);
  if (parent !== absolute && !fs.existsSync(parent)) ensureDirectory(parent);
  if (fs.existsSync(absolute)) {
    const info = fs.lstatSync(absolute);
    if (!info.isDirectory() || info.isSymbolicLink()) throw new Error(`Regular output directory required: ${absolute}`);
    if (parent !== absolute && fs.realpathSync(absolute) !== absolute) throw new Error(`Redirected output directory refused: ${absolute}`);
  } else fs.mkdirSync(absolute);
}

export function writeLatest(target, data, scratch) {
  ensureDirectory(scratch);
  ensureDirectory(path.dirname(target));
  if (fs.existsSync(target) && (!fs.lstatSync(target).isFile() || fs.lstatSync(target).isSymbolicLink())) throw new Error(`Regular output file required: ${target}`);
  const temporary = path.join(scratch, `${path.basename(target)}.pending`);
  let pending;
  try { pending=fs.lstatSync(temporary); } catch(error) { if(error.code!=='ENOENT')throw error; }
  if (pending) {
    if(!pending.isFile()||pending.isSymbolicLink())throw new Error(`Regular staging file required: ${temporary}`);
    fs.unlinkSync(temporary);
  }
  fs.writeFileSync(temporary, data, {flag:'wx'});
  fs.renameSync(temporary, target);
}

export function writeJson(target, data, scratch) {
  writeLatest(target, JSON.stringify(data, null, 2) + '\n', scratch);
}
