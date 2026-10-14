"""AST/text-only metadata exporter delta audit; no imported helper or job reads."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json

P = Path(__file__).resolve().parent
B = P.parents[2] / '.tmp/20261013-rerun-12h/training-assisted'
A = B / 'pin_registration_detail_state_v03.py'
C = B / 'pin_search_basic_state_r06_v01.py'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
expected = {str(A): '8985f34c25ad4840316e3a90e43596c66ba7049fea9caf091ba7595dec5d0a08',
            str(C): 'bc440ff83e15ef78827d0d3def0b03475b789c84c019608f80909014025127ea'}
assert all(sha(Path(p)) == h for p, h in expected.items())
old = A.read_text(encoding='utf-8-sig'); new = C.read_text(encoding='utf-8-sig')
mapping = {
    'state-projections/state-basic-search-r06-v01': 'state-projections/state-detail-registration-r05-v02',
    'CSHARP_ASPNET-BAS-STU-01': 'CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-002',
    '1c4c133b16d838a441eaae7f6f3734cd1276d679c4a250ca5e6c5d9bfce4157b': 'ecc68152d691076da8cc95c49387928d9e4f89d0f52aaaa5859708b547474cbd',
    'searchbasic-r06-export-pin-v1.json': 'registrationdetail-r05-export-pin-v1.json',
}
before_ast = ast.dump(ast.parse(old), include_attributes=False)
def allowed_delta(text):
    if any(text.count(k) != 1 for k in mapping): return False
    restored = text
    for k, v in mapping.items(): restored = restored.replace(k, v)
    try: tree = ast.dump(ast.parse(restored), include_attributes=False)
    except SyntaxError: return False
    return tree == before_ast and restored == old

probes = [('accepted-four-literals', new, True)]
for k in mapping:
    probes.append(('wrong-fixed-literal-' + str(len(probes)), new.replace(k, k + '-wrong'), False))
probes.extend([
    ('extra-top-level-call', new + '\nprovider_unapproved()\n', False),
    ('different-helper-sha', new.replace('ed1600aa3814c45ebc518f5c40205ea1631a8ec1a4aef908cab437f4e65967c0', '0' * 64), False),
    ('different-manifest-sha', new.replace('e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7', '1' * 64), False),
    ('false-native-claim', new.replace("'nativeSizeStateImagesVerified': False", "'nativeSizeStateImagesVerified': True"), False),
    ('allow-canonical-body-modification', new.replace("'canonicalSpecificationModified': False", "'canonicalSpecificationModified': True"), False),
    ('overwrite-report-instead-of-fresh', new.replace("target.open('x'", "target.open('w'"), False),
    ('change-unrelated-function', new.replace('def raw(', 'def unrelated_raw('), False),
])
results = [{'name': n, 'expected': e, 'actual': allowed_delta(t)} for n, t, e in probes]
assert all(r['actual'] == r['expected'] for r in results)
oldfunctions = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(old).body if isinstance(n, ast.FunctionDef)}
newfunctions = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(new).body if isinstance(n, ast.FunctionDef)}
assert oldfunctions == newfunctions and len(newfunctions) == 3
restored = new
for k, v in mapping.items(): restored = restored.replace(k, v)
assert restored.encode('utf-8') == A.read_bytes()
assert all(sha(Path(p)) == h for p, h in expected.items())
out = P / 'search-basic-r06-state-exporter-code-only-delta-review-r01.json'
assert not out.exists()
record = {'schema': 'reverse-agent-code-only-metadata-exporter-delta-review/1',
          'createdUtc': datetime.now(timezone.utc).isoformat(), 'scope': 'STATIC_CODE_DELTA_AND_SYNTHETIC_ONLY',
          'referenceMode': 'training-assisted', 'status': 'PASS_EXACT_FOUR_LITERAL_DELTA_ONLY',
          'before': str(A), 'beforeSha256': expected[str(A)], 'candidate': str(C), 'candidateSha256': expected[str(C)],
          'approvedDeltaFields': ['JOB', 'DOCUMENT_ID', 'PARENT_SHA', 'fresh report filename'],
          'byteRestorationExact': True, 'astRestorationExact': True, 'unchangedFunctionNames': list(newfunctions),
          'syntheticProbes': results, 'probeCount': len(results), 'allPinnedBytesUnchanged': True, 'afterHashes': expected,
          'jobOrProductionFilesRead': False, 'sourceOrReferenceOrEvaluatorRead': False,
          'helperImported': False, 'topLevelExecuted': False, 'providerStarted': False, 'actualExportRun': False,
          'fullInheritedGuardReaudit': False, 'actualInputPreflightVerified': False,
          'semanticApproval': False, 'nativeApproval': False, 'formalQualityApproval': False,
          'wholeDocumentApproval': False, 'adoptionApproval': False, 'published': False}
out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'path': str(out), 'sha256': sha(out), 'probes': len(results), 'status': record['status']}, ensure_ascii=False))
