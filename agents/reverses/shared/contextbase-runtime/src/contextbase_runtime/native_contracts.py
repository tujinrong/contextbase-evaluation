"""Immutable native tool contracts, authorization and argument diagnostics."""
from __future__ import annotations

from copy import deepcopy
import json

from jsonschema import Draft202012Validator

from . import catalog, candidate_amendment as amendment, contracts as c, investigation
from .native_draft_patch import FIELDS as PATCH_FIELDS
from .evidence import REQUEST_SCHEMA

MAX_STATE_CHARACTERS = 32768


class ToolContracts:
    """Freeze one task's advertised tools and validate against the same contracts."""

    def __init__(self, task, retained_amendment=None):
        task = deepcopy(task)
        self._task = task
        retained_amendment = deepcopy(retained_amendment)
        definitions = _common_tools(retained_amendment)
        if retained_amendment:
            definitions += _amendment_tools(task, retained_amendment)
        elif task['operation'] == 'extract':
            definitions += _author_tools(task)
        else:
            definitions.append({
                'name': 'review_submit',
                'description': 'Submit complete independent review; cannot modify the candidate.',
                'inputSchema': c.obj({'review': c.result_schema(task)}),
            })
        self._definitions = deepcopy(definitions)
        self._validators = {
            definition['name']: Draft202012Validator(definition['inputSchema'])
            for definition in self._definitions
        }
        self._contracts = {
            'record': deepcopy(c.RECORD),
            'classification': deepcopy(catalog.CLASSIFICATION),
            'result': deepcopy(c.result_schema(task)),
        }
        _describe_followups(self._contracts['result'])

    def schemas(self):
        return deepcopy(self._definitions)

    def validate(self, name, arguments):
        validator = self._validators.get(name)
        if validator is None:
            raise ValueError('Tool is not authorized for this role')
        if name == 'draft_apply' and isinstance(arguments, dict) and isinstance(arguments.get('draft'), dict):
            investigation.validate_unknown_definitions(self._task, arguments['draft'].get('unknowns'))
        _raise_argument_errors(list(validator.iter_errors(arguments)))

    def describe(self, contract, category):
        if contract == 'classification':
            schema = self._contracts['classification']
            if category is not None:
                variants = [variant for variant in schema['anyOf']
                    if isinstance(variant, dict) and variant.get('properties', {}).get('category', {}).get('const') == category]
                if len(variants) != 1:
                    raise ValueError('Unknown classification category')
                schema = variants[0]
        elif contract == 'record':
            schema = self._contracts['record']
        else:
            schema = self._contracts['result']
        return {'schema': deepcopy(schema),
                'meaning': 'Contract shape only; supply your own source-supported conclusions.'}


def _common_tools(retained_amendment):
    result = []
    for schema in REQUEST_SCHEMA['anyOf']:
        schema = deepcopy(schema)
        name = schema['properties'].pop('operation')['const']
        schema['required'].remove('operation')
        description = 'Retrieve sealed source evidence: ' + name
        if name in {'inventory', 'query', 'search'}:
            description += '. offset and limit count ITEMS, not characters or bytes; limit is at most 100.'
        result.append({'name': name, 'description': description,
                       'inputSchema': schema})
    result.append({'name': 'evidence_batch',
        'description': 'Retrieve up to 8 independent read/query/search requests in one call. Prefer this when the needed paths or filters are already known. Replies are complete, bounded by serialized UTF-8 bytes, and in request order. Follow next_request_index by resubmitting only the remaining suffix. Query pointers do not deliver original source text.',
        'inputSchema': c.obj({'requests': {**c.arr({'anyOf': [deepcopy(schema)
            for schema in REQUEST_SCHEMA['anyOf']
            if schema['properties']['operation']['const'] in {'read', 'query', 'search'}]}, 1), 'maxItems': 8}})})
    result.append({'name': 'contract_schema', 'description': 'Inspect exact record/classification/review schema. Use a category such as common to retrieve only that classification variant. Consult this instead of guessing fields after validation errors.',
        'inputSchema': c.obj({'contract': {'enum': ['record', 'classification', 'result']},
                             'category': {'type': ['string', 'null']}})})
    result.append({'name': 'analysis_state', 'description': 'Read task, source scope, drafts and frozen review material as a JSON text page. offset and limit are CHARACTERS. Request limit=32768; the server may return fewer characters to fit its serialized UTF-8 byte budget. Always continue at next_offset, never offset+limit.',
        'inputSchema': c.obj({'collection': {'enum': ['task', 'context', 'drafts', 'draft_versions', 'summary', 'fact_usage_diagnostics', 'plan', 'submission'] + (['amendment'] if retained_amendment else [])},
                             'offset': {'type': 'integer', 'minimum': 0, 'description': 'Character offset, initially 0.'},
                             'limit': {'type': 'integer', 'minimum': 1, 'maximum': MAX_STATE_CHARACTERS, 'description': 'Maximum character count; use 32768 and follow the actual next_offset.'},
                             'field': {'type': 'string', 'minLength': 1, 'description': 'Optional single top-level dictionary field; retrieve only missing material named in bootstrap directory.'}}, required=['collection', 'offset', 'limit'])})
    return result


def _amendment_tools(task, retained_amendment):
    seed, spec = retained_amendment['seed'], retained_amendment['spec']
    closure = investigation.closure_schema(task, task['requirements'][0])
    closure['properties']['requirement'] = {'type': 'string', 'enum': task['requirements']}
    return [{'name': 'submit_amendment',
        'description': 'Submit only permitted record replacements and each selected issue disposition, plus fresh closures for all original obligations. Read analysis_state(amendment) for exact frozen expectedVersion values. Omitted base records, unknowns and followups are preserved by the host as untrusted input. Changed claims, dispositions and closures require current evidence; the entire new candidate receives fresh independent verification.',
        'inputSchema': c.obj({'patch': amendment.response_schema(seed, task, spec),
            'closures': c.arr(closure), 'retain_blocking_followups': {'type': 'boolean'}},
            required=['patch', 'closures'])}]


def _author_tools(task):
    mutation = {'operation_id': c.TEXT, 'expected_revision': {'type': 'integer', 'minimum': 0}}
    diagnostics = {'type': 'boolean', 'description': 'Use true to return bounded nonblocking fact-usage diagnostics for records affected by this mutation. No fact IDs or source content are delivered. Full current diagnostics: analysis_state(collection=fact_usage_diagnostics).'}
    sample = {'id': 'unit', 'requirement': task['requirements'][0],
              'question': 'Investigate the assigned source', 'paths': []}
    draft_schema = investigation.draft_schema(task, sample)
    _describe_followups(draft_schema)
    draft_schema['properties']['unitId'] = c.TEXT
    draft_schema['properties']['complete']['description'] = (
        'True when investigation of this unit has ended under current authorized inputs; '
        'unresolved unknowns may remain. This is not acceptance or a claim of certainty.')
    draft_schema['properties']['remainingQuestions']['description'] = (
        'Only concrete next investigation actions executable with the current source tools. '
        'Move unavailable runtime or external-input questions into unknowns; '
        'an ended unit has an empty remainingQuestions array.')
    draft_schema['properties']['records']['items']['properties']['ownerRequirement'] = {
        'type': 'string', 'enum': task['requirements']}
    closure_schema = investigation.closure_schema(task, task['requirements'][0])
    closure_schema['properties']['requirement'] = {'type': 'string', 'enum': task['requirements']}
    record_properties = draft_schema['properties']['records']['items']['properties']
    patch_fields = c.obj({name: deepcopy(record_properties[name]) for name in PATCH_FIELDS
                         if name in record_properties}, required=[])
    patch_fields['minProperties'] = 1
    definitions = [
        {'name': 'plan_update', 'description': 'Save or extend your investigation plan; choose execution order yourself.',
         'inputSchema': c.obj({**mutation, 'plan': investigation.plan_schema(task)})},
        {'name': 'draft_apply', 'description': 'Persist a typed draft with exact record versions. Required record fields include key, ownerRequirement, kind, name, statement, basis, evidence and dependsOn. Before replacing or removing a record, retrieve analysis_state(collection=draft_versions, offset=0, limit=12000) and follow next_offset if present; copy its exact normalized {key,sha256} into expectedVersions or removals, and use the reply revision as expected_revision. Never compute or guess these hashes. Use classification=null on noncatalog kinds; inspect contract_schema for exact classified variants. Inspect plan for unit definitions.',
         'inputSchema': c.obj({**mutation, 'unit_id': c.TEXT, 'draft': draft_schema,
             'include_diagnostics': diagnostics,
             'retain_blocking_followups': {'type': 'boolean', 'description': 'Default false. Set true only to intentionally preserve NEW followups assigned to the current task, acknowledging that they prevent adoption. This never resolves or waives them. For current investigation use plans/remainingQuestions; preserve source uncertainty as unknowns. Classify genuinely unassigned future work explicitly rather than assigning its related topic as a completion target.'}},
             required=['operation_id', 'expected_revision', 'unit_id', 'draft'])},
        {'name': 'draft_patch', 'description': 'Update existing records or replace their factUsage without resending unchanged record bodies or copying hashes. Supply the current expected_revision; the host checks it before deriving exact record versions. updates replaces only the named whole fields. factUsage replaces only the named record associations, which you must support from delivered facts/source. Keys must belong to this unit. This preserves its completion state, remaining questions, unknowns and followups. Inspect analysis_state(summary) for host counts and stable unknown identities.',
         'inputSchema': c.obj({**mutation, 'unit_id': c.TEXT,
             'include_diagnostics': diagnostics,
             'updates': c.arr(c.obj({'key': c.TEXT, 'fields': patch_fields})),
             'factUsage': deepcopy(draft_schema['properties']['factUsage'])},
             required=['operation_id', 'expected_revision', 'unit_id'])},
        {'name': 'submit_candidate', 'description': 'Freeze ended draft units and coverage declarations for independent verification. Blocking unknowns may remain; submission is not acceptance.',
         'inputSchema': c.obj({**mutation, 'closures': c.arr(closure_schema)})}]
    if investigation.explicit_unknown_definitions(task):
        definitions[1]['description'] += (
            ' unknowns creates local definitions only. Existing questions remain saved; '
            'close with unknowns=[] when there are no new questions. Reference a saved '
            'referenceId in classification.unknownIds without redeclaring its definition.')
    return definitions


def _describe_followups(schema):
    followups = schema.get('properties', {}).get('followups')
    if not followups:
        return
    followups['description'] = ('Additional investigation requests, not topic labels. Current assigned unfinished work '
        'belongs in plan units/remainingQuestions, and uncertainty in unknowns. A non-null requirement names a '
        'completion obligation and prevents adoption while retained; null means genuinely unassigned future work. '
        'Do not reclassify a required source investigation merely to obtain acceptance.')
    item = followups['items']
    for variant in item.get('anyOf', [item]):
        variant['properties']['requirement']['description'] = (
            'Completion target, not merely the related area. Assigning a current requirement retains an '
            'unfinished obligation. Use null only for genuinely unassigned future work, preserving source '
            'uncertainties and any actual blocking requirements in unknowns.')


def _raise_argument_errors(errors):
    if not errors:
        return
    rows = []
    def append(error):
        pointer = '/' + '/'.join(str(part).replace('~', '~0').replace('/', '~1')
                                  for part in error.absolute_path)
        message = error.message if error.validator != 'anyOf' else 'Value does not match the required variant'
        rows.append({'path': pointer[:180], 'rule': str(error.validator), 'message': message[:260]})
    for error in errors:
        if error.validator == 'anyOf' and isinstance(error.instance, dict):
            category = error.instance.get('category')
            variants = error.schema.get('anyOf', [])
            selected = [i for i, variant in enumerate(variants)
                        if isinstance(variant, dict) and variant.get('properties', {}).get('category', {}).get('const') == category]
            if selected:
                children = [child for child in error.context
                            if child.schema_path and child.schema_path[0] in selected]
                for child in children:
                    append(child)
                if not children:
                    append(error)
            else:
                append(error)
        else:
            append(error)
        if len(rows) >= 20:
            break
    raise ValueError('Invalid native tool arguments: ' + json.dumps(
        {'errors': rows[:20], 'truncated': len(rows) > 20 or len(errors) > 20}, ensure_ascii=False))
