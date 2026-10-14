"""Fresh evidence writer for the literal-bound Markdown guard revision."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
base=HERE/'record_core_r16.py'
source=base.read_text(encoding='utf8')
source=source.replace('core-r16-full-r01','core-r16-full-r02')
source=source.replace("'core-r16-result.json'","'core-r16-result-r02.json'")
source=source.replace("'edge-markdown-baseline']:","'edge-markdown-baseline','edge-markdown-collision-reject']:")
source=source.replace("'core-r16-native-r01/edge-whole-token/diagram-001.png'",
 "'core-r16-full-r02/edge-whole-token/diagram-001.png','core-r16-full-r02/edge-markdown-baseline/diagram-001.png'")
source=source.replace("'markdownLabels':'baseline display unchanged; excluded from whole-token projection'",
 "'markdownLabels':'baseline display unchanged; literal-text binding required; excluded from whole-token projection'")
source=source.replace("'targetedPriorRun':{'tests':50", "'historicalTargetedPriorRevision':{'tests':50")
env={'__file__':str(base),'__name__':'fresh_evidence_writer'}
exec(compile(source,str(base),'exec'),env)
env['main']()
