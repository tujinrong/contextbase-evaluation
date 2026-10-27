import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const masters=JSON.parse(fs.readFileSync(path.join(root,'database/seed/approved-masters.json'),'utf8'));
const sample=JSON.parse(fs.readFileSync(path.join(root,'database/seed/sample.json'),'utf8'));
const literal=v=>v===null?'NULL':typeof v==='boolean'?(v?'1':'0'):typeof v==='number'?String(v):`N'${v.replaceAll("'","''")}'`;
const audit={created_at:{$sql:'SYSUTCDATETIME()'},created_by:'verification-admin',updated_at:{$sql:'SYSUTCDATETIME()'},updated_by:'verification-admin',row_version:1};
const groups=[
 ['m_code_category',masters.categories.map(c=>({category_id:c.categoryId,category_name:c.categoryName,code_length:c.codeLength,allow_add:c.allowAdd,is_active:c.isActive,remarks:null,...audit}))],
 ['m_code',masters.codes.map(c=>({category_id:c.categoryId,code_value:c.codeValue,code_name:c.codeName,display_order:c.displayOrder,is_protected:c.isProtected,is_active:c.isActive,valid_from:c.validFrom,valid_to:c.validTo,remarks:null,...audit}))],
 ['m_class',sample.classes.map(c=>({...c,...audit}))],
 ['m_student',sample.students.map(s=>({...s,...audit}))],
 ['t_app_role',sample.actors],['t_write_guard',[{guard_id:1,lock_bit:false}]]
];
const marker='ACCESS-REBUILDER-TRAINING-V1';
let sql=`-- Synthetic dataset ${marker}; basis 2026-10-27, class validity through 2027-03-31.\nSET XACT_ABORT ON;\nBEGIN TRANSACTION;\nDECLARE @seed nvarchar(128)=(SELECT CONVERT(nvarchar(128),value) FROM sys.extended_properties WHERE class=0 AND name=N'AccessRebuilderSeed');\nIF @seed IS NOT NULL AND @seed<>N'${marker}' THROW 51010,'Different dataset owner; no changes.',1;\nIF @seed IS NULL AND (${groups.map(([table])=>`(SELECT COUNT_BIG(*) FROM dbo.[${table}])`).join('+')})<>0 THROW 51011,'Nonempty database without dataset marker; no changes.',1;\n`;
for(const [table,rows] of groups){
 const cols=Object.keys(rows[0]);const identity=table==='m_class'?'class_id':table==='m_student'?'student_id':null;
 const values=rows.map(r=>`(${cols.map(c=>r[c]?.$sql??literal(r[c])).join(',')})`).join(',\n');
 const comparable=cols.filter(c=>!['created_at','created_by','updated_at','updated_by','row_version'].includes(c));
 const expected=rows.map(r=>`(${comparable.map(c=>literal(r[c])).join(',')})`).join(',');
 sql+=`\nIF @seed IS NOT NULL AND EXISTS (SELECT * FROM (VALUES ${expected}) AS expected(${comparable.map(c=>`[${c}]`).join(',')}) EXCEPT SELECT ${comparable.map(c=>`[${c}]`).join(',')} FROM dbo.[${table}]) THROW 51012,'Seeded business values changed; no changes.',1;\nIF @seed IS NULL BEGIN\n${identity?`SET IDENTITY_INSERT dbo.[${table}] ON;\n`:''}INSERT dbo.[${table}] (${cols.map(c=>`[${c}]`).join(',')}) VALUES\n${values};\n${identity?`SET IDENTITY_INSERT dbo.[${table}] OFF;\n`:''}END;\n`;
}
sql+=`IF @seed IS NULL EXEC sys.sp_addextendedproperty @name=N'AccessRebuilderSeed',@value=N'${marker}';\nCOMMIT TRANSACTION;\n`;
fs.mkdirSync(path.join(root,'database/sql'),{recursive:true});fs.writeFileSync(path.join(root,'database/sql/002-seed.sql'),sql,'utf8');
process.stdout.write(JSON.stringify({categories:masters.categories.length,codes:masters.codes.length,classes:sample.classes.length,students:sample.students.length})+'\n');
