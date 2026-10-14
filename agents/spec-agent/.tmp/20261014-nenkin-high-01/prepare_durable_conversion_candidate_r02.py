from pathlib import Path
import ast, hashlib, json
ROOT=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
old=ROOT/'prepare_durable_conversion_candidate_r01.py'
failure={'schema':'spec-agent-durable-conversion-candidate-attempt/1','status':'PREPARATION_FAILED_METADATA_FIELD_LOOKUP',
    'helper':str(old),'helperSha256':hashlib.sha256(old.read_bytes()).hexdigest(),
    'errorType':'KeyError','error':'table','correction':'The current profile names its TABLE metadata tableException; no converter logic or input data change is needed.',
    'candidateFilesCreated':False,'activeComponentsModified':False,'authoringMarkersExecuted':False,
    'actualXlsxOrPdfAuthored':False,'sourceOrOldOutputRead':False}
path=REPORT/'durable-conversion-candidate-attempt-r01.json'
with path.open('x',encoding='utf-8',newline='\n') as f:
    json.dump(failure,f,ensure_ascii=False,indent=2)
    f.write('\n')
source=old.read_text(encoding='utf-8').replace("['cover','normal','itemList','table','generalList','preamble',",
    "['cover','normal','itemList','tableException','generalList','preamble',",1)
source=source.replace("profile['table']['declaredContentColumns']", "profile['tableException']['declaredContentColumns']",1)
source=source.replace("report_path=REPORT/'durable-conversion-candidate-preparation-r01.json'",
    "result['priorPreparationFailure']={'path':str(REPORT/'durable-conversion-candidate-attempt-r01.json'),'sha256':hashlib.sha256((REPORT/'durable-conversion-candidate-attempt-r01.json').read_bytes()).hexdigest()}\nreport_path=REPORT/'durable-conversion-candidate-preparation-r02.json'",1)
ast.parse(source)
new=ROOT/'prepare_durable_conversion_candidate_r02_actual.py'
with new.open('x',encoding='utf-8',newline='\n') as f:
    f.write(source)
print(hashlib.sha256(new.read_bytes()).hexdigest())
