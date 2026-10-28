"""Publish one current result set; IBM i compilation is reported separately."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import datetime,hashlib,json
B=Path(__file__).resolve().parents[1];R=B/'build/test-results'
read=lambda n:json.loads((R/n).read_text('utf8'))
host=read('host/rpg-results.json');compact=read('compact/compact-static.json');state=read('state/state.json')
assert host['hostSucceeded'] and host['staticSucceeded'] and state['passed'] and compact['passed']==compact['total']
for item in [host,compact,state]:
 assert all(hashlib.sha256((B/p).read_bytes()).hexdigest()==h for p,h in item['sourceHashes'].items())
result=dict(projectId='test-project1',profileId='AS400_RPG',runId=state['runId'],recordedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),inputManifest='build/input-manifest.json',inputManifestSha256=hashlib.sha256((B/'build/input-manifest.json').read_bytes()).hexdigest(),hostSucceeded=True,cTests=host['cTests'],cFailures=host['cFailures'],hostStaticChecks=len(host['staticChecks']),compactStaticChecks=compact['total'],stateGateCTests=state['cTests'],stateGateStaticChecks=len(state['staticChecks']),sourceHashesMatch=True,generationStatus='SOURCE_UPDATED_NATIVE_NOT_RUN',targetUi='5250 Text 27x132 EDSTUDENT',nativeRegistryExecution='NOT_RUN',formalScore=None,scope=state['scope'],skipped=host['skipped'],evidence=['host/rpg-results.json','compact/compact-static.json','state/state.json'])
(R/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
(R/'README.md').write_text(f"""# AS400_RPG 現行検査結果

Windows Cホスト {host['cTests']}件、製品C状態ゲート {state['cTests']}件、参照等の静的検査 {len(host['staticChecks'])}件、検索・DDS配置 {compact['total']}件、状態・候補・生成器 {len(state['staticChecks'])}件がPASS。全記録のsource hashを現ソースへ照合済みです。

[host](host/rpg-results.json)、[配置](compact/compact-static.json)、[状態](state/state.json)にコマンド・終了値・生ログを保存します。同名結果を最新へ置換し、履歴はGitで管理します。ホスト試験exeは .tmp/host に置きます。

SQLRPGLE／DDS／CLのネイティブコンパイル、バインド、Db2、5250、CCSID往復、保存・競合は未実施。Cホスト検査や静的検査をIBM i合格へ転記しません。formalScore=null。
""",'utf8')
app=B/'build/app';app.mkdir(parents=True,exist_ok=True)
(app/'native-status.json').write_text(json.dumps(dict(profile='IBM i 7.5',status='NOT_BUILT',reason='IBM i compiler and runtime unavailable',sourceEntry='cl/BUILD.clle',hostProbesAreDistribution=False),indent=2)+'\n','utf8')
print(json.dumps(result,ensure_ascii=False))
