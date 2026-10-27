#!/usr/bin/env node
import path from 'node:path';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {loadRequest,prepare,begin,complete,readJson,writeJson,outputManifest} from '../src/workflow.mjs';

try {
  const args=process.argv.slice(2), command=args.shift();
  const options={};
  while(args.length) { const key=args.shift(); if(!key.startsWith('--') || !args.length) throw Error('Expected --name value'); options[key.slice(2)]=args.shift(); }
  const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
  const context=loadRequest(root,options.profile ?? 'agents/access-rebuilder-agent/profiles/test-project1.json');
  let result;
  if(command==='prepare') result=prepare(context);
  else if(command==='begin-iteration') result=begin(context);
  else if(command==='complete-iteration') result=complete(context,options.result ?? '');
  else if(command==='status') result=fs.existsSync(context.ledger)?readJson(context.ledger):{iterations:[],maxIterations:context.profile.training.maxIterations};
  else if(command==='manifest') {
    const artifacts=directory=>fs.readdirSync(directory,{withFileTypes:true}).flatMap(entry=>{
      const file=path.join(directory,entry.name);
      if(entry.isSymbolicLink())throw Error('Linked build artifact refused');
      if(file===path.join(context.target,'build/generation/outputs.json'))return [];
      return entry.isDirectory()?artifacts(file):[file];
    });
    const {hash}=await import('../src/workflow.mjs');
    result={schema:'access-rebuilder-outputs/0.2',sourceHash:context.profile.source.sha256,recordedAt:new Date().toISOString(),outputs:outputManifest(context),artifacts:artifacts(path.join(context.target,'build')).map(file=>({path:path.relative(context.target,file).replaceAll('\\','/'),bytes:fs.statSync(file).size,sha256:hash(file)})),formalScore:null};
    writeJson(path.join(context.target,'build/generation/outputs.json'),result);
  } else throw Error('Usage: rebuild.mjs prepare|begin-iteration|complete-iteration --result <json>|status|manifest [--profile <path>]');
  process.stdout.write(JSON.stringify(result,null,2)+'\n');
} catch(error) { process.stderr.write(error.message+'\n'); process.exitCode=1; }
