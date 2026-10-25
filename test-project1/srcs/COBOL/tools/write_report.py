"""Replace the fixed current summary using freshly matching build/test records."""
import datetime, hashlib, json
from evidence import ROOT, compiled_inputs, binary_hashes
report=ROOT/'build/test-results'
read=lambda p:json.loads((report/p).read_text('utf8'))
build=read('host-build/host-build.json');host=read('host-tests/host-tests.json');static=read('static/static.json');compact=read('compact/compact.json')
proof=json.loads((ROOT/'.tmp/host/build-evidence.json').read_text('utf8'))
assert build['succeeded'] and proof['succeeded']
assert build['compiledInputs']==proof['compiledInputs']==compact['compiledInputs']==compiled_inputs()
assert build['binaryHashes']==proof['binaries']==compact['binaryHashes']==binary_hashes()
assert all(item['passed']==item['total'] for item in [host,static,compact])
data=dict(projectId='test-project1',profileId='COBOL',runId=host['runId'],recordedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),inputManifest='build/input-manifest.json',inputManifestSha256=hashlib.sha256((ROOT/'build/input-manifest.json').read_bytes()).hexdigest(),buildSucceeded=True,compiledSourceHashesMatch=True,formalScore=None,host=dict(passed=host['passed'],total=host['total']),compact=dict(passed=compact['passed'],total=compact['total'],processCommands=len(compact['commands'])),static=dict(passed=static['passed'],total=static['total']),app='build/app/windows',limits=['Windows host build; not Linux CGI deployment','Rendering candidates and prompt state I/O use isolated fixtures','Real SQL, encrypted state table, real-clock expiry, browser acceptance and formal scoring not run'])
(report/'summary.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
(report/'README.md').write_text(f"""# COBOL 現行検査結果

build成功、host {host['passed']}/{host['total']}、追加回帰 {compact['passed']}/{compact['total']}、静的検査 {static['passed']}/{static['total']}。入力・バイナリーhashは現在のソースと照合済みです。

[build](host-build/host-build.json)、[host](host-tests/host-tests.json)、[追加回帰](compact/compact.json)、[静的検査](static/static.json)にコマンド・終了値と生ログを保存します。同名ファイルを最新結果で置換し、過去版はGit履歴で管理します。

Windowsホスト用CGI／保守CLIは[app](../app/windows/runtime.json)へ配置します。Linux CGI、実SQL、暗号化状態表統合、実時間期限、実ブラウザー、正式採点は未実施。候補読込みと確認状態I/Oにはfixtureを用い、訂正後CONFIRMは保存dispatchまでを検査します。formalScore=null。
""",'utf8')
print(json.dumps(data,ensure_ascii=False))
