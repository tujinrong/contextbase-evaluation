"""Idempotent preflight: an identical closed artifact skips; edited/foreign stops.
It intentionally never opens Access and never inserts or repairs existing data.
"""
import argparse,hashlib,json,sys
from pathlib import Path
def main():
    p=argparse.ArgumentParser(); p.add_argument('--database',type=Path,required=True); p.add_argument('--manifest',type=Path,required=True); a=p.parse_args()
    if not a.database.is_file() or not a.manifest.is_file(): print('STOP: missing database or ownership manifest'); return 2
    m=json.loads(a.manifest.read_text(encoding='utf-8')); current=hashlib.sha256(a.database.read_bytes()).hexdigest()
    same=m.get('datasetId')=='SP2-DEMO-01' and m.get('version')=='1.0' and current==m.get('artifactSha256')
    print('SKIP: identical owned dataset, no insertion' if same else 'STOP: modified or foreign artifact; no change')
    return 0 if same else 2
if __name__=='__main__': sys.exit(main())
