"""Prepare a fresh metadata-only root issuer for the inspected r05 writer."""
from pathlib import Path
import ast
import hashlib
import json

work = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
old = work / 'issue_author_activation_r01.py'
new = work / 'issue_author_activation_r02.py'
text = old.read_text(encoding='utf-8')
changes = {
    "DRIVER = RUN / 'nenkin_writer_driver_r04.py'": "DRIVER = RUN / 'nenkin_writer_driver_r05.py'",
    "DRIVER_SHA = 'ce836766e61f5abad0fc4d2abfe11b3c6e6588f4dc8b9d46f62f913f0cd8e664'": "DRIVER_SHA = '6b8e5456d96fabfda1bf43b6c17b6155167726492b10c0f9145473f243ee102c'",
    "audit = REPORT / 'writer-root-code-audit-r04.json'": "audit = REPORT / 'writer-root-code-audit-r05.json'",
    "writer.require(writer.sha(audit) == 'f1271a52da98ec3ebd430dccb50d32a1a30537fbccb79dbea3086e2ef37e2a96'": "writer.require(writer.sha(audit) == '673983cab479dbf6418ad0d816e30c9219e7cdfba2585fd255c0751212af897a'",
}
for before, after in changes.items():
    assert text.count(before) == 1
    text = text.replace(before, after)
ast.parse(text)
with new.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(text)
print(json.dumps({'path': str(new), 'sha256': hashlib.sha256(new.read_bytes()).hexdigest(), 'literalPointerChanges': len(changes), 'actualGrantCreated': False}, ensure_ascii=False))
