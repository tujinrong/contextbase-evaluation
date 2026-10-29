// The selected project's routing index is the authority for registered methods.
import fs from 'node:fs';
import path from 'node:path';

export const validProject = value => /^(?:sample|test)-project[1-9]\d*$/.test(value ?? '');
export const validProfile = value => /^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$/.test(value ?? '') && !/\.{2}|\.$/.test(value) && !/^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)/i.test(value);

export function projectProfiles(root, project) {
  if (!validProject(project)) throw new Error('Invalid project scope.');
  const index = path.join(root, project, 'spec', 'README.md');
  const stat = fs.lstatSync(index);
  if (!stat.isFile() || stat.isSymbolicLink() || fs.realpathSync(index).toLowerCase() !== path.resolve(index).toLowerCase()) throw new Error('Regular project specification index required.');
  const lines = fs.readFileSync(index, 'utf8').split(/\r?\n/);
  const cells = line => line.trim().slice(1, -1).split('|').map(value => value.trim().replace(/^`|`$/g, ''));
  let headers, methods = [];
  for (const line of lines) {
    if (!/^\s*\|.*\|\s*$/.test(line)) { headers = undefined; continue; }
    const row = cells(line);
    if (row.includes('方式ID') && row.includes('specRoot') && row.includes('sourceRoot')) { headers = row; continue; }
    if (!headers || row.every(value => /^:?-{3,}:?$/.test(value))) continue;
    const method = row[headers.indexOf('方式ID')];
    if (!validProfile(method) || row[headers.indexOf('specRoot')] !== `${project}/spec/${method}/` || row[headers.indexOf('sourceRoot')] !== `${project}/srcs/${method}/` || methods.includes(method)) throw new Error(`Invalid/duplicate registered specification scope: ${method}`);
    methods.push(method);
  }
  if (!methods.length) throw new Error('Project specification index has no registered method scopes.');
  return methods;
}

export function selectedProfiles(root, project, profile) {
  const registered = projectProfiles(root, project);
  if (profile !== undefined && !registered.includes(profile)) throw new Error(`Profile is not registered in ${project}: ${profile}`);
  return profile ? [profile] : registered;
}
