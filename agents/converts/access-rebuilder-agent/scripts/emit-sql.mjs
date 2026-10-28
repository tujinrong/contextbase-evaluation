import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {loadRequest} from '../src/workflow.mjs';
import {emitSql} from '../src/sql.mjs';
try {
  const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../..');
  const context=loadRequest(root,process.argv[2]??'agents/converts/access-rebuilder-agent/profiles/sample-project1.json');
  process.stdout.write(JSON.stringify(emitSql(path.join(context.target,'build/generation/access-extraction.json'),context.target))+'\n');
} catch(error){process.stderr.write(error.message+'\n');process.exitCode=1;}
