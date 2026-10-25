"""Run the current host test driver; fixture source files remain independent."""
from pathlib import Path
import argparse,subprocess,sys
BASE=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--report-dir',type=Path,default=BASE/'.tmp/fixture-results');a=p.parse_args()
raise SystemExit(subprocess.call([sys.executable,'-X','utf8',str(BASE/'tools/test_host.py'),'--report-dir',str(a.report_dir),'--run-id','fixture-check'],cwd=BASE))
