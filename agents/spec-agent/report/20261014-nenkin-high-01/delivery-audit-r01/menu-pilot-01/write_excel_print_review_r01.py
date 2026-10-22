"""Record actual actor views and immutable delivery evidence; no authoring."""
import datetime
import hashlib
import json
import stat
from pathlib import Path

WORK = Path('D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path('D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
Q = REPORT / 'delivery-audit-r01/menu-pilot-01'
E = Q / 'excel-static-readonly-r01'
P = WORK / 'delivery/menu-pilot-01'

def safe(path):
    path = Path(path).absolute()
    if not any(path.is_relative_to(root) for root in (WORK, REPORT)):
        raise ValueError('evidence path outside this run')
    for node in (path, *path.parents):
        if node.exists():
            st = node.lstat()
            if stat.S_ISLNK(st.st_mode) or getattr(st, 'st_file_attributes', 0) & 0x400:
                raise ValueError('linked/reparse evidence path')
    return path

def sha(path):
    return hashlib.sha256(safe(path).read_bytes()).hexdigest()

def load(path):
    return json.loads(safe(path).read_text(encoding='utf-8'))

def exact(path, expected):
    if sha(path) != expected:
        raise ValueError('evidence SHA drift: ' + str(path))

before = load(Q / 'qa-inputs-before-r01.json')
for name in ('model', 'binding', 'author', 'originalXlsx'):
    exact(before[name]['path'], before[name]['sha256'])
for image in before['previews']:
    exact(image['path'], image['sha256'])
inventory = load(E / 'native-print-inventory-r01.json')
exact(E / 'native-print-inventory-r01.json', 'd7bd41c1092c25f066c9390bdda2730498d12895406811b404c4d3afdaa616fb')
for image in inventory['images']:
    exact(image['path'], image['sha256'])
    exact(image['pdf'], image['pdfSha256'])
exact(E / 'result.json', '59e1ce36d7027138adc2c530b9300d84634c19982bb9650ac063d7f1439745b6')
exact(P / 'xlsx-print-r01/Excel/basic/menu.xlsx', 'a8681156199ea84c66ebcb6b0527c0c4d5b6d5094832d048b36ef4a75f710fbb')
root_path = E / 'root-native-print-pages12-22-review-r01.json'
exact(root_path, '7467d95540c501b419f755aefe7a60287be1f8cb5ce7cbdb957cc33d215e95cd')
root = load(root_path)
result = load(E / 'result.json')
x18 = [x for x in result['cells'] if x['sheet'] == '表紙' and x['cell'] == 'X18']
if len(x18) != 1 or (x18[0]['value2'], x18[0]['text'], x18[0]['numberFormat']) != ('1.0', '1.0', '@'):
    raise ValueError('actual Excel version evidence mismatch')
viewed = [{**x, 'actorViewed': True, 'actor': '/root/delivery_tools', 'inventoryOrdinal': i + 1,
           'viewMethod': 'view_image original detail'} for i, x in enumerate(inventory['images'][:11])]
report = {
    'schema': 'readonly-excel-static-print-native-review/1',
    'createdUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'SECONDARY_STATIC_EXCEL_PRINT_QA_GEOMETRY_ONLY',
    'actor': '/root/delivery_tools',
    'status': 'HOLD_PRINT_PAGINATION',
    'actualAll11AssignedImagesViewed': True,
    'assignedInventoryOrdinals': list(range(1, 12)),
    'images': viewed,
    'inputPinsAndAll22Png5PdfHashesRecheckedAfterViews': True,
    'inventory': {'path': str(E / 'native-print-inventory-r01.json'), 'sha256': sha(E / 'native-print-inventory-r01.json')},
    'staticExcelResult': {'path': str(E / 'result.json'), 'sha256': sha(E / 'result.json')},
    'immutableWorkbook': {'path': str(P / 'xlsx-print-r01/Excel/basic/menu.xlsx'), 'sha256': sha(P / 'xlsx-print-r01/Excel/basic/menu.xlsx')},
    'originalArtifactReview': {'path': str(Q / 'artifact-original17-native-review-r01.json'), 'sha256': sha(Q / 'artifact-original17-native-review-r01.json'),
                               'statusRetained': 'HOLD_ARTIFACT_LITERAL_DISPLAY_AND_ASCII_WRAP', 'actualOriginalPreviewsViewed': 17},
    'actualExcelVersionDisplay': {**x18[0], 'sourceAndOOXMLLiteralExact': True,
                                 'artifactPreviewDisplays': '1', 'previewDiscrepancyDoesNotChangeSource': True},
    'resolvedInspection': [{'id': 'LIST-HEADER-PAGE2', 'initialObservation': 'header appeared faint at full page',
                            'inspectionPath': str(E / 'item-list-page2-header-inspection-r01.png'),
                            'inspectionSha256': sha(E / 'item-list-page2-header-inspection-r01.png'),
                            'source': str(E / 'page-pngs/sheet-003-2.png'), 'crop': [0, 0, 1287, 190],
                            'method': 'lossless source-pixel crop, actually viewed original detail',
                            'result': 'all ten header strings are readable; no header omission or clipping observed'}],
    'findings': [{'id': 'PRINT-DIAGRAM-SPLIT-FIRST-HALF', 'severity': 'major',
                  'pages': ['sheet-004-01.png', 'sheet-004-02.png', 'sheet-004-03.png', 'sheet-004-04.png', 'sheet-004-05.png'],
                  'observation': 'Long diagrams cross A4 landscape page boundaries. Node rectangles, decision diamonds, connecting lines and some vertical label regions are cut at page edges. Adjacent page union retains pixels but a single printed page does not retain the complete flow figure.',
                  'payloadLossObserved': False, 'originalEmbeddedImagesChanged': False}],
    'nonBlockingNotes': ['All declared columns and ordinary text inspected on assigned pages were readable.',
                         'Actual Excel prints Bean and LogoutAction as whole tokens where Artifact preview fragmented them.',
                         'Repeated section title is not visibly present on some pages containing continued drawing regions; titleRows metadata alone is insufficient to qualify visible printing.'],
    'otherActorReview': {'path': str(root_path), 'sha256': sha(root_path), 'actor': '/root', 'assignedInventoryOrdinals': list(range(12, 23)),
                         'actualAll11AssignedImagesViewed': root['actualAll11AssignedImagesViewed'], 'nativeQualification': root['nativeQualification']},
    'unionActualViews': {'count': 22, 'actors': ['/root/delivery_tools', '/root'], 'allInventoryOrdinalsCoveredExactlyOnce': True,
                        'claim': 'Separate actors actually viewed their assigned originals; this actor did not view the latter eleven.'},
    'readOnlyExcel': True, 'macroDisabled': True, 'updateLinks': 0, 'saved': False, 'clipboardUsed': False,
    'ownedExcelQuitReported': True, 'ownedExcel307716AbsentAtPostCheck': True,
    'primarySpecificationPdfQualification': False, 'applicationBehaviorExecuted': False,
    'businessSourceOrReferenceRead': False, 'semanticOrFormalAssessment': False, 'formalPercentage': None,
    'wholeDocumentApproval': False, 'publicationApproved': False, 'markerRepeated': False, 'originalArtifactAuthoringRepeated': False
}
output = safe(E / 'delivery-native-print-pages01-11-review-r01.json')
if output.exists():
    raise ValueError('fresh review path already exists')
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'path': str(output), 'sha256': sha(output), 'status': report['status'], 'actualViews': 11}, ensure_ascii=False))
