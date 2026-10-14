from pathlib import Path
HERE=Path(__file__).absolute().parent
text=(HERE.parent/'split-retry-code-audit-r02/audit.py').read_text(encoding='utf8').replace('retry_split_failed_batch_r02.py','retry_split_failed_batch_r03.py')
(HERE/'audit.py').write_text(text,encoding='utf8')
out=HERE.parent/'split-retry-code-audit-r05';out.mkdir(exist_ok=False)
delta=(HERE.parent/'split-retry-code-audit-r03/delta.py').read_text(encoding='utf8').replace('split-retry-code-audit-r02/audit.py','split-retry-code-audit-r04/audit.py')
(out/'delta.py').write_text(delta,encoding='utf8')
