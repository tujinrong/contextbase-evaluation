"""Own graph extraction over verified catalogs, independent of their producer."""
from copy import deepcopy

from contextbase_runtime.agent import AnalysisAgent


class RelationshipAgent(AnalysisAgent):
    name = 'relationship-agent'
    stage = 'relationship'
    record_kinds = frozenset({'relation'})
    instruction = '''Build source-evidenced relationships from the revalidated
catalog. Trace entries to definitions, caller/callee direction, inputs/outputs,
data operations and common processing. Read conditions, arguments and configuration
as needed to determine applicability. Name the catalog keys in each relation's
dependsOn, keep unresolved targets explicit, and check reverse uses for omissions.
Do not fabricate absent objects. Return discovery followups for missing catalog
premises. You own relationship obligations only; do not execute another agent.'''

    def build_context(self, context):
        obligations = {item['id']: item for item in context['task']['goalRequirements']}
        required = {dep for key in context['task']['requirements'] for dep in obligations[key]['requires']}
        catalog = {key: deepcopy(record) for key, record in context['currentRecords'].items()
                   if record['ownerRequirement'] in required}
        return {'verifiedCatalog': catalog,
                'catalogByKind': {kind: [key for key, record in catalog.items() if record['kind'] == kind]
                                  for kind in ('system', 'function', 'operation', 'entry', 'data', 'common',
                                               'support', 'material', 'dependency', 'unclassified')},
                'traceTargets': ['entry to definition', 'caller to callee', 'function to data operation',
                                 'function to common processing', 'inputs and outputs'],
                'completion': 'Relationships bind catalog identities, versions, direction and original source evidence.'}

    def validate_extraction(self, answer):
        super().validate_extraction(answer)
        current = self.session.status()['records']
        catalog = {key for key, record in current.items()
                   if self.session.obligations[record['ownerRequirement']]['stage'] == 'discovery'}
        for record in answer.get('records', []):
            if not set(record.get('dependsOn', [])) & catalog:
                raise ValueError('A relationship must depend on a locally revalidated catalog record')
