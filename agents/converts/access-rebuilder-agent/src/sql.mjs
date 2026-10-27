import fs from 'node:fs';
import path from 'node:path';
import {readJson,writeJson,hash} from './workflow.mjs';

export const identifier = name => `[${String(name).replaceAll(']',']]')}]`;
export function sqlType(field) {
  switch(field.type) {
    case 1: return 'bit'; case 2:return 'tinyint';case 3:return 'smallint';case 4:return 'int';
    case 5:return 'decimal(19,4)';case 6:return 'real';case 7:return 'float';case 8:return 'datetime2(3)';
    case 10: if(!Number.isInteger(field.size)||field.size<1||field.size>4000) throw Error(`Unsupported text size: ${field.name}`); return `nvarchar(${field.size})`;
    case 11:return 'varbinary(max)';case 12:return 'nvarchar(max)';case 15:return 'uniqueidentifier';case 16:return 'bigint';
    default:throw Error(`Unsupported DAO type ${field.type}: ${field.name}`);
  }
}
export function expression(source,fields,{ansi89=false}={}) {
  if(!source) return null;
  // Only the tested expression subset is accepted; identifiers and literals are tokenized.
  const names=new Set(fields.map(f=>f.name)), literals=[];
  let value=String(source).replace(/"((?:[^"]|"")*)"/g,(_,s)=>{literals.push(s.replaceAll('""','"'));return `__L${literals.length-1}__`;});
  value=value.replace(/\[([^\]]+)\]/g,(all,name)=>{if(!names.has(name))throw Error(`Unknown validation column: ${name}`);return identifier(name);});
  value=value.replace(/CStr\((\[[^\]]+\](?:\s*[+-]\s*\d+)?)\)/gi,'CONVERT(nvarchar(20),$1)').replace(/\bTrue\b/gi,'1').replace(/\bFalse\b/gi,'0').replaceAll('&','+');
  value=value.replace(/(\b(?:Not\s+)?Like\s+)__L(\d+)__/gi,(_,op,index)=>{if(!ansi89)throw Error('LIKE mode is not confirmed');const p=literals[Number(index)].replaceAll('%','[%]').replaceAll('_','[_]').replaceAll('*','%').replaceAll('?','_').replaceAll('[!','[^');return `${op}N'${p.replaceAll("'","''")}'`;});
  value=value.replace(/__L(\d+)__/g,(_,index)=>`N'${literals[Number(index)].replaceAll("'","''")}'`);
  const outside=value.replace(/N?'(?:[^']|'')*'/g,'').replace(/\[[^\]]*\]/g,'').replace(/CONVERT\(nvarchar\(20\),/gi,'(').replace(/\b(And|Or|Not|Is|Null|In|Like)\b/gi,'');
  if(/[^\d\s(),.+<>=!\-]/.test(outside))throw Error(`Unsupported Access validation expression: ${source}`);
  return value;
}
function defaultValue(value) {
  if(value===null||value===undefined||value==='')return null;
  if(/^\(?[-+]?\d+(\.\d+)?\)?$/.test(String(value))) return String(value);
  if(/^True$/i.test(value))return '1';if(/^False$/i.test(value))return '0';
  if(/^"[^"]*"$/.test(value))return `N'${value.slice(1,-1).replaceAll("'","''")}'`;
  throw Error(`Unsupported Access default: ${value}`);
}
export function generateSql(extraction) {
  if(extraction.status!=='PASS'||extraction.failures.length)throw Error('Extraction must pass');
  const lines=[`-- Source ACCDB SHA-256: ${extraction.sourceSha256}`,'-- Generated from DAO structure. Text uses explicit BIN2 comparison.','SET XACT_ABORT ON;','BEGIN TRANSACTION;'];
  const mapping=[];
  const widened=new Map();
  for(const relation of extraction.relations)for(const pair of relation.fields){
    const parent=extraction.tables.find(t=>t.name===relation.table)?.fields.find(f=>f.name===pair.name);
    const child=extraction.tables.find(t=>t.name===relation.foreignTable)?.fields.find(f=>f.name===pair.foreignName);
    if(parent?.type===10&&child?.type===10&&parent.size!==child.size){
      if(child.size>parent.size)throw Error(`Foreign-key parent capacity requires explicit design: ${relation.name}`);
      widened.set(`${relation.foreignTable}.${pair.foreignName}`,parent.size);
    }
  }
  for(const table of extraction.tables) {
    if(table.linked)throw Error(`External linked table requires explicit migration: ${table.name}`);
    const indexes=Array.isArray(table.indexes)?table.indexes:[table.indexes];const primary=indexes.find(i=>i.primary);const keys=new Set(primary?.fields.map(f=>f.name));
    const columns=table.fields.map(field=>{
      const prop=field.properties, targetSize=widened.get(`${table.name}.${field.name}`), type=sqlType(targetSize?{...field,size:targetSize}:field);let text=`  ${identifier(field.name)} ${type}`;
      if(type.startsWith('nvarchar'))text+=' COLLATE Latin1_General_100_BIN2';
      if(field.attributes&16){if(!['int','bigint'].includes(type))throw Error('Unsupported AutoNumber type');text+=' IDENTITY(1,1)';}
      text+=prop.Required||keys.has(field.name)?' NOT NULL':' NULL';const def=defaultValue(prop.DefaultValue);if(def!==null)text+=` DEFAULT (${def})`;
      mapping.push({table:table.name,column:field.name,daoType:field.type,accessSize:field.size,sqlType:type,capacityAlignment:targetSize?'foreign-key physical alignment with source-length CHECK':null,identity:!!(field.attributes&16),required:!!(prop.Required||keys.has(field.name)),sourceSha256:extraction.sourceSha256});
      return text;
    });
    if(primary)columns.push(`  CONSTRAINT ${identifier(primary.name)} PRIMARY KEY (${primary.fields.map(f=>identifier(f.name)).join(', ')})`);
    lines.push(`CREATE TABLE dbo.${identifier(table.name)} (\n${columns.join(',\n')}\n);`);
    let count=0;
    for(const field of table.fields) {
      const prop=field.properties;
      if(widened.has(`${table.name}.${field.name}`))lines.push(`ALTER TABLE dbo.${identifier(table.name)} ADD CONSTRAINT ${identifier(`ck_${table.name}_${++count}`)} CHECK (DATALENGTH(${identifier(field.name)})<=${field.size*2});`);
      if([10,12].includes(field.type)&&prop.AllowZeroLength===false)lines.push(`ALTER TABLE dbo.${identifier(table.name)} ADD CONSTRAINT ${identifier(`ck_${table.name}_${++count}`)} CHECK (${identifier(field.name)} IS NULL OR DATALENGTH(${identifier(field.name)})>0);`);
      if(prop.ValidationRule){const raw=String(prop.ValidationRule);const full=/^[<>!=]/.test(raw)?`${identifier(field.name)}${raw}`:raw;lines.push(`ALTER TABLE dbo.${identifier(table.name)} ADD CONSTRAINT ${identifier(`ck_${table.name}_${++count}`)} CHECK (${expression(full,table.fields,{ansi89:extraction.databaseProperties['ANSI Query Mode']===0})});`);}
    }
    if(table.properties.ValidationRule) lines.push(`ALTER TABLE dbo.${identifier(table.name)} ADD CONSTRAINT ${identifier(`ck_${table.name}_record`)} CHECK (${expression(table.properties.ValidationRule,table.fields,{ansi89:extraction.databaseProperties['ANSI Query Mode']===0})});`);
    for(const index of indexes.filter(i=>!i.primary)) lines.push(`CREATE ${index.unique?'UNIQUE ':''}INDEX ${identifier(index.name)} ON dbo.${identifier(table.name)} (${index.fields.map(f=>identifier(f.name)+(f.attributes&1?' DESC':'')).join(', ')});`);
  }
  for(const relation of extraction.relations) {
    if(relation.attributes!==0)throw Error(`Unsupported relationship options: ${relation.name}`);
    lines.push(`ALTER TABLE dbo.${identifier(relation.foreignTable)} ADD CONSTRAINT ${identifier(relation.name)} FOREIGN KEY (${relation.fields.map(f=>identifier(f.foreignName)).join(', ')}) REFERENCES dbo.${identifier(relation.table)} (${relation.fields.map(f=>identifier(f.name)).join(', ')});`);
  }
  lines.push('COMMIT TRANSACTION;');
  return {sql:lines.join('\n\n')+'\n',mapping};
}
export function emitSql(extractionFile,target) {
  const extraction=readJson(extractionFile),generated=generateSql(extraction);
  const out=path.join(target,'database/sql/001-schema.sql');fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,generated.sql,'utf8');
  writeJson(path.join(target,'database/schema/type-mapping.json'),{schema:'access-sqlserver-type-mapping/0.2',sourceSha256:extraction.sourceSha256,extractionSha256:hash(extractionFile),columns:generated.mapping,collation:'Latin1_General_100_BIN2',limitation:'DAO physical capacity retained; business scalar limits are validated separately by C#.'});
  return {tables:extraction.tables.length,relations:extraction.relations.length,columns:generated.mapping.length};
}
