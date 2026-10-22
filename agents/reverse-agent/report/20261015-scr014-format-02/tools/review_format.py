"""Fresh independent AI review of a user-requested presentation revision."""
import json,sys,datetime
from pathlib import Path
W=Path(__file__).resolve().parent; REV=W.parents[1];R=REV/'report'/W.name
sys.dont_write_bytecode=True;sys.path[:0]=[str(REV/'.tmp/20261013-rerun-12h/source-only/runtime-code/source-13/src'),str(REV/'.tmp/20261013-rerun-12h/engine-runtime-deps'),str(REV/'.tmp/session-python-deps')]
from contextbase.ai import workflow,prompts
base=json.loads((R/'baseline.json').read_bytes());old=REV/'.tmp/20261015-scr014-pilot-01'
definition=workflow.select_document(old/'jobs/plan/plan-verified.json','SCR-014')
prompts.REVIEW+='\n今回の最新ユーザー指定：成果物の「根拠：ファイル:行」はreportへ移設し、処理手順が多い箇所は1.、1.1.、1.2.、2.の階層へ整理する。根拠段落を本文へ戻さない。これは版1.2の業務内容を保持する書式改訂で、新規解析の実績ではない。親見出し追加・順序維持・番号参照の整合・内容欠落を確認する。移設された根拠一覧は以下である。\n'+(R/'source-evidence.json').read_text('utf8')
prompts.REVIEW+='\n比較用の版1.2本文（今回の書式変更前の既存成果物）:\n'+(REV/'output/md'/definition['path']).read_text('utf8')+'\n機械的な可逆比較の記録（意味採点結果ではない）:\n'+(R/'format-equivalence.json').read_text('utf8')
result=workflow.review(Path(base['capsule']['path']),W/'draft'/definition['path'],definition,W/'jobs/review-02',timeout=1800,deadline='2026-10-15T16:30:00+00:00')
print(json.dumps(result,ensure_ascii=False))
