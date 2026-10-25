"""Publish only a current matching Windows sample build/test summary."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import datetime,hashlib,json,os
from evidence import ROOT,compiled_inputs,binary_hashes
from checked_sources import checked_source_hashes
from output_paths import write_json,write_latest
report=ROOT/'build/test-results'
run_id=os.environ.get('COBOL_RUN_ID','local-cobol')
inputs=compiled_inputs();binaries=binary_hashes()
manifest_sha=hashlib.sha256((ROOT/'build/input-manifest.json').read_bytes()).hexdigest()
read=lambda p:json.loads((report/p).read_text('utf-8'))
data={'projectId':'test-project1','profileId':'COBOL','runId':run_id,'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'VERIFICATION_FAILED','buildSucceeded':False,'applicationVerification':'NOT_ESTABLISHED','formalScore':None}
try:
 build=read('host-build/host-build.json')
 proof=json.loads((ROOT/'.tmp/host/build-evidence.json').read_text('utf-8'))
 if not build.get('succeeded') or not proof.get('succeeded'):raise ValueError('Current build did not succeed')
 if build.get('runId')!=run_id or build.get('inputManifestSha256')!=manifest_sha:raise ValueError('Build run/input provenance is stale')
 if build.get('compiledInputs')!=inputs or proof.get('compiledInputs')!=inputs or build.get('binaryHashes')!=binaries or proof.get('binaries')!=binaries:raise ValueError('Build/source/binary fingerprint mismatch')
 suites={}
 for name,path,runner in [('host','host-tests/host-tests.json','host_tests.py'),('static','static/static.json','static_check.py'),('text','text/text.json','test_text.py')]:
  suite=read(path);expected_runner=hashlib.sha256((ROOT/'tools'/runner).read_bytes()).hexdigest()
  if suite.get('runId')!=run_id or suite.get('inputManifestSha256')!=manifest_sha or suite.get('compiledInputs')!=inputs or suite.get('binaryHashes')!=binaries or suite.get('runnerSha256')!=expected_runner:raise ValueError(name+' suite provenance differs from current run/input/source/binary/runner')
  if suite.get('status')!='PASSED' or not suite.get('inputsUnchangedDuringTests') or not suite.get('total') or suite.get('passed')!=suite.get('total') or not all(row.get('passed') for row in suite.get('results',[])):raise ValueError(name+' suite did not pass or changed during tests')
  if name=='static' and suite.get('checkedSourceHashes')!=checked_source_hashes():raise ValueError('Static checked source/document hashes changed')
  suites[name]={'passed':suite['passed'],'total':suite['total'],'record':path,'runnerSha256':expected_runner}
 data.update(status='VERIFIED_WITH_LIMITS',buildSucceeded=True,generationStatus='REGENERATED',targetTextStatus='IMPLEMENTED_WINDOWS_SAMPLE',applicationVerification='SYNTHETIC_CONTROLS_AND_DATA_BOUNDARIES_PASSED',nativeExecution='COMPILED_AND_SYNTHETIC_UNIT_TESTED',compiledSourceHashesMatch=True,inputManifest='build/input-manifest.json',inputManifestSha256=manifest_sha,compiledInputs=inputs,binaryHashes=binaries,suites=suites,legacyHttpUtilityChecks=read('host-tests/host-tests.json').get('legacyHttpUtilityChecks',0),legacyHtmlAcceptance='NOT_SELECTED_NOT_COUNTED',app='build/app/windows',limits=['Physical Console glyph/IME/key acceptance has not run','Real SQL transactions, encrypted runtime-state table, expiry and concurrent saves have not run','Authentication intentionally absent: fixed sample-user/Administrator is for this sample only','Formal scoring has not run'])
except Exception as error:
 data['failure']=type(error).__name__+': '+str(error)
 write_json(report/'summary.json',data);print(json.dumps(data,ensure_ascii=False));raise SystemExit(1)
write_json(report/'summary.json',data)
write_latest(report/'README.md',f'''# COBOL Windows Text サンプル 検査結果

今回の入力・現在のコンパイル対象・実行バイナリー・各runnerのSHAを照合済みです。Windows x64ビルド成功、共通境界 {suites['host']['passed']}/{suites['host']['total']}、Text制御 {suites['text']['passed']}/{suites['text']['total']}、静的検査 {suites['static']['passed']}/{suites['static']['total']}。

[ビルド](host-build/host-build.json)、[共通境界](host-tests/host-tests.json)、[Text](text/text.json)、[静的検査](static/static.json)に今回のコマンド・終了値・生ログを記録します。旧HTTP decoder {data['legacyHttpUtilityChecks']}件は互換境界で、端末適合の件数へ読み替えません。旧HTML/CGI専用検査は正式ソースを保持し、今回targetの合格へ数えません。

画面・入力制御はproduction COBOLとsynthetic terminal fixture、Win32エンジンはsynthetic INPUT_RECORDを使用します。実Consoleのglyph/IME/物理キー、実SQL/暗号化状態表/同時保存、本番受入は未実施です。認証はユーザー指定により行わず、sample-user/Administrator固定。formalScore=null。
''')
print(json.dumps({k:v for k,v in data.items() if k not in ['compiledInputs','binaryHashes']},ensure_ascii=False))
