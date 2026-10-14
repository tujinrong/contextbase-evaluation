"""Append a generic strict material-path contract only; no source or AI answer edits."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json
REPO = Path(r'D:/開発/contextbase-evaluation')
RUN = REPO/'agents/spec-agent/.tmp/20261014-nenkin-high-01'
AUDIT = REPO/'agents/spec-agent/report/20261014-nenkin-high-01/independent-audit'
OLD = RUN/'review_plan_with_scope_r05.py'
OLD_SHA = '9d5ec80c5fd3efe2044302104a64ff928777fd98d3cdd0e0c8ef0ff301ee5802'
NEW = RUN/'review_plan_with_scope_r06.py'
OUT = AUDIT/'scoped-plan-wrapper-review-r06.json'

def safe(path):
    path = Path(path).absolute()
    for node in (path, *path.parents):
        if node.is_symlink() or (node.exists() and getattr(node.lstat(), 'st_file_attributes', 0)&0x400):
            raise ValueError('Linked path refused before read/write')
    return path.resolve()

def sha(path):
    return hashlib.sha256(safe(path).read_bytes()).hexdigest()

assert sha(OLD) == OLD_SHA and not safe(NEW).exists() and not safe(OUT).exists()
original = safe(OLD).read_bytes().decode('utf-8')
tree = ast.parse(original)
assignment = next(node for node in tree.body if isinstance(node, ast.Assign) and
                  any(isinstance(target, ast.Name) and target.id == 'SCOPE_TASK' for target in node.targets))
assert isinstance(assignment.value, ast.Constant) and isinstance(assignment.value.value, str)
addition = '''
提出前に、原文materialのpath契約を全objectで照合してください。
sourcePathsRead、subjects.sourcePaths、scopeLimits.sourcePaths、reachability.searchScope、
全references[].pathに記載できる原文識別子は、現在のmanifestに含まれるentry.path、
sources/+entry.path、entry.indexedのいずれかとの完全一致だけです。収録179原文の外は含めません。
ワイルドカード（*、**、/**/*等）、ディレクトリ、検索式、未収録pathを記載しません。
manifest.jsonはinventoryとしてsourcePathsRead又はscopeLimits.sourcePathsに限り使用でき、
subjects.sourcePaths、reachability.searchScope、原文referencesへ含めません。
原文のcanonical origin（entry.path）へ正規化して比較し、引用した全originをsourcePathsReadの
読了申告範囲へ含めます。未読原文を申告へ追加して通過させず、実際の探索と申告を一致させます。
reachabilityのGROUP自身・entryPoints・callers・registrationsの全referencesのoriginは、
そのGROUPのsearchScopeの原文origin集合に含めます。subject自身の全referencesのoriginは、
そのsubjectのsourcePathsの原文origin集合に含めます。subject.documentIdsと
documentCoverage.subjectIdsは双方向で一致させ、計画の全文書を各一度だけ評価します。
全evidence-bearing objectのbasisと自身のreferencesは既存契約どおりです。
この照合のためにapprovedを強制したり、文書・subject・coverage・探索範囲を減らしたり、
原文根拠を創作したりしません。実際の根拠不足・未知・重要な欠陥はそのまま報告してください。
'''
lines = original.splitlines(keepends=True)
start = sum(len(line.encode('utf-8')) for line in lines[:assignment.value.lineno-1])+assignment.value.col_offset
end = sum(len(line.encode('utf-8')) for line in lines[:assignment.value.end_lineno-1])+assignment.value.end_col_offset
original_bytes = original.encode('utf-8')
updated = (original_bytes[:start]+repr(assignment.value.value+addition).encode('utf-8')+
           original_bytes[end:]).decode('utf-8')
new_tree = ast.parse(updated)
new_assignment = next(node for node in new_tree.body if isinstance(node, ast.Assign) and
                      any(isinstance(target, ast.Name) and target.id == 'SCOPE_TASK' for target in node.targets))
old_non_scope = [ast.dump(node, include_attributes=False) for node in tree.body if node is not assignment]
new_non_scope = [ast.dump(node, include_attributes=False) for node in new_tree.body if node is not new_assignment]
assert old_non_scope == new_non_scope and new_assignment.value.value == assignment.value.value+addition
with safe(NEW).open('xb') as stream:
    stream.write(updated.encode('utf-8'))
assert sha(OLD) == OLD_SHA
result = {'schema': 'spec-agent-scoped-plan-wrapper-code-review/1',
          'createdUtc': datetime.now(timezone.utc).isoformat(), 'previousHelper': str(safe(OLD)),
          'previousHelperSha256': OLD_SHA, 'helper': str(safe(NEW)), 'helperSha256': sha(NEW),
          'scopeTaskAppendOnly': True, 'allOtherTopLevelAstIdentical': True,
          'allFunctionsAstIdentical': True, 'originalPrefixAndSuffixBytesPreserved': True,
          'appendedGenericContract': addition, 'snapshotContextRuntimeDeadlineChanged': False,
          'coreValidatorSchemaChanged': False, 'businessFactsOrProseAdded': False,
          'sourceApplicationDatabaseExecuted': False, 'providerExecuted': False,
          'originalAnswerBytesModified': False,
          'creationToolCorrection': 'An initial AST offset attempt used character counts for UTF-8 byte offsets and was rejected by ast.parse before any helper/report write; byte offsets are now used.',
          'scope': 'CODE_ONLY_GENERIC_PATH_CONTRACT_DELTA_NOT_PLAN_SEMANTIC_APPROVAL'}
with safe(OUT).open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'helper': str(safe(NEW)), 'helperSha256': sha(NEW),
                  'report': str(safe(OUT)), 'reportSha256': sha(OUT)}, ensure_ascii=False))
