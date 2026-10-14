"""AST/text-only metadata exporter delta audit; no helper imports or job reads."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json

P = Path(__file__).resolve().parent
B = P.parents[2] / '.tmp/20261013-rerun-12h/training-assisted'
A = B / 'pin_search_basic_state_r06_v01.py'
C = B / 'pin_search_basic_state_r07_v01.py'
PREVIOUS = P / 'search-basic-r06-state-exporter-code-only-delta-review-r01.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
expected = {
    str(A): 'bc440ff83e15ef78827d0d3def0b03475b789c84c019608f80909014025127ea',
    str(C): '807ecfa2aaab8f56faf5b70567f176d0b8aa633b5ee2fd21f344f2a225f18709',
    str(PREVIOUS): 'c9859d962c3ec601b0744821a1fba4185fcc44733ffad7a4294d1bc147de7563',
}
assert all(sha(Path(p)) == h for p, h in expected.items())
old = A.read_text(encoding='utf-8-sig'); new = C.read_text(encoding='utf-8-sig')
mapping = {
    'state-projections/state-basic-search-r07-v01': 'state-projections/state-basic-search-r06-v01',
    'c954ae728a0a51040c2ab99dc0d20fc4416955483a158269e5014df7bd9e122b': '1c4c133b16d838a441eaae7f6f3734cd1276d679c4a250ca5e6c5d9bfce4157b',
    'searchbasic-r07-export-pin-v1.json': 'searchbasic-r06-export-pin-v1.json',
}
before_ast = ast.dump(ast.parse(old), include_attributes=False)
def allowed_delta(text):
    if any(text.count(k) != 1 for k in mapping): return False
    restored = text
    for k, v in mapping.items(): restored = restored.replace(k, v)
    try: tree = ast.dump(ast.parse(restored), include_attributes=False)
    except SyntaxError: return False
    return tree == before_ast and restored == old

probes = [('accepted-three-literals', new, True)]
for k in mapping:
    probes.append(('wrong-fixed-literal-' + str(len(probes)), new.replace(k, k + '-wrong'), False))
probes.extend([
    ('extra-top-level-call', new + '\nprovider_unapproved()\n', False),
    ('different-helper-sha', new.replace('ed1600aa3814c45ebc518f5c40205ea1631a8ec1a4aef908cab437f4e65967c0', '0' * 64), False),
    ('different-manifest-sha', new.replace('e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7', '1' * 64), False),
    ('different-document-id', new.replace('CSHARP_ASPNET-BAS-STU-01', 'CSHARP_ASPNET-BAS-STU-02'), False),
    ('false-native-claim', new.replace("'nativeSizeStateImagesVerified': False", "'nativeSizeStateImagesVerified': True"), False),
    ('allow-canonical-body-modification', new.replace("'canonicalSpecificationModified': False", "'canonicalSpecificationModified': True"), False),
    ('overwrite-report-instead-of-fresh', new.replace("target.open('x'", "target.open('w'"), False),
    ('change-unrelated-function', new.replace('def raw(', 'def unrelated_raw('), False),
])
results = [{'name': n, 'expected': e, 'actual': allowed_delta(t)} for n, t, e in probes]
assert len(results) == 12 and all(r['actual'] == r['expected'] for r in results)
oldfunctions = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(old).body if isinstance(n, ast.FunctionDef)}
newfunctions = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(new).body if isinstance(n, ast.FunctionDef)}
assert oldfunctions == newfunctions and len(newfunctions) == 3
restored = new
for k, v in mapping.items(): restored = restored.replace(k, v)
assert restored.encode('utf-8') == A.read_bytes()
assert all(sha(Path(p)) == h for p, h in expected.items())
out = P / 'search-basic-r07-state-exporter-code-only-delta-review-r01.json'
assert not out.exists()
record = {
    'schema': 'reverse-agent-code-only-metadata-exporter-delta-review/1',
    'createdUtc': datetime.now(timezone.utc).isoformat(), 'scope': 'STATIC_CODE_DELTA_AND_SYNTHETIC_ONLY',
    'referenceMode': 'training-assisted', 'status': 'PASS_EXACT_THREE_LITERAL_DELTA_ONLY',
    'before': str(A), 'beforeSha256': expected[str(A)], 'candidate': str(C), 'candidateSha256': expected[str(C)],
    'previousIndependentAudit': str(PREVIOUS), 'previousIndependentAuditSha256': expected[str(PREVIOUS)],
    'approvedDeltaFields': ['JOB', 'PARENT_SHA', 'fresh report filename'],
    'unchangedDocumentId': 'CSHARP_ASPNET-BAS-STU-01',
    'unchangedHelperSha256': 'ed1600aa3814c45ebc518f5c40205ea1631a8ec1a4aef908cab437f4e65967c0',
    'byteRestorationExact': True, 'astRestorationExact': True, 'unchangedFunctionNames': list(newfunctions),
    'syntheticProbes': results, 'probeCount': len(results), 'allPinnedBytesUnchanged': True, 'afterHashes': expected,
    'jobOrProductionFilesRead': False, 'sourceOrReferenceOrEvaluatorRead': False,
    'helperImported': False, 'topLevelExecuted': False, 'providerStarted': False, 'actualExportRun': False,
    'fullInheritedGuardReaudit': False, 'actualInputPreflightVerified': False,
    'semanticApproval': False, 'nativeApproval': False, 'formalQualityApproval': False,
    'wholeDocumentApproval': False, 'adoptionApproval': False, 'published': False,
}
out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'path': str(out), 'sha256': sha(out), 'probes': len(results), 'status': record['status']}, ensure_ascii=False))
