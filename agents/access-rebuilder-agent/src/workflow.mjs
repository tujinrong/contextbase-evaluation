import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

export const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex').toUpperCase();
export function readJson(file) { return JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '')); }
export function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), {recursive:true});
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}
export function safePath(root, relative) {
  if (typeof relative !== 'string' || !relative || path.isAbsolute(relative) || /(^|[\\/])\.\.([\\/]|$)/.test(relative)) throw Error('Unsafe relative path');
  const base = path.resolve(root), target = path.resolve(base, relative);
  if (!target.startsWith(base + path.sep)) throw Error('Path outside root');
  let current = base;
  for (const part of path.relative(base, target).split(path.sep)) {
    current = path.join(current, part);
    if (fs.existsSync(current) && fs.lstatSync(current).isSymbolicLink()) throw Error(`Linked path refused: ${relative}`);
  }
  return target;
}
export function loadRequest(root, profilePath) {
  const profile = readJson(safePath(root, profilePath));
  if (profile.schema !== 'access-rebuilder-request/0.1' || !/^test-project[\w-]+$/.test(profile.projectId)) throw Error('Unsupported request/project');
  if (!['implementation','verification'].includes(profile.phase) || profile.approval?.implementation !== 'authorized' || !profile.approval?.evidence || !profile.approval?.accessExtraction || !profile.approval?.codeGeneration) throw Error('Implementation is not authorized');
  const maximum = profile.training?.maxIterations;
  if (!Number.isInteger(maximum) || maximum < 1 || maximum > 2) throw Error('Training requires maxIterations between 1 and 2');
  const id = profile.target.profileId;
  if (!/^[\w.-]+$/.test(id) || profile.target.sourceRoot !== `${profile.projectId}/srcs/${id}` || profile.target.specRoot !== `${profile.projectId}/spec/${id}`) throw Error('Invalid target roots');
  if (!profile.source.file.startsWith(`${profile.projectId}/srcs/`) || !/\.(accdb|mdb)$/i.test(profile.source.file)) throw Error('Invalid Access source');
  const source = safePath(root, profile.source.file), target = safePath(root, profile.target.sourceRoot);
  if (source.startsWith(target + path.sep)) throw Error('Input cannot be inside output');
  if (hash(source) !== profile.source.sha256.toUpperCase()) throw Error('Source hash changed; review and freeze current input');
  if (profile.approval.databaseExecution && !profile.target.databaseConnection) throw Error('DB execution requires an explicit dedicated connection');
  return {root:path.resolve(root), profile, source, target, ledger:path.join(target,'build/generation/training.json')};
}
export function walk(root) {
  if (!fs.existsSync(root)) return [];
  return fs.readdirSync(root,{withFileTypes:true}).flatMap(entry => {
    const file = path.join(root,entry.name);
    if (entry.isSymbolicLink()) throw Error(`Linked artifact refused: ${file}`);
    if (['.tmp','bin','obj','.git','node_modules','build'].includes(entry.name)) return [];
    return entry.isDirectory() ? walk(file) : [file];
  });
}
export function outputManifest(context) {
  return walk(context.target).map(file=>({path:path.relative(context.target,file).replaceAll('\\','/'),bytes:fs.statSync(file).size,sha256:hash(file)})).sort((a,b)=>a.path.localeCompare(b.path));
}
export function prepare(context) {
  const {profile,target,root} = context;
  fs.mkdirSync(path.join(target,'.tmp'),{recursive:true});
  const referenceInputs=(profile.reference?.allowedFiles??[]).map(file=>({path:file,sha256:hash(safePath(root,file))}));
  const record = {schema:'access-rebuilder-inputs/0.3',projectId:profile.projectId,profileId:profile.target.profileId,source:profile.source,authorization:profile.approval,training:profile.training,revision:profile.revision??null,rebuildPolicy:profile.rebuildPolicy??null,referencePurpose:profile.reference?.purpose??null,referenceInputs,agentVersion:'0.3',rulesHash:hash(path.join(root,'agents/access-rebuilder-agent/docs/変換ルール.md')),recordedAt:new Date().toISOString()};
  writeJson(path.join(target,'build/generation/inputs.json'),record);
  return record;
}
export function begin(context) {
  const {profile,ledger,root} = context;
  const state = fs.existsSync(ledger) ? readJson(ledger) : {schema:'access-rebuilder-training/0.2',projectId:profile.projectId,profileId:profile.target.profileId,sourceHash:profile.source.sha256,maxIterations:profile.training.maxIterations,iterations:[]};
  if (state.sourceHash !== profile.source.sha256 || state.maxIterations !== profile.training.maxIterations) throw Error('Training identity or limit changed');
  if (state.iterations.some(item=>item.status==='running')) throw Error('An iteration is already running');
  if (state.iterations.length >= state.maxIterations) throw Error('Iteration limit reached; no third iteration permitted');
  state.iterations.push({number:state.iterations.length+1,status:'running',startedAt:new Date().toISOString(),rulesHash:hash(path.join(root,'agents/access-rebuilder-agent/docs/変換ルール.md'))});
  writeJson(ledger,state);
  return state;
}
export function complete(context,resultRelative) {
  const state = readJson(context.ledger), current = state.iterations.at(-1);
  if (!current || current.status!=='running') throw Error('No running iteration');
  if (!resultRelative.startsWith(`${context.profile.target.sourceRoot}/build/test-results/`)) throw Error('Result must be in target build/test-results');
  const resultPath = safePath(context.root,resultRelative), result = readJson(resultPath);
  if (result.sourceHash !== state.sourceHash || result.iteration !== current.number || !Array.isArray(result.checks) || !Array.isArray(result.findings)) throw Error('Result does not match current iteration');
  current.status='completed'; current.completedAt=new Date().toISOString();
  current.result=result; current.resultSha256=hash(resultPath); current.outputs=outputManifest(context);
  current.outputSetHash=crypto.createHash('sha256').update(JSON.stringify(current.outputs)).digest('hex').toUpperCase();
  writeJson(context.ledger,state);
  return state;
}
