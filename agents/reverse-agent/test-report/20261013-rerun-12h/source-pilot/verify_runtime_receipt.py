"""Record complete tool-runtime inventory and import resolution without input-app execution."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--receipt', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
receipt_bytes = args.receipt.read_bytes()
value = json.loads(receipt_bytes)
root = Path(value['destination']).resolve()
actual = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts
          and p.suffix.lower() not in {'.pyc', '.pyo'}}
imports = {name: importlib.util.find_spec(name).origin for name in value['imports']}
if actual != value['files'] or imports != value['imports']:
    raise ValueError('frozen runtime or actual imports differ from the exact receipt')
output = {'schema': 'source-pilot-frozen-runtime-verification/1',
          'createdAt': datetime.now(timezone.utc).isoformat(), 'runtimeRoot': str(root),
          'receiptFile': str(args.receipt.resolve()), 'receiptSha256': hashlib.sha256(receipt_bytes).hexdigest(),
          'files': actual, 'fileCount': len(actual), 'actualImports': imports,
          'pythonExecutable': sys.executable, 'byteIdenticalToReceipt': True,
          'inputApplicationImportedOrExecuted': False}
with args.output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(output, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'file': str(args.output), 'fileCount': len(actual), 'importCount': len(imports),
                  'receiptSha256': output['receiptSha256']}, ensure_ascii=False))
