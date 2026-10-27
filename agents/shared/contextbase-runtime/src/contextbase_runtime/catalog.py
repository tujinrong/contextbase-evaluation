"""Language-neutral catalog classifications and independent acceptance gates."""
from __future__ import annotations

VERSION = 'contextbase-catalog/1'
EXTRACTION_RULES = '''
Catalog classification policy contextbase-catalog/1 is mandatory for this task.
Separate semantic level, function area and entry modality. A main function
(kind=function/category=main) explains actor, the user-facing object, independent
user purpose, trigger and completion outcome in the original requested scope.
It may be a business function or a system function such as login. Use area to
distinguish their responsibility; the compatible businessObject field can name
an authentication session or another system object. Independent does not mean
free of prerequisites. A method, URL, page or menu link alone is not enough.
Do not silently narrow the goal to business-domain functions or Web only.
CLI/API tasks with independent user purposes can be main without a screen.

A dedicated login screen with credential input, submission and authentication
success/failure feedback is an independent system function in its selected scope.
Do not hide it solely in common or entry because it precedes other functions,
has shared implementation, or lacks account registration/administration features.
Retain its authentication service, session handling and shared rules as separate
common records with evidenced consumers when appropriate. Reuse of implementation
does not replace a user-facing function. Logout must be classified from its own
user purpose and interaction context; do not force it to be either a separate
main function or a child of login merely because of the name.

An independently operated complete screen is strong main-function evidence,
not an automatic one-screen-one-function rule. Inspect its purpose, input,
actions, result and caller context. Details, confirmations, dialogs and editing
modes may remain operations of an evidenced parent. Shared UI fragments and
layouts are not independent user screens merely because they have files.

Classify menus from their responsibility. Shared navigation fragments, a common
layout or a generic shared menu screen may be common capabilities or technical
navigation when their evidenced responsibility is the common navigation framework,
rather than a separately owned customer/user task. Being displayed as a whole
screen does not by itself override that responsibility. A customer-specific
complete menu, role-based function selector or workbench can be an independent
system/business function when it owns a distinct user purpose and completion
result. Function selection and navigation may be that purpose; database writes
or complex business processing are not required. A different brand, title or URL
alone is insufficient. Explain dedicated-screen versus shared-navigation evidence;
do not classify every menu alike or invent customer requirements from its name.

Use kind=operation/category=operation for a step, mode or auxiliary action of a
named main parent in that user-task useContext. The same technical entry may serve
independent inquiry and preparation for editing. Share its entry key; explain the
different operation contexts. CRUD and search have no predetermined level: normal
editing steps may be operations, whereas an independently justified approval or
legal disposal workflow may be main. Avoid both over-splitting and over-merging.
For each main and operation explain rationale and a credible alternative partition
or counterexample; do not invent source facts to justify a preferred count.

Use kind=common/category=common for a reusable or centrally owned responsibility,
with actual consumer keys and a responsibility explanation. One consumer can be
sufficient; a common directory or call count is not proof. Documentation belongs
to material, third-party packages to dependency, and deployment/build support to
support unless the original business goal establishes a different semantic role.
Common includes shared business rules and centrally owned responsibilities as
well as technical helpers; do not reduce it to utility code. An independent
user-facing function must also be visible as function, even when it uses common.
Entry modality is not business level. Keep records for such resources rather than
inflating the function or common count. Other kinds use classification=null.

All semantic references use record keys in this same scope. Main/operation
entryRefs point to kind=entry, parent points to a classified main function, and
common consumers point to function/operation/entry/common records. Consumers must
not be self. These identity links are separate from dependsOn version dependencies.
Keep dependsOn empty unless a strictly acyclic evidence dependency is necessary;
never make parent and child depend on each other or mirror inverse consumers there.

Use unclassified/category=pending if semantic classification lacks evidence;
bind actual unknown IDs and explain impact. If it affects the current count or
required coverage, impact=count-or-coverage and the related unknown must block
the assigned obligation. Do not claim complete classification in that case.
An outside-obligation judgment needs scope evidence and independent review.
Count only classified main functions by area in the original scope. Show operations,
common capabilities, entries, supporting resources and pending candidates separately.
There is NO expected function count. Preserve source evidence; keep catalog
statements concise and do not expand the full behavior of every operation.

Before declaring a catalog gap, establish its impact on the assigned scope.
Project/solution files, compile exclusions, project references, registration
points and authored generators are source evidence; inspect their text without
running build tools, imports or generators. A file readable without an adapter
still supplies source evidence; report its unsupported syntax analysis honestly.

Separate a declaration with no observed static consumers, a retired endpoint,
an architectural comment and an active registration. Reverse-check the complete
acquired source and registrations before describing a declaration as unconnected.
No observed consumer does not prove runtime unreachability: dynamic/reflection
uses may remain unknown. Retain such source material as support or another
evidenced category when its identity is known, explaining the observation limit;
do not invent common consumers or a business function merely to classify it.
An unknown about detailed runtime reachability need not block a source catalog
whose objects and classifications are already supported. If it can change the
current objects, business count or required coverage, keep the catalog blocked.

A comment mentioning a separate deployment, hypothetical adapter or unimplemented
alternative is not itself an active entry or an expansion of the requested scope.
Use actual project membership, configuration and registrations to establish its
applicability. Preserve the comment and any genuine uncertainty; judge it
non-blocking only with evidence that it does not change this catalog's conclusions.
If a current production registration requires the missing target, it remains a gap.

Omitted tests, generated outputs, caches and private materials are not automatically
catalog blockers or automatically proven support. Directory names and omitted
entries alone cannot establish roles. Account for them from acquired project
Compile/Content/Import rules, explicit test/build configuration and generation
references. A production include, conditional import or generated source pointing
into an omitted area must remain unresolved when it can affect this catalog.
Do not read excluded content, copy old run results, follow specification references
or execute inputs to close a gap. Requests to deepen confirmed relationships or
runtime behavior belong to the appropriate original downstream obligation;
retain catalog followups only for investigations actually needed by this layer.
'''

VERIFICATION_RULES = '''
Independently apply catalog classification policy contextbase-catalog/1 to the
entire proposed view. Return classificationChecks exactly for host bindings, with
their record version hashes, and scopeChecks exactly for all host-assigned scopes,
including a scope with zero classified records. Do not choose the review set.
For each main check actor/object/purpose/outcome and original scope; for operations
check user-task parentage; for common check shared/central responsibility
and consumers. Challenge both over-splitting and over-merging, the rationale and
alternative partition. Source existence alone cannot establish semantic level.
Review scope coverage from original registrations, reverse uses and excluded or
uninvestigated resources. In scopeChecks also challenge business or system user
functions incorrectly hidden as common/entry/support/material/dependency or
unclassified. Do not infer Web-only
scope, exclude management business because of CLI, or force any expected count.
Pending that affects required coverage or the main-function count prevents adoption,
even if a general catalog check passes. Other pending questions require an evidenced
scope judgment; a recorded unknown is not automatic permission to claim completion.
Use fail or unknown and blocking findings for material partition errors. Do not
rewrite the author's records. Positive judgments require exact original evidence.

Independently inspect complete user screens, entry handlers, templates and caller
contexts. A supported interactive standalone login must have its independent
system-function record, beyond its entry and authentication implementation.
Fail the assigned scope with a blocking finding if such a function is buried
solely as common/entry. Do not require account-management business to recognize
login. Likewise challenge a customer-specific complete menu wrongly collapsed
into generic common navigation, without assuming every menu is independent.
Check shared framework/menu responsibility versus a dedicated screen's user task; function selection
can be a complete purpose without database writes. Challenge the opposite error
too: elevating every detail page, dialog or mode into a main function. Source
evidence and the original user task must explain main/operation/common placement.

Independently verify the applicability and impact of each alleged gap using the
same catalog-scope rules as the author. Inspect project membership, exclusions,
registrations, reverse uses and generation references, not just an omitted path
or absence of a call. Distinguish retired routes and unconnected declarations
from active entries, and separate-deployment comments from selected implementations.
Do not require runtime reachability proofs, excluded test results or another
deployment's implementation solely to approve a static source catalog. Conversely,
do not approve missing production objects or an unresolved current include/import
by calling them support. Preserve material uncertainty and require blocking
findings whenever it can change the assigned catalog's objects, count or coverage.
Non-blocking and resolved are different judgments: a source-backed scope decision
does not prove an external implementation exists or a runtime question was solved.
'''
EXTRA_KINDS = ('operation', 'support', 'material', 'dependency', 'unclassified')
_TYPED = {'function': 'main', 'operation': 'operation', 'common': 'common',
          'unclassified': 'pending'}
_TEXT = {'type': 'string', 'minLength': 1}
_REFS = {'type': 'array', 'items': _TEXT, 'minItems': 1, 'uniqueItems': True}


def _object(properties):
    return {'type': 'object', 'properties': properties, 'required': list(properties),
            'additionalProperties': False}


def _classification(category, fields):
    return _object({'category': {'type': 'string', 'const': category}, 'scope': _TEXT, **fields})


CLASSIFICATION = {'anyOf': [
    {'type': 'null'},
    _classification('main', {**{k: _TEXT for k in (
        'area', 'businessObject', 'purpose', 'trigger', 'outcome', 'rationale', 'alternative')},
        'actors': _REFS, 'entryRefs': _REFS}),
    _classification('operation', {**{k: _TEXT for k in (
        'parent', 'purpose', 'useContext', 'outcome', 'rationale', 'alternative')}, 'entryRefs': _REFS}),
    _classification('common', {**{k: _TEXT for k in (
        'responsibility', 'rationale', 'alternative')}, 'consumers': _REFS}),
    _classification('pending', {
        'tentativeKind': {'enum': ['function', 'operation', 'common', 'entry', 'support',
                                  'material', 'dependency']},
        'impact': {'enum': ['count-or-coverage', 'outside-obligation']},
        'reason': _TEXT, 'unknownIds': _REFS}),
]}


def semantic_references(record):
    classification = record.get('classification')
    if not classification:
        return []
    references = ([classification['parent']] if classification.get('category') == 'operation' else [])
    references += classification.get('entryRefs', []) + classification.get('consumers', [])
    return list(dict.fromkeys(references))


def validate_records(records, obligations, *, strict=False, unknown_ids=None):
    from . import contracts
    for key, record in records.items():
        classification = record.get('classification')
        if 'classification' in record:
            contracts.validate(classification, CLASSIFICATION)
        expected = _TYPED.get(record['kind'])
        if classification is None:
            if strict and expected:
                raise ValueError('Semantic record requires typed classification: ' + key)
            continue
        if classification['category'] != expected:
            raise ValueError('Classification must match record kind: ' + key)
        owner = obligations.get(record['ownerRequirement'])
        if owner is None or classification['scope'] != owner['scope']:
            raise ValueError('Classification scope must match its owner: ' + key)
        for reference in semantic_references(record):
            target = records.get(reference)
            if target is None:
                raise ValueError('Missing semantic reference: ' + reference)
            target_owner = obligations.get(target['ownerRequirement'])
            if target_owner is None or target_owner['scope'] != classification['scope']:
                raise ValueError('Semantic references must remain in the same scope')
        for reference in classification.get('entryRefs', []):
            if records[reference]['kind'] != 'entry':
                raise ValueError('entryRefs must reference entry records')
        if classification['category'] == 'operation':
            parent = records[classification['parent']]
            if parent['kind'] != 'function' or (parent.get('classification') or {}).get('category') != 'main':
                raise ValueError('Operation parent must be a classified main function')
        if classification['category'] == 'common':
            for reference in classification['consumers']:
                if reference == key or records[reference]['kind'] not in {'function', 'operation', 'entry', 'common'}:
                    raise ValueError('Common consumer must be another function, operation, entry or common')
        if classification['category'] == 'pending' and unknown_ids is not None:
            if not set(classification['unknownIds']).issubset(unknown_ids):
                raise ValueError('Pending classification must reference known unknowns')


def bindings(records):
    return [{'key': key, 'sha256': record['version'], 'category': record['classification']['category'],
             'scope': record['classification']['scope']}
            for key, record in records.items()
            if record['kind'] in _TYPED and record.get('classification') is not None]


def scopes(task):
    assigned = set(task['requirements'])
    return list(dict.fromkeys(item['scope'] for item in task['goalRequirements']
                             if item['id'] in assigned and item['stage'] == 'discovery'))


def CHECKS_SCHEMA(task):
    from . import contracts as c
    bound = task.get('classificationBindings', [])
    scope_ids = scopes(task)
    result = {'status': {'enum': ['pass', 'fail', 'unknown']}, 'reason': c.TEXT,
              'evidence': c.arr(c.EVIDENCE)}
    return {'classificationChecks': c._exact_array(c.obj({
                'key': c._enum(item['key'] for item in bound), 'recordSha256': c.SHA256,
                **result}), len(bound)),
            'scopeChecks': c._exact_array(c.obj({'scope': c._enum(scope_ids), **result}), len(scope_ids))}


def validate_checks(answer, task, source, *, defer_evidence=False):
    from . import contracts as c
    fields = CHECKS_SCHEMA(task)
    c.validate({key: answer.get(key) for key in fields}, c.obj(fields))
    checks = answer['classificationChecks']
    scope_checks = answer['scopeChecks']
    expected = {item['key']: item['sha256'] for item in task.get('classificationBindings', [])}
    keys = c._unique_ids(checks, 'key', 'classification check')
    actual_scopes = c._unique_ids(scope_checks, 'scope', 'scope check')
    if set(keys) != set(expected) or set(actual_scopes) != set(scopes(task)):
        raise ValueError('Classification verification must cover exact bound records and scopes')
    for item in checks:
        if item['recordSha256'] != expected[item['key']]:
            raise ValueError('Classification record fingerprint changed')
    for item in checks + scope_checks:
        if item['status'] == 'pass' and not item['evidence']:
            raise ValueError('Positive classification verification requires source evidence')
    if not defer_evidence:
        source.verify_evidence_many([ref for item in checks + scope_checks for ref in item['evidence']])


def require_resolved(view, answer):
    if any(item['status'] != 'pass' for field in ('classificationChecks', 'scopeChecks')
           for item in answer[field]):
        raise ValueError('Classification and scope verification must all pass')
    for record in view['records'].values():
        classification = record.get('classification') or {}
        if classification.get('category') == 'pending' and classification['impact'] == 'count-or-coverage':
            raise ValueError('Pending catalog classification affects count or coverage')
