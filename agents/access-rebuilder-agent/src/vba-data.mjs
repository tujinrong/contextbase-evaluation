// Mechanical extraction of literal Array(...) records. No eval or VBA execution.
export function literalArrays(source,functionName,collectionName) {
  const functionMatch=source.match(new RegExp(`Public Function ${functionName}\\(\\)[\\s\\S]*?End Function`));
  if(!functionMatch)throw Error(`Missing literal function: ${functionName}`);
  const rows=[];
  for(const line of functionMatch[0].split(/\r?\n/)) {
    if(!line.includes(`${collectionName}.Add Array(`))continue;
    const value=line.match(/\.Add Array\((.*)\)\s*$/)?.[1];if(value===undefined)throw Error('Unsupported array syntax');
    const tokens=value.match(/"(?:[^"]|"")*"|True|False|-?\d+|[,\s]+/g)??[];
    if(tokens.join('')!==value)throw Error('Nonliteral VBA data rejected');
    rows.push(tokens.filter(t=>!/^[,\s]+$/.test(t)).map(t=>t.startsWith('"')?t.slice(1,-1).replaceAll('""','"'):t==='True'?true:t==='False'?false:Number(t)));
  }
  if(!rows.length)throw Error('No literal rows');
  return rows;
}
