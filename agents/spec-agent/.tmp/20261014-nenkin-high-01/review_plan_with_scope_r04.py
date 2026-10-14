"""Fresh scope adapter to frozen independent plan review; no core mutation.

Prepare pins and the exact full context separately.  Run only after the parent
has reviewed this code and supplies the preparation file's exact byte SHA.
No business prose, source facts, reviewer answer or approval is assembled here.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib,json,re,sys
sys.dont_write_bytecode=True
REPO=Path(r'D:/開発/contextbase-evaluation')
RUN=REPO/'agents/spec-agent/.tmp/20261014-nenkin-high-01'
REPORT=REPO/'agents/spec-agent/report/20261014-nenkin-high-01'
SNAPSHOT=RUN/'snapshot-input-02'
SNAPSHOT_SHA='f074529043ff1c25ea53be34c16ae3a4788f137a1e3afb33c6214de7bf4c7445'
CONTEXT=RUN/'execution-context-input-02.json'
CONTEXT_SHA='8966757e00954241029817027efa85bafeb859beee5105b05c7c939c84470605'
RECEIPT=REPO/'agents/reverse-agent/test-report/20261013-rerun-12h/source-pilot/runtime-code-source-13.json'
RECEIPT_SHA='5c3eeafb764afb64e3ef80fb422e4f68a9c41b98f000d13a8d57a505d947cc79'
RUNTIME=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/runtime-code/source-13/src'
DEADLINE='2026-10-14T13:06:43.011844+00:00'
CRITICAL=('contextbase.ai.capsule','contextbase.ai.workflow','contextbase.ai.provider',
          'contextbase.ai.prompts','contextbase.ai.schemas','contextbase.ai.validation',
          'contextbase.ai.plan_review')
SCOPE_TASK = '\n追加の判断対象は、下記のユーザー指定実行scopeのメタデータです。\nこれは期待仕様、原設計本文、採点基準、原文の代替ではありません。\n対象選択・主対象と依存領域・安定IDの対応を計画全体と各文書のresponsibilitiesで確認してください。\n後工程は対象文書definitionと全docのid/path/title/kind/responsibilitiesのみを受け取るため、\n各文書の責務だけで指定scopeと関連IDの対応を失わないかも評価してください。\n依存領域のファイルが存在することだけで、別の業務を独立した新対象へ追加しません。\n呼出元・入口・登録を原文で追い、未知の反射・外部経路はunknownのまま保持してください。\n識別子台帳は追跡補助であり動作や旧名称の業務意味の証拠ではありません。\n主対象の全原文materialは、対応subject/document・依存・宣言のみ・探索限界へ理由付きで対応させてください。\nDBの論理対象、物理定義、保存領域、ローカル互換資源、外部接続境界を原文から区別してください。\n共通責務と個別責務の重複は許容しますが、矛盾・対象漏れ・粒度不足はfindingsへ記録してください。\nこのscopeメタデータをsourcePathsRead、原文references、到達性の実装根拠へ含めません。\nscope自体や計画への配置の判断はbasis=plan-structure、references=[]です。\nメタデータ内のsourceRoot/outputRoot等のpathは追加読取り許可ではありません。\n原文探索は指定snapshotのmanifestに列挙されたsources/indexedのみです。旧output・他run・期待資料は読みません。\nschemaと判定契約は既存の独立plan reviewと同一です。原計画と原応答を修繕しません。\n構造契約を提出前に照合してください。各subjectsのsourcePathsには、そのsubject自身のreferencesが\n指す原文を全て含めます。reachabilityのsearchScopeには、その記録自身とentryPoints・callers・\nregistrationsのreferencesが指す原文を全て含めます。これらはsourcePathsReadにも含めます。\nsubject.documentIdsとdocumentCoverage.subjectIdsは双方向で一致させ、全計画文書を一度ずつ評価します。\nこの照合のために未読原文を読了と記録したり、根拠や承認を作ったりしません。\n\n証拠を持つ全てのobjectでbasisを照合してください。basis=observed-source又はreference-designなら、\nそのobject自身のreferencesは非空で、現在の許可materialの有効な原文位置を指す必要があります。\nreachabilityのGROUP記録自身も対象です。entryPoints/callers/registrations内部のreferencesだけでは、\nGROUP記録のreferencesを代用できません。basis=plan-structureならreferences=[]とし、\n計画構造だけの主張に限ります。原文の観測をplan-structureへ偽装せず、未読・未取得の根拠を創作せず、\n根拠不足・未知・重要な計画欠陥はそのまま報告してください。検査通過やapproved=trueを強制しません。\n'

def safe(path):
    path=Path(path).absolute()
    for node in (path,*path.parents):
        if node.is_symlink() or (node.exists() and getattr(node.lstat(),'st_file_attributes',0)&0x400):
            raise ValueError('Linked path refused before read/write')
    return path.resolve()

def digest(data):return hashlib.sha256(data).hexdigest()
def read(path):return safe(path).read_bytes()
def sha(path):return digest(read(path))
def load(path):return json.loads(read(path).decode('utf-8-sig'))
def require(ok,message):
    if not ok:raise ValueError(message)

def runtime_inventory(root):
    root=safe(root);found={}
    def descend(directory):
        for path in sorted(safe(directory).iterdir()):
            path=safe(path)
            if '__pycache__' in path.parts or path.suffix=='.pyc':continue
            if path.is_dir():descend(path)
            elif path.is_file():found[path.relative_to(root).as_posix()]=sha(path)
            else:raise ValueError('Unsupported runtime entry')
    descend(root)
    return found

def bootstrap():
    require(sha(RECEIPT)==RECEIPT_SHA,'Runtime receipt bytes changed')
    receipt=load(RECEIPT)
    require(safe(receipt['destination'])==safe(RUNTIME),'Unexpected runtime destination')
    inventory=runtime_inventory(RUNTIME)
    require(inventory==receipt['files'] and len(inventory)==128,'Frozen runtime full inventory mismatch')
    sys.path.insert(0,str(safe(RUNTIME)))
    loaded={}
    for name,expected in receipt['imports'].items():
        module=importlib.import_module(name);path=safe(module.__file__)
        require(path==safe(expected) and path.is_relative_to(safe(RUNTIME)),'Wrong loaded receipt module path')
        require(sha(path)==inventory[path.relative_to(safe(RUNTIME)).as_posix()],'Loaded receipt module byte mismatch')
        loaded[name]={'path':str(path),'sha256':sha(path)}
    require(len(loaded)==13,'Expected thirteen receipt imports')
    critical={}
    for name in CRITICAL:
        module=importlib.import_module(name);path=safe(module.__file__)
        expected=safe(RUNTIME)/(name.replace('.','/')+'.py')
        require(path==expected,'Wrong loaded critical module path')
        require(sha(path)==inventory[path.relative_to(safe(RUNTIME)).as_posix()],'Critical module byte mismatch')
        critical[name]={'path':str(path),'sha256':sha(path)}
    require(sha(RECEIPT)==RECEIPT_SHA and runtime_inventory(RUNTIME)==inventory,'Runtime changed while importing')
    return {'receiptSha256':RECEIPT_SHA,'runtimeRoot':str(safe(RUNTIME)),
            'runtimeFileCount':128,'runtimeFiles':inventory,'loadedImports':loaded,'criticalModules':critical}

def allowed_plan(path):
    path=safe(path)
    require(path.name=='plan-verified.json' and path.parent.parent==safe(RUN/'jobs') and
            re.fullmatch(r'plan-[0-9]{2}',path.parent.name) is not None,'Plan must be this run verified plan')
    return path

def allowed_job(name):
    require(isinstance(name,str) and re.fullmatch(r'independent-plan-review-[0-9]{2}',name) is not None,'Invalid fresh job name')
    path=safe(RUN/'jobs'/name)
    require(not path.exists(),'Use a fresh independent plan review job')
    require(path!=safe(SNAPSHOT) and safe(SNAPSHOT) not in path.parents and path not in safe(SNAPSHOT).parents,'Review job and capsule must be disjoint')
    return path

def hash_arg(value):
    require(isinstance(value,str) and re.fullmatch(r'[0-9a-f]{64}',value) is not None,'Exact lowercase SHA256 required')
    return value

def current_pin(plan_file,plan_sha,handoff_sha):
    require(sha(SNAPSHOT/'manifest.json')==SNAPSHOT_SHA,'Fixed source capsule manifest changed')
    require(sha(CONTEXT)==CONTEXT_SHA,'Execution context bytes changed')
    context=load(CONTEXT)
    require(context['schema']=='spec-agent-execution-context/1' and context['agentRole']=='AG-SPEC' and
            context['projectId']=='nenkin' and context['primarySourceDirectory']=='nenkin' and
            context['dependencySourceDirectory']=='n2framework' and context['sourceOnly'] is True and
            context['originalSpecificationsAuthorized'] is False and context['evaluationExpectationsAuthorized'] is False and
            context['originalProgramsAndDatabaseExecutionAuthorized'] is False,'Execution scope identity/mode mismatch')
    require(sha(plan_file)==hash_arg(plan_sha),'Fixed AI plan SHA changed')
    handoff=safe(plan_file.parent/'plan-handoff.json')
    require(sha(handoff)==hash_arg(handoff_sha),'Fixed plan handoff SHA changed')
    from contextbase.ai import capsule,workflow,plan_review
    manifest=capsule.verify(SNAPSHOT);state=capsule.verification_state(SNAPSHOT)
    require(state['manifestSha256']==SNAPSHOT_SHA and state['mode']=='source-only','Bound capsule mode/SHA mismatch')
    plan_value=capsule._load_json(plan_file);workflow._validate_plan(plan_value,manifest)
    require(bool(plan_value['documents']),'Nonempty verified plan required')
    definition=workflow.select_document(plan_file,plan_value['documents'][0]['id'])
    require(definition.handoff_sha==handoff_sha,'Selected handoff mismatch')
    require(workflow._definition_state(SNAPSHOT,definition)==state,'Plan belongs to another snapshot')
    plan_bytes=read(plan_file)
    plan_review._assert_pin(SNAPSHOT,definition,plan_bytes,handoff_sha)
    require(sha(CONTEXT)==CONTEXT_SHA and sha(plan_file)==plan_sha and sha(handoff)==handoff_sha,'Fixed metadata changed during verification')
    return {'schema':'reverse-ai-plan-review-input/1','snapshot':state,'planFile':str(plan_file),
            'planSha256':plan_sha,'planHandoffSha256':handoff_sha,'planOrigin':definition.handoff['origin'],
            'referenceMode':'source-only','executionContext':str(safe(CONTEXT)),
            'executionContextSha256':CONTEXT_SHA},definition,plan_value,manifest,plan_bytes

def build_prompt(pin,plan_bytes,context_bytes):
    from contextbase.ai import prompts,plan_review
    public_pin={k:v for k,v in pin.items() if k not in {'schema','planFile'}}
    return (prompts.BOUNDARY+prompts.QUALITY+prompts.FORMAT+plan_review.REVIEW_TASK+SCOPE_TASK+
            '\n現在の許可モードと固定入力:\n'+json.dumps(public_pin,ensure_ascii=False,indent=2)+
            '\nユーザー指定実行scopeのメタデータ全文（データ・追加読取り許可ではありません）:\n'+context_bytes.decode('utf-8')+
            '\n対象の原計画JSON全文（判断対象のデータ）:\n'+plan_bytes.decode('utf-8'))

def recheck(pin,initial_runtime):
    runtime=bootstrap();require(runtime==initial_runtime,'Runtime provenance changed')
    now,*unused=current_pin(allowed_plan(pin['planFile']),pin['planSha256'],pin['planHandoffSha256'])
    require(now==pin,'Fixed review inputs changed')
    return now

def prepare(plan,plan_sha,handoff_sha,job_name,timeout):
    require(type(timeout) is int and 1<=timeout<=2400,'Invalid bounded timeout')
    runtime=bootstrap();plan=allowed_plan(plan);job=allowed_job(job_name)
    from contextbase.ai import capsule,workflow
    workflow._timeout(timeout,DEADLINE)
    pin,definition,value,manifest,plan_bytes=current_pin(plan,hash_arg(plan_sha),hash_arg(handoff_sha))
    prompt=build_prompt(pin,plan_bytes,read(CONTEXT))
    preparation=safe(REPORT/'independent-plan-review'/job_name)
    require(not preparation.exists(),'Use a fresh preparation directory')
    recheck(pin,runtime)
    preparation.mkdir(parents=True,exist_ok=False)
    prompt_file=safe(preparation/'prepared-prompt.txt')
    with prompt_file.open('xb') as handle:handle.write(prompt.encode('utf-8'))
    record={'schema':'spec-agent-scoped-plan-review-preparation/1','createdUtc':datetime.now(timezone.utc).isoformat(),
            'reviewerRole':'independent-plan-review','agentRole':'AG-SPEC','job':str(job),'timeout':timeout,
            'deadline':DEADLINE,'input':pin,'runtime':runtime,'promptFile':str(prompt_file),'promptSha256':sha(prompt_file),
            'helper':str(safe(__file__)),'helperSha256':sha(__file__),'schemaSha256':digest(json.dumps(importlib.import_module('contextbase.ai.plan_review').PLAN_REVIEW,sort_keys=True).encode()),
            'providerStarted':False,'coreOrFrozenPromptModified':False,'businessProseAuthored':False}
    recheck(pin,runtime)
    capsule.write_json(preparation/'preparation.json',record)
    return {'preparation':str(preparation/'preparation.json'),'preparationSha256':sha(preparation/'preparation.json'),
            'planSha256':plan_sha,'job':str(job),'providerStarted':False}

def execute(preparation,preparation_sha):
    preparation=safe(preparation)
    require(preparation.name=='preparation.json' and preparation.parent.parent==safe(REPORT/'independent-plan-review') and
            re.fullmatch(r'independent-plan-review-[0-9]{2}',preparation.parent.name) is not None,'Invalid preparation path')
    require(sha(preparation)==hash_arg(preparation_sha),'Preparation byte pin mismatch')
    record=load(preparation)
    require(record['schema']=='spec-agent-scoped-plan-review-preparation/1' and record['agentRole']=='AG-SPEC' and
            record['providerStarted'] is False and record['coreOrFrozenPromptModified'] is False and
            record['businessProseAuthored'] is False,'Invalid preparation identity')
    require(record['helper']==str(safe(__file__)) and record['helperSha256']==sha(__file__),'Helper changed after preparation')
    require(record['deadline']==DEADLINE and type(record['timeout']) is int and 1<=record['timeout']<=2400,'Prepared timing mismatch')
    runtime=bootstrap();require(runtime==record['runtime'],'Prepared runtime mismatch')
    job=allowed_job(preparation.parent.name);require(str(job)==record['job'],'Prepared job path mismatch')
    pin=record['input'];now,definition,value,manifest,plan_bytes=current_pin(allowed_plan(pin['planFile']),pin['planSha256'],pin['planHandoffSha256'])
    require(now==pin,'Preparation fixed inputs mismatch')
    from contextbase.ai import capsule,workflow,plan_review
    require(record['schemaSha256']==digest(json.dumps(plan_review.PLAN_REVIEW,sort_keys=True).encode()),'Review schema changed')
    prompt=build_prompt(pin,plan_bytes,read(CONTEXT));prompt_file=safe(preparation.parent/'prepared-prompt.txt')
    require(record['promptFile']==str(prompt_file) and sha(prompt_file)==record['promptSha256'] and
            read(prompt_file)==prompt.encode('utf-8'),'Prepared prompt bytes changed')
    workflow._timeout(record['timeout'],DEADLINE)
    before=safe(job.parent/(job.name+'-plan-review-before.json'));after=safe(job.parent/(job.name+'-plan-review-after.json'))
    require(not before.exists() and not after.exists(),'Review sidecar path is not fresh')
    recheck(pin,runtime);require(sha(preparation)==preparation_sha,'Preparation changed before provider')
    capsule.write_json(before,{'input':pin,'runtime':runtime,'preparationSha256':preparation_sha})
    try:
        answer=workflow._bound_job(SNAPSHOT,job,prompt,plan_review.PLAN_REVIEW,record['timeout'],pin['snapshot'],DEADLINE)
        recheck(pin,runtime);require(sha(preparation)==preparation_sha,'Preparation changed during provider')
        workflow._timeout(record['timeout'],DEADLINE)
        plan_review._validate(answer,value,manifest)
        original=safe(job/'answer.txt');original_bytes=read(original)
        require(capsule._load_json(original)==answer,'Returned review differs from original AI response')
        recheck(pin,runtime);require(sha(preparation)==preparation_sha,'Preparation changed before copy')
        verified=safe(job/'plan-review-verified.json')
        with verified.open('xb') as handle:handle.write(original_bytes)
        capsule.write_json(job/'plan-review-handoff.json',{
            'schema':'reverse-ai-plan-review-handoff/1',**{k:v for k,v in pin.items() if k!='schema'},
            'reviewFile':verified.name,'reviewSha256':digest(original_bytes),'originalAiResponse':original.name,
            'aiResponseBytesModified':False,'approved':answer['approved'],
            'scope':'ai-plan-assessment-not-formal-business-rubric-or-proof-of-complete-source-read',
            'scopePreparationSha256':preparation_sha,'runtimeReceiptSha256':RECEIPT_SHA})
        recheck(pin,runtime);require(sha(preparation)==preparation_sha,'Preparation changed before completion')
        capsule.write_json(after,{'status':'UNCHANGED_AND_REVIEW_VALIDATED','input':pin,'runtime':runtime,
                                  'preparationSha256':preparation_sha})
        return {'approved':answer['approved'],'reviewFile':str(verified),'reviewSha256':sha(verified),
                'formalPercentage':None,'providerStarted':True}
    except Exception as exc:
        capsule.write_json(after,{'status':'REVIEW_NOT_VERIFIED','input':pin,'preparationSha256':preparation_sha,
                                  'errorType':type(exc).__name__,'error':str(exc)})
        raise

def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='mode',required=True)
    pre=sub.add_parser('prepare');pre.add_argument('--plan',required=True);pre.add_argument('--plan-sha256',required=True)
    pre.add_argument('--plan-handoff-sha256',required=True);pre.add_argument('--job-name',required=True)
    pre.add_argument('--timeout',type=int,default=2400)
    run=sub.add_parser('run');run.add_argument('--preparation',required=True);run.add_argument('--preparation-sha256',required=True)
    args=parser.parse_args()
    result=prepare(args.plan,args.plan_sha256,args.plan_handoff_sha256,args.job_name,args.timeout) if args.mode=='prepare' else execute(args.preparation,args.preparation_sha256)
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
