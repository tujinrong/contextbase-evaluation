"""Persist manually judged source-only data flow, quotes, pins, and bounded scans."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = ROOT / 'agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/snapshot/sources'
CHECKLIST = HERE / 'checklist.v1.json'
PRIOR = HERE / 'document-comparison-03.json'
assert hashlib.sha256(CHECKLIST.read_bytes()).hexdigest() == '40e184c35018ec8efe31915a91c48ab35a4ebb70670e61bc8d35c7d0a4aa4242'
assert hashlib.sha256(PRIOR.read_bytes()).hexdigest() == '3e1b6ee5f8d0a61fec5d5aa055d48bda3e48cf37ea9afc2e993eaa8a23d8716d'
prior = json.loads(PRIOR.read_text(encoding='utf8'))
checklist = json.loads(CHECKLIST.read_text(encoding='utf8'))
files = {p.relative_to(SOURCE).as_posix(): p for p in SOURCE.rglob('*') if p.is_file()}
hashes = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in files.items()}
assert hashes == {entry['path']: entry['sourceSha256'] for entry in prior['rawSourceInventory']}
assert all(hashes[entry['path']] == entry['sourceSha256'] for entry in checklist['sourceFiles'])
cache = {key: path.read_text(encoding='utf8').splitlines() for key, path in files.items()}
evidence_catalogue = {}


def source(label, path, start, end):
    quote = '\n'.join(cache[path][start-1:end])
    assert start >= 1 and start <= end <= len(cache[path])
    evidence_catalogue[label] = {
        'path': 'agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/snapshot/sources/' + path,
        'sha256': hashes[path], 'startLine': start, 'endLine': end, 'quote': quote,
        'normalizedRangeSha256': hashlib.sha256(quote.encode('utf8')).hexdigest(),
    }
    return label


def scan(pattern, suffixes):
    compiled = re.compile(pattern, re.IGNORECASE)
    scoped = [key for key, path in files.items() if path.suffix.lower() in suffixes]
    matches = [{'path': key, 'line': n, 'quote': line}
               for key in sorted(scoped) for n, line in enumerate(cache[key], 1) if compiled.search(line)]
    return {'pattern': pattern, 'scannedFiles': sorted(scoped), 'matches': matches,
            'interpretation': 'Only absence/presence of these textual patterns in the listed sealed source files; no runtime or external framework behavior proof.'}


source('E01', 'Core/Contracts.cs', 9, 30)
source('E02', 'Core/Contracts.cs', 31, 60)
source('E03', 'Web/Inputs/StudentSearchInput.cs', 7, 22)
source('E04', 'Web/Inputs/StudentSaveInput.cs', 9, 42)
source('E05', 'Web/Inputs/StudentSaveInput.cs', 44, 54)
source('E06', 'Core/StudentNormalizer.cs', 119, 147)
source('E07', 'Core/SqlServerStudentService.cs', 77, 90)
source('E08', 'Core/SqlServerStudentService.cs', 173, 194)
source('E09', 'Infrastructure/WebPresentation.cs', 20, 22)
source('E10', 'Web/Models/StudentSearchPageModel.cs', 6, 15)
source('E11', 'Infrastructure/WebStudentCoordinator.cs', 7, 15)
source('E12', 'Infrastructure/WebStudentCoordinator.cs', 17, 21)
source('E13', 'Infrastructure/SearchContextStore.cs', 6, 15)
source('E14', 'Infrastructure/EditorSnapshotStore.cs', 7, 11)
source('E15', 'Infrastructure/FlashMessageStore.cs', 6, 9)
source('E16', 'Views/Students/Search.cshtml', 4, 8)
source('E17', 'Views/Students/Edit.cshtml', 4, 17)
source('E18', 'Web/Controllers/StudentsController.cs', 8, 16)
source('E19', 'Web/Controllers/StudentsController.cs', 23, 40)
source('E20', 'Infrastructure/WebHostSetup.cs', 13, 19)
source('E21', 'Infrastructure/WebHostSetup.cs', 21, 28)
source('E22', 'Infrastructure/RequestIdentity.cs', 7, 16)
source('E23', 'Views/Shared/_Layout.cshtml', 1, 1)
source('E24', 'Views/Shared/_MessagePanel.cshtml', 1, 3)
source('E25', 'Views/_ViewImports.cshtml', 1, 3)
source('E26', 'wwwroot/js/site.js', 2, 9)
source('E27', 'appsettings.json', 1, 1)
source('E28', 'Core/StudentNormalizer.cs', 47, 57)
source('E29', 'Core/SqlServerStudentService.cs', 224, 239)
source('E30', 'Core/SqlServerStudentService.cs', 261, 262)
source('E31', 'Core/SqlServerStudentService.cs', 274, 290)
source('E32', 'Core/SqlServerStudentService.cs', 294, 322)
source('E33', 'Core/SqlServerStudentService.cs', 330, 342)
source('E34', 'Core/SqlServerStudentService.cs', 385, 390)
source('E35', 'Core/SqlServerStudentService.cs', 392, 416)
source('E36', 'Core/MasterMaintenanceService.cs', 132, 135)
source('E37', 'database/001_schema.sql', 7, 42)
source('E38', 'database/001_schema.sql', 137, 154)
source('E39', 'database/001_schema.sql', 156, 184)
source('E40', 'Core/SqlServerStudentService.cs', 30, 42)

raw_scan = scan(r'\bHtml\s*\.\s*Raw\s*\(|\bRaw\s*\(|\b(?:IHtmlContent|HtmlString|WriteLiteral)\b', {'.cs', '.cshtml', '.js'})
log_scan = scan(r'\bILogger\b|\bLog(?:Critical|Error|Warning|Information|Debug|Trace)\s*\(|\bConsole\s*\.', {'.cs', '.cshtml', '.js'})
builder_scan = scan(r'\bAuditBuilder\b', {'.cs'})
cookie_scan = scan(r'Response\s*\.\s*Cookies|Set-Cookie|document\s*\.\s*cookie', {'.cs', '.cshtml', '.js'})
assert not raw_scan['matches'] and not log_scan['matches'] and not builder_scan['matches'] and not cookie_scan['matches']

draft_defs = [
    ('basic05', 'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts/search-basic-05/基本設計書/01_学生検索画面.md', '1f307707bebcb621f7c0e7f895cec8e2a5c386c98c96aa5821c7e9619f0f6778'),
    ('detail04', 'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts/search-detail-04/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md', '658617eb1367817031128eef12fbd51d50b758e04dff14f01997f14eacb1c785'),
]
drafts = {}
for key, path, sha in draft_defs:
    data = (ROOT / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == sha
    drafts[key] = {'path': path, 'sha256': sha, 'lines': data.decode('utf8').splitlines()}


def manuscript(key, start, end):
    draft = drafts[key]
    quote = '\n'.join(draft['lines'][start-1:end])
    assert 1 <= start <= end <= len(draft['lines'])
    return {'path': draft['path'], 'sha256': draft['sha256'], 'startLine': start, 'endLine': end,
            'quote': quote, 'normalizedRangeSha256': hashlib.sha256(quote.encode('utf8')).hexdigest()}


flows = [
    {'id': 'PF01', 'area': 'DTO and persistent business columns',
     'observed': 'Search Name/Kana/PhoneNumber map to SearchCriteria.StudentName/StudentNameKana/PhoneNumber. Save input maps names, birth date, postal/prefecture/address, phone/email, emergency contact and remarks to StudentDraft; normalizer maps those to m_student columns including name_key/kana_key. Parameters carry normalized values to typed SQL fields. Reason and ReturnContextId are separate transport properties, not StudentDraft business fields.',
     'evidence': ['E01', 'E02', 'E03', 'E04', 'E06', 'E32', 'E37', 'E40'],
     'notEstablished': 'No app/database execution, real personal values, database encryption-at-rest or deployed field population was observed.'},
    {'id': 'PF02', 'area': 'search view data versus edit detail',
     'observed': 'Search SELECT/StudentRow includes student ID/no/name/kana/birth, affiliation/status, prefecture-name plus address1, personal phone, dates/version. WebPresentation.Row exposes ID as decimal string plus selected display fields; no address2, email, emergency contact, remarks, AdmissionDate or RowVersion in the search display object. GetAsync builds full StudentDetail/StudentDraft and StudentSaveInput.From supplies edit controls. Page model JsonElement is an internal view handoff, not a public search JSON response from these controller routes.',
     'evidence': ['E02', 'E05', 'E07', 'E08', 'E09', 'E10', 'E16', 'E17', 'E18', 'E19']},
    {'id': 'PF03', 'area': 'browser form and generated URL channels',
     'observed': 'Search personal filters are rendered in a POST form to /students/search; edit/create/update values are POST controls. New/edit links contain returnContextId and optional studentId, return link contains contextId/contextRevision, and post-save 303 Location contains only escaped contextId/contextRevision. These source-generated URLs do not serialize search names/phone or student address fields. Hidden controls carry state ID/revision/tab, snapshot ID, expected version and confirmation/return tokens separately from business data.',
     'evidence': ['E16', 'E17', 'E18', 'E19'],
     'notEstablished': 'The claim is limited to source-generated routes/forms; it does not guarantee what an arbitrary client sends, what middleware/request logging captures, or that identifiers themselves are non-sensitive.'},
    {'id': 'PF04', 'area': 'server-held personal data and references',
     'observed': 'Search success copies criteria to Applied and stores SearchResult in LastResult; page/resume reuse those server-held values. Singleton ConcurrentDictionary Entry contains owner, session, tab, expiry, revision, Applied and LastResult. Token is 32 random bytes rendered as lower hexadecimal, not encoded search values. EditorSnapshotStore contains original full detail/form copies; flash stores fixed save/delete messages keyed by principal/session/context. State reads compare principal/session and optionally nonempty tab.',
     'evidence': ['E11', 'E12', 'E13', 'E14', 'E15', 'E19', 'E22'],
     'notEstablished': 'Dictionary scope/lifetime is observed; durable encrypted state storage, multi-node behavior, browser private-memory guarantees, and physical memory clearing on expiry are not proven.'},
    {'id': 'PF05', 'area': 'search context versus authentication/antiforgery cookie',
     'observed': 'No reviewed application Response.Cookies/Set-Cookie/document.cookie write stores search criteria. Stores use memory dictionaries. Authentication AddCookie and Antiforgery configure Secure/HttpOnly/SameSiteStrict names. The evaluation SignInAsync call passes NameIdentifier, Name, Role and random login_session claims; authentication identity is separate from search student fields. Cookie ticket bytes and framework serialization were not inspected.',
     'evidence': ['E13', 'E14', 'E15', 'E20', 'E21'],
     'notEstablished': 'Do not generalize the source comment about search personal values to no personal identifiers in every authentication cookie or operational header.'},
    {'id': 'PF06', 'area': 'HTTP protections in source',
     'observed': 'Outer middleware sets Cache-Control no-store, X-Content-Type-Options nosniff, Referrer-Policy no-referrer and CSP default/script/style/img self, frame-ancestors none, base-uri self, form-action self before invoking the next delegate. HTTPS redirection is present. Authentication cookie expiry is 30 minutes with sliding expiration; CSRF header/cookie and automatic POST antiforgery filter are configured.',
     'evidence': ['E20', 'E21'],
     'notEstablished': 'Source configuration is not proof of deployed headers, TLS negotiation, cookie contents, browser cache behavior or production authentication setup.'},
    {'id': 'PF07', 'area': 'dynamic view output and Raw boundary',
     'observed': 'Student/control names and messages use normal Razor @ expressions and MVC asp-for/validation Tag Helpers. Search row names/address/phone use @row.GetProperty(...).GetString(), duplicate candidates use @c.StudentName, header uses @User.Identity?.Name and message panel uses @Model. Raw/Html.Raw/IHtmlContent/HtmlString/WriteLiteral patterns have zero matches in the listed reviewed application source files. RenderBody and AntiForgeryToken are view/framework markup calls, not custom Raw calls for these business strings. site.js modifies control values/attributes and removes a dialog; it does not build personal HTML via innerHTML.',
     'evidence': ['E16', 'E17', 'E23', 'E24', 'E25', 'E26'],
     'notEstablished': 'This records syntax and the absence of explicit Raw output. Framework-generated HTML, actual encoded payloads, DOM execution and an end-to-end XSS claim were not tested.'},
    {'id': 'PF08', 'area': 'hand-built error HTML',
     'observed': 'For non-/api failures before response start, outer middleware concatenates a static HTML shell and HtmlEncode(fault.Message or generic guidance). Unknown/system errors in Save/Delete catch return fixed messages and request IDs, not SqlException.ToString() or raw DTO payloads. WebFault field/messages are passed to ModelState, whose summary and message panel are Razor/TagHelper output.',
     'evidence': ['E18', 'E19', 'E21', 'E24', 'E32', 'E35'],
     'notEstablished': 'Model-binding-generated messages, framework/provider logging and already-started exception behavior were not executed.'},
    {'id': 'PF09', 'area': 'ordinary diagnostic logging',
     'observed': 'The listed application source files contain no matching app-specific ILogger/LogCritical/Error/Warning/Information/Debug/Trace or Console call. appsettings selects Warning for Default and Microsoft.AspNetCore. The host catch consumes known/generic messages without an explicit logger call. No actual operational log file was read.',
     'evidence': ['E21', 'E27', 'E32', 'E35'],
     'notEstablished': 'A Warning threshold and absence of explicit application logger calls do not prove no PII in framework, hosting, SQL provider, server, proxy or operational logs.'},
    {'id': 'PF10', 'area': 'actual audit method arguments and saved columns',
     'observed': 'The actual student Audit method receives ID, CREATE/UPDATE/DELETE, before/after version, string[] changed, actor, time, reason, confirmed flag and request GUID. changed is derived by selecting dictionary keys, and JsonSerializer.Serialize(changed) stores a JSON array of column names in changed_columns. No before/after student name/address/phone values are passed to this audit INSERT. target_table=m_student, decimal target_key, actor and free reason are saved in t_operation_log; master Log uses the same column-name representation with operation_reason=NULL. AuditBuilder symbol is absent in these .cs files.',
     'evidence': ['E30', 'E32', 'E34', 'E35', 'E36', 'E38'],
     'notEstablished': 'Audit target identifiers and actor remain identifiers; absence of business field snapshots is not complete audit anonymization.'},
    {'id': 'PF11', 'area': 'reason text and privacy limit',
     'observed': 'Save OperationReason maps to SaveRequest.Reason, Text(rawMax=60,savedMax=60,multiline=true) and NVarChar/120 @reason in t_operation_log.operation_reason. Delete reason uses required Text(60,60), is saved in both m_student.delete_reason and the DELETE audit operation_reason. Text enforces scalar length/control characters, newline conversion and trim; it does not remove names, phone numbers or addresses. User-entered reason may therefore contain personal text; no real reason content was inspected.',
     'evidence': ['E04', 'E17', 'E28', 'E29', 'E34', 'E35', 'E37', 'E38'],
     'notEstablished': 'Do not claim audit or delete reasons are PII-free. No new redaction feature or operational policy is requested by this source-only audit.'},
    {'id': 'PF12', 'area': 'confirmation/hash state versus encrypted-state DDL',
     'observed': 'HashPayload computes SHA256 over normalized selected field key/value pairs; candidate hash uses ID/version pairs. webTokens=true in DI uses memory confirmation records containing owner/id/version/hash bytes/expiry and a random token, while the alternate non-Web branch writes hashes into t_confirmation. t_runtime_state declares encrypted_payload but no current store read/write path is connected to it. SQL client constructor requires Encrypt=Mandatory and TrustServerCertificate=false; this is connection configuration, not observed deployed transport or at-rest encryption.',
     'evidence': ['E20', 'E29', 'E31', 'E33', 'E39', 'E40'],
     'notEstablished': 'Hashing is not encryption or anonymization proof, and the unused encrypted_payload column does not prove active encryption of memory-held search/edit data.'},
]

comparisons = [
    {'id': 'PC01', 'topic': 'DTO/display and in-memory state', 'status': 'INCLUDED_FOR_SEARCH_RESPONSIBILITY',
     'manuscriptEvidence': [manuscript('basic05', 27, 29), manuscript('basic05', 904, 909), manuscript('detail04', 746, 748), manuscript('detail04', 808, 812)],
     'judgment': 'The existing manuscripts correctly separate Razor internal JSON, input versus applied criteria, row display and server memory; full registration field behavior is outside their search responsibility.'},
    {'id': 'PC02', 'topic': 'generated URL versus search-cookie/identity channels', 'status': 'SOURCE_BACKED_SUPPLEMENT_MISSING', 'severity': 'minor',
     'relatedFlows': ['PF03', 'PF04', 'PF05'],
     'manuscriptEvidence': [manuscript('basic05', 937, 937), manuscript('detail04', 808, 812)],
     'judgment': 'Routes, hidden IDs and memory stores are described in individual sections, but the search personal-data channel boundary and distinction from authentication identity claims are not stated explicitly. No contradictory no-PII guarantee was found.'},
    {'id': 'PC03', 'topic': 'HTTP/cookie exact settings', 'status': 'PREVIOUS_MINOR_GAP_PERSISTS', 'severity': 'minor',
     'relatedIssue': 'DC07', 'relatedFlows': ['PF06'],
     'manuscriptEvidence': [manuscript('basic05', 943, 945), manuscript('detail04', 556, 560)],
     'judgment': 'Basic does not describe the HTTP settings; detail names header families but omits the CSP value and secure cookie/expiry settings. Already shared separately; no need to count as a newly discovered gap.'},
    {'id': 'PC04', 'topic': 'Razor Raw and manual error encoding', 'status': 'SOURCE_BACKED_SUPPLEMENT_MISSING', 'severity': 'minor',
     'relatedFlows': ['PF07', 'PF08'],
     'manuscriptEvidence': [manuscript('basic05', 25, 27), manuscript('basic05', 943, 943), manuscript('detail04', 746, 748), manuscript('detail04', 556, 560)],
     'judgment': 'Both identify Razor transfer and outer HTML errors but omit the observed normal output notation/no explicit Raw boundary and the explicit HtmlEncode used by hand-built error HTML.'},
    {'id': 'PC05', 'topic': 'audit names versus free reason / ordinary logs', 'status': 'SOURCE_BACKED_SUPPLEMENT_PARTIAL', 'severity': 'minor',
     'relatedFlows': ['PF09', 'PF10', 'PF11'],
     'manuscriptEvidence': [manuscript('basic05', 702, 702), manuscript('basic05', 807, 807), manuscript('detail04', 832, 836)],
     'judgment': 'Basic already lists column-name JSON, actor and reason. Detail states audit INSERT without its argument/column boundary. Neither states the source-bound limitation that free reason is stored and no explicit app logger is present; neither falsely claims all logs are PII-free.'},
    {'id': 'PC06', 'topic': 'unused encrypted-state DDL / SQL transport', 'status': 'INCLUDED_WITH_LIMITS',
     'relatedFlows': ['PF12'], 'manuscriptEvidence': [manuscript('basic05', 907, 909), manuscript('basic05', 941, 941), manuscript('detail04', 808, 812)],
     'judgment': 'Existing manuscripts preserve the unused encrypted_payload boundary and do not infer active encryption/persistence from the column name.'},
]

output = {
    'schema': 'reverse-source-personal-data-flow-audit/1', 'projectId': 'test-project1', 'technology': 'CSharp_ASPNET',
    'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
    'role': 'SOURCE_ONLY_INDEPENDENT_PERSONAL_DATA_FLOW_AND_MANUSCRIPT_SUPPLEMENT_REVIEW',
    'checklist': {'path': CHECKLIST.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(CHECKLIST.read_bytes()).hexdigest(), 'unchanged': True},
    'priorAudit': {'path': PRIOR.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(PRIOR.read_bytes()).hexdigest()},
    'inputs': [{'id': key, 'path': drafts[key]['path'], 'sha256': drafts[key]['sha256'], 'lineCount': len(drafts[key]['lines'])} for key, _, _ in draft_defs],
    'boundaries': {'originalSpecRead': False, 'specEvalRead': False, 'trainingAssistedRead': False,
                   'scoringCreated': False, 'newDraft06Or05Read': False, 'canonicalOrSourceEdited': False,
                   'applicationDbSqlDeploymentExecuted': False, 'browserOrFrameworkOutputExecuted': False,
                   'operationalLogsRead': False, 'programExecutionMeaning': 'Only audit serialization and bounded source-text/hash scans ran; original program/source/SQL did not execute.'},
    'method': 'AI traces code arguments/properties/SQL columns and Razor syntax. Python records the manually judged flow, exact file/range SHA/quotes, pins and bounded absence searches; it does not author or modify specification prose.',
    'sourceIntegrity': {'rawFiles': len(files), 'matchesPreviousSourceOnlyAuditInventory': True,
                        'matchesFixedChecklistSourceFiles': len(checklist['sourceFiles']),
                        'wholeManifestSealVerificationRepeated': False,
                        'sourceFileHashes': hashes},
    'flows': flows, 'sourceEvidenceCatalogue': evidence_catalogue,
    'boundedAbsenceSearches': {'explicitRawOutput': raw_scan, 'explicitAppDiagnosticCalls': log_scan,
                              'AuditBuilderSymbol': builder_scan, 'explicitApplicationCookieWrites': cookie_scan},
    'manuscriptComparisons': comparisons,
    'summary': {'newImportantContradictionsFound': 0, 'newImportantBusinessDefectsFound': 0,
                'sourceBackedSupplementGaps': ['PC02', 'PC04', 'PC05'], 'existingGap': 'DC07/PC03',
                'privacySafetyOrOperationalGuarantee': 'NOT_ESTABLISHED'},
    'communications': {'sourcePilotDirectMessages': 'Exact source line/quote boundaries and manuscript omissions shared; active frozen jobs were not changed.',
                       'parentUpdate': 'Findings and limitations shared before serialization.'},
    'unknowns': ['Real request/response/cookie contents', 'Framework/provider/host/proxy/server operational logs',
                 'Deployed response headers and TLS', 'Actual database records and reason content',
                 'Authentication in production', 'Database at-rest encryption, retention and physical memory clearing',
                 'Full browser encoding behavior and end-to-end XSS/confidentiality outcome'],
}
for key, path, sha in draft_defs:
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha
assert hashes == {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in files.items()}
target = HERE / 'personal-data-flow-audit-01.json'
assert not target.exists()
target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')
summary = HERE / 'personal-data-flow-audit-01.summary.md'
assert not summary.exists()
summary.write_text('''# 個人データ source-only 追加監査

対象は封印snapshotの41 raw sourceと、SHA固定済み検索基本05・詳細04。固定checklist.v1と25 sourceのSHA、前回独立監査の41 source SHAを再照合した。原仕様・評価期待値・採点・training-assisted・新基本06/詳細05は未読。原稿と原ソースは変更していない。

検索氏名・カナ・電話はPOSTフォーム/DTOから検索用引数へ渡り、成功後はAppliedの入力コピーとLastResultをサーバー辞書に保持する。一覧は氏名・カナ・和暦生年月日・所属・都道府県名＋住所1・本人電話を含む。住所2、メール、緊急連絡先、備考を検索表示へ出さず、登録読込では明細から編集inputへ渡す。生成された往復URLには状態ID/版や学生IDを載せ、氏名・電話・住所をシリアライズしない。状態IDは乱数32バイトの16進値である。検索専用cookie書込みは見つからず、認証cookieへのSignInAsyncは別の利用者claimsを受けるため、全cookieの個人識別情報がないとは保証しない。

原ビューの動的値は通常のRazor @式とasp-for/validation Tag Helper記法。明示Raw/Html.Raw/IHtmlContent/HtmlString/WriteLiteralは対象application source内で0件。手組の外側エラーHTMLはHtmlEncodeを使用する。実HTML・DOM・framework出力は未実行。

HTTP原設定はno-store/nosniff/no-referrerとselfを中心とするCSP、frame-ancestors none、HTTPS redirect、Secure/HttpOnly/SameSiteStrict cookie、認証30分・sliding expiration。実配備の挙動は未確認。

通常障害のapp固有ILogger/Log*/Console呼出しは未観測で、appsettingsはDefault/ASP.NET Warning。これは運用ログのPII不在を保証しない。実監査はAuditメソッドで、変更列名JSON、対象ID、前後版、実施者、時刻、相関ID、理由、重複確認値を保存する。氏名/住所/電話のbefore/after値を監査引数へ渡さない。一方、自由入力の理由は長さ・制御文字・改行・trimの検査後にoperation_reasonへ本文保存され、削除理由は学生表delete_reasonにも保存される。伏字処理はなく、理由内容次第で個人情報を含み得る。AuditBuilderという型名は見つからない。

既存2稿に新たな重要矛盾・重要業務誤りは発見しなかった。DTO・表示・メモリ・暗号化DDLの未接続境界は説明されている。検索データ/URL/cookieの区分、Razor/手組HTMLの出力境界、監査引数と自由理由・通常ログの限界は補足が不足する。詳細の監査はINSERT記述のみで、基本は変更列JSON・理由等を既に記述する。HTTP不足は既存DC07の継続として扱い、新規重複計数しない。source-pilotへ根拠行・実quote付きで共有済み。

本監査はコードの観測であり、アプリ・DB・SQL・ブラウザ・運用ログ・配備を検証していない。仕様書得点、個人情報保護の合格、視覚合格は作成していない。40 source引用範囲、12 flow、6稿比較、負の文字列検索、各SHAをJSONへ保存した。
''', encoding='utf8', newline='\n')
print(json.dumps({'report': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                  'summary': str(summary), 'summarySha256': hashlib.sha256(summary.read_bytes()).hexdigest(),
                  'sourceFiles': len(files), 'evidenceRanges': len(evidence_catalogue), 'flows': len(flows),
                  'comparisons': len(comparisons), 'absenceScanApplicationFiles': len(raw_scan['scannedFiles'])}, ensure_ascii=False))
