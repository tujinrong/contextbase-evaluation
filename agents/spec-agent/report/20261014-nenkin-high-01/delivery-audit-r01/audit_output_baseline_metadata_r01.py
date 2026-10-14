"""Read baseline JSON metadata only; never touch actual output or business inputs."""
import hashlib,json,re
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath

REPORT=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01')
BASELINE=REPORT/'independent-audit/output-inventory-publish-baseline-r01.json'
TARGET=REPORT/'delivery-audit-r01/output-baseline-independent-metadata-audit-r01.json'
BASELINE_SHA='b66ea84af2fc79b8980358717a92b01136e28e59adda00f4079fa17eb5235449'
EXPECTED_OUTPUT=Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\output')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def checked_metadata_path(path):
    for p in (path,*path.parents):
        if p.exists():
            s=p.lstat()
            require(not p.is_symlink() and not(getattr(s,'st_file_attributes',0)&0x400),'linked/reparse metadata path')
    require(path.absolute()==path.resolve(),'nonexact metadata path')
    return path
def pairs(items):
    result={}
    for key,value in items:
        require(key not in result,'duplicate JSON key')
        result[key]=value
    return result
def canonical_metadata_relative(value):
    require(type(value) is str and bool(value),'relative path must be nonempty string')
    require('\\' not in value and ':' not in value,'backslash/colon relative path forbidden')
    require(not any(ord(c)<32 or ord(c)==127 for c in value),'control character relative path forbidden')
    p=PurePosixPath(value)
    require(not p.is_absolute() and p.as_posix()==value,'relative path must be normalized POSIX')
    require(all(part not in {'','..','.'} for part in p.parts),'relative path traversal forbidden')
    for part in p.parts:
        require(part[-1] not in {'.',' '},'Windows trailing-dot/space alias forbidden')
        require(not any(c in '<>"|?*' for c in part),'Windows invalid filename character')
        stem=part.split('.',1)[0].casefold()
        require(stem not in {'con','prn','aux','nul',*[f'com{i}' for i in range(1,10)],*[f'lpt{i}' for i in range(1,10)]},'Windows reserved filename')
    return value

checked_metadata_path(BASELINE);checked_metadata_path(TARGET)
raw=BASELINE.read_bytes();require(sha(raw)==BASELINE_SHA,'baseline SHA mismatch')
baseline=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
require(type(baseline) is dict and baseline.get('schema')=='spec-agent-output-change-baseline/1','baseline schema')
require(Path(baseline['outputRoot'])==EXPECTED_OUTPUT,'baseline outputRoot exact mismatch')
require(baseline.get('exists') is True,'baseline exists')
require(type(baseline.get('fileCount')) is int and baseline['fileCount']==906,'baseline count strict integer906')
files=baseline['files'];require(type(files) is dict and len(files)==906,'baseline files count906')
for relative,digest in files.items():
    canonical_metadata_relative(relative)
    require(type(digest) is str and re.fullmatch(r'[0-9a-f]{64}',digest) is not None,'invalid SHA256 metadata')
folded=[p.casefold() for p in files];require(len(set(folded))==len(files),'Windows casefold path collision')
require(baseline.get('oldOutputBodyReadByReviewer') is False and baseline.get('oldOutputProvidedToAiAuthor') is False,'baseline stated scope')
metadata_digest=sha(json.dumps(files,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
tests=[]
for relative in ('Excel/通常/合成01.xlsx','Markdown/合成/index.md','PDF/合成/file.pdf'):
    require(canonical_metadata_relative(relative)==relative,'positive canonical path')
    tests.append({'name':'positive-canonical-'+relative,'pass':True})
for relative in ('../escape.md','/absolute.md','C:/drive.md','a\\b.md','a//b.md','a/./b.md','a/../b.md','a:stream.md','a\x00.md','a\n.md','a/CON.md','a/NUL.txt','a/file.','a/file ','a/file?.md'):
    try:canonical_metadata_relative(relative)
    except ValueError:tests.append({'name':'reject-canonical-'+repr(relative),'pass':True})
    else:raise AssertionError('Bad path accepted '+repr(relative))
require(sha(BASELINE.read_bytes())==BASELINE_SHA,'baseline changed during metadata audit')
record={
 'schema':'spec-agent-output-baseline-independent-metadata-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'scope':'BASELINE_JSON_STRUCTURAL_METADATA_ONLY','status':'STRUCTURAL_METADATA_PASS_PUBLICATION_NOT_QUALIFIED',
 'baseline':{'path':str(BASELINE),'sha256':BASELINE_SHA,'schema':baseline['schema'],'createdUtc':baseline['createdUtc'],
             'outputRoot':baseline['outputRoot'],'exists':baseline['exists'],'fileCount':baseline['fileCount'],
             'fileMapEntries':len(files),'sortedPathHashMapSha256':metadata_digest,'statedScope':baseline['scope']},
 'checks':{'noDuplicateJsonKeys':True,'exactOutputRoot':True,'strictIntegerFileCount906':True,'all906RelativePathsCanonical':True,
           'all906Sha256Lowercase64':True,'noWindowsCasefoldFileCollisions':True,'baselineBytesUnchanged':True},
 'metadataOnlyCounts':{'firstPathComponent':dict(Counter(p.split('/',1)[0] for p in files)),
                     'extensions':dict(Counter(PurePosixPath(p).suffix.casefold() for p in files)),
                     'longestRelativePathCharacters':max(map(len,files))},
 'protectedGateRequirements':[
   {'gate':'OLD_OUTPUT_906','presentInBaseline':True,'additionalAtFutureExecution':'Exact current complete relative-path+SHA set equals this baseline; no link/reparse nodes, source/output race or publisher concurrency assumed away.'},
   {'gate':'OLD_SOURCE_345','presentInBaseline':False,'additionalAtFutureExecution':'Separate caller-pinned inventory/root/schema/count345 and allbyte before/after hash receipt; do not derive this gate from output906.'},
   {'gate':'SOURCE_INPUT','presentInBaseline':False,'additionalAtFutureExecution':'Explicit immutable input snapshot/capability closure and root/path/hash schema; raw source read scope stays outside this preparer.'},
   {'gate':'NEW_CAP_179','presentInBaseline':False,'additionalAtFutureExecution':'Separate pinned capability/schema/item-count179/complete status/selected membership and sourcebinding; final candidate file count is separately specified.'},
   {'gate':'SELECTED_NEW_DELIVERY','presentInBaseline':False,'additionalAtFutureExecution':'Explicit approved path→sha copy allowlist, nonempty complete deliverable sets/index/manifest/reviews; reject unknown, unfinished, missing, extra, or linked entries.'},
   {'gate':'ROLLBACK_AND_BACKUP','presentInBaseline':False,'additionalAtFutureExecution':'Explicit fresh backup/quarantine/staging paths plus durable step receipt and checksum906 restoration proof; never discard old or failed new bytes.'},
 ],
 'minimumReversibleWindowsCandidate':[
   'Prepare/check a fresh complete candidate from explicit caller-pinned files under the new run; no wildcard copy or recursive traversal follows links.',
   'Require same volume for final directory renames, exact allowed roots, every path/ancestor os.lstat reparse0x400 or is_symlink rejection, resolve exact, no existing backup/target alias.',
   'Immediately before switching, require current old output exact906 inventory and protected source/input/cap pins still unchanged; an exclusive operation lock can exclude cooperating publishers only.',
   'Write and flush an exclusive step journal. Rename old output to explicit fresh backup, verify its906 hashes, then rename the already verified candidate into exact output.',
   'Verify new explicit membership/checksums and all protected pins. On failure, preserve the new candidate at explicit fresh quarantine if present, restore the backup to exact output, and recheck906.',
   'Retain backup/journal/failure evidence; do not recursively delete either old output or failed new output during this operation.',
 ],
 'limits':['Only baseline JSON was inspected; actual output exists/count/hashes/links were not remeasured.',
           'Two directory renames are individually atomic on suitable Windows same-volume paths, but their pair is not an atomic transaction; output may be briefly absent.',
           'Path preflight is a limited filesystem actor gate and does not prove race-free exclusion against arbitrary concurrent processes.',
           'Baseline hashes cover file payloads only and do not inventory directories, empty directories, ACLs, ADS, file identity, timestamps, or reparse exclusions.',
           '906 is old-output file count; 345 and179 are separate protected-population claims not verified by this baseline.',
           'This current baseline cannot prove historical pre-prepare_run output preservation.',
           'No new candidate completion, semantic/visual qualification, adoption, or publication approval was inferred.'],
 'tests':tests,'syntheticPathCases':len(tests),
 'actualOutputInspected':False,'actualOutputBodyRead':False,'actualOutputHashesRead':False,
 'actualSourceOrInputRead':False,'actualNewCapabilityRead':False,'actualCopyExecuted':False,
 'actualRenameExecuted':False,'actualBackupExecuted':False,'actualRollbackExecuted':False,
 'providerExecuted':False,'authorExecuted':False,'markerExecuted':False,'semanticApproval':False,
 'formalQualityAssessed':False,'stateApproval':False,'wholeApproval':False,'adoption':False,'published':False,
 'reviewer':'/root/delivery_tools/registration_pdf_qa',
}
with TARGET.open('x',encoding='utf-8') as h:json.dump(record,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'path':str(TARGET),'sha256':sha(TARGET.read_bytes()),'baselineSha256':BASELINE_SHA,'fileMapEntries':len(files),'syntheticPathCases':len(tests),'metadataOnlyCounts':record['metadataOnlyCounts']},ensure_ascii=False))
