"""Actual read-only verification and print-plan metadata for approved Menu candidate."""
import datetime,hashlib,json,types,sys
from pathlib import Path
D=Path('D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01/delivery')
P=D/'menu-pilot-01'
Q=Path('D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01/delivery-audit-r01/menu-pilot-01')
def digest(raw):return hashlib.sha256(raw).hexdigest()
def module(name,sha):
    path=D/name;raw=path.read_bytes();assert digest(raw)==sha
    mod=types.ModuleType('mechanical_'+path.stem);sys.modules[mod.__name__]=mod;mod.__file__=str(path)
    exec(compile(raw,str(path),'exec'),mod.__dict__);return mod
guard=module('prepare_native_print_annex_r02.py','ebe037fd2afa47c088dde179db715069ceda3000e29d2c976e2dd9fa2c6951d0')
reader=module('verify_xlsx_v2_62_r02.py','bf6f59881cd0377dca8dada139f47b000688019683dc07203629558e4c12ab09')
compare=module('verify_original_sheets_append_only_r02.py','208f4318bddaf510ef82d342ef9e38c93d6072e21765fa36d4eac17e434caafa')
projected_path=P/'native-print-annex-r01/model.json';model=guard.unique(guard.read(projected_path,'d08d90555338f744c20e764cda7a005af9766ddd76ce96b1f55fd6724cb42385').decode('utf8'))
receipt_path=P/'native-print-annex-r01/annex-receipt.json';proof=guard.verify(receipt_path,'353752c9c88c203f798149827956fee7cbf3ba1ebcd5a5b02933790905b72a91',projected_path,'d08d90555338f744c20e764cda7a005af9766ddd76ce96b1f55fd6724cb42385')
manifest_path=P/'xlsx-native-print-annex-r01/delivery-manifest.json';manifest_raw=guard.safe(manifest_path).read_bytes();manifest=guard.unique(manifest_raw.decode('utf8'))
assert manifest['status']=='EXPORTED_VERIFICATION_PENDING' and len(manifest['documents'])==1 and manifest['modelSha256']=='d08d90555338f744c20e764cda7a005af9766ddd76ce96b1f55fd6724cb42385'
document=model['documents'][0];actual=manifest['documents'][0];assert actual['documentId']==document['documentId']=='SCR-017'
xlsx_raw=guard.read(actual['xlsx'],actual['xlsxSha256']);old_raw=guard.read(P/'xlsx/Excel/basic/menu.xlsx','6c4a85237dc65cf7e1b1c6549d0209693effb83d2754ce68bc29518836e57e62')
verification=reader.verify(xlsx_raw,document,require_print=False)
comparison=compare.compare(old_raw,xlsx_raw,5)
assert len(actual['writtenCells'])==453 and actual['writtenCells'][:425]==guard.unique(guard.safe(P/'xlsx/delivery-manifest.json').read_text(encoding='utf8'))['documents'][0]['writtenCells']
report={'schema':'actual-native-print-annex-readonly-verification/1','createdUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope':'READ_ONLY_XLSX_MODEL_AND_ORIGINAL_SHEETS_EQUALITY','status':'PASS_MECHANICAL_NATIVE_PENDING','xlsx':actual['xlsx'],'xlsxSha256':actual['xlsxSha256'],
        'authorManifest':str(manifest_path),'authorManifestSha256':digest(manifest_raw),'model':str(projected_path),'modelSha256':manifest['modelSha256'],
        'verification':verification,'originalFiveSheetComparison':comparison,'original425WrittenCellsExactAndOrdered':True,
        'preparedAnnexReceiptSha256':proof['receiptSha256'],'originalPngPayloadsRetained':8,'markerRepeated':False,'actualPrintOrNativeQualified':False}
output=Q/'native-print-annex-actual-readonly-verification-r02.json';guard.safe(output,fresh=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
items=[]
for ordinal,spec in enumerate(document['sheets']):
    item={'ordinal':ordinal,'name':spec['name'],'kind':spec['role'],'lastRow':spec['lastRow'],'columns':spec['columns']}
    if spec['role']=='normal':item['printRanges']=proof['originalSheetPrintProjection'][0][ordinal]['printRanges'] if ordinal<5 else [spec['printArea']]
    elif spec['role']=='list':item.update(headerRow=spec['tables'][0]['headerRow'],itemList=spec.get('itemList',False))
    elif spec['role']=='table':item['headerRow']=spec['tables'][0]['headerRow']
    items.append(item)
plan={'schema':'print-metadata-v2-62/1','scope':'PRINT_METADATA_ONLY','ownedFreshArtifact':True,'documentId':document['documentId'],
      'source':{'path':actual['xlsx'],'sha256':actual['xlsxSha256']},'sourceAuthorReceipt':{'path':str(manifest_path),'sha256':digest(manifest_raw)},
      'sourceModel':{'path':str(projected_path),'sha256':manifest['modelSha256']},
      'nativePrintAnnexReceipt':{'path':str(receipt_path),'sha256':proof['receiptSha256']},'sheets':items}
plan_path=P/'native-print-annex-print-plan-r01.json';guard.safe(plan_path,fresh=True);plan_path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert guard.safe(manifest_path).read_bytes()==manifest_raw and guard.read(actual['xlsx'],actual['xlsxSha256'])==xlsx_raw
print(json.dumps({'verificationPath':str(output),'verificationSha256':digest(output.read_bytes()),'xlsxSha256':actual['xlsxSha256'],
                  'printPlan':str(plan_path),'printPlanSha256':digest(plan_path.read_bytes()),'nonemptyCells':verification['cellsChecked'],'originalWrittenCells':425,'sheets':19,'embeddedImages':verification['embeddedImagesChecked']},ensure_ascii=False))
