import fs from 'node:fs';
import path from 'node:path';

// Test expectations and generated/scratch trees are never implementation inputs.
export function sourceFiles(directory, {excludeSpec=false}={}) {
  const skip=new Set(['.tmp','spec-eval','build','bin','obj','node_modules','dist','.vs','.git','__pycache__','test-report','test-evidence',...(excludeSpec?['spec']:[])]);
  const files=[];
  function walk(current) {
    const info=fs.lstatSync(current);
    if(!info.isDirectory()||info.isSymbolicLink()||fs.realpathSync(current).toLowerCase()!==path.resolve(current).toLowerCase())throw new Error(`Regular source directory required: ${current}`);
    for(const entry of fs.readdirSync(current,{withFileTypes:true})) {
      if(skip.has(entry.name))continue;
      const target=path.join(current,entry.name);
      if(entry.isSymbolicLink())throw new Error(`Linked source refused: ${target}`);
      if(entry.isDirectory())walk(target);
      else if(entry.isFile())files.push(target);
    }
  }
  walk(directory);
  return files;
}
