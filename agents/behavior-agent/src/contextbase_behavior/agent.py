"""Own behavior tracing over verified relationships and their source evidence."""
from copy import deepcopy

from contextbase_runtime.agent import AnalysisAgent


class BehaviorAgent(AnalysisAgent):
    name = 'behavior-agent'
    stage = 'behavior'
    record_kinds = frozenset({'fact'})
    instruction = '''Deepen behavior along revalidated relationships, reading
original source. Trace values/defaults, conditions and branches, state/order,
exceptions, transaction boundaries, data changes and caller differences. Each fact
must name a verified relationship in dependsOn and provide exact source evidence.
Distinguish static inference from runtime observation. Return relationship or
discovery followups for missing premises. Do not invent a complete behavior path
from unresolved links or run another agent. Produce facts, not specification prose.'''

    def build_context(self, context):
        obligations = {item['id']: item for item in context['task']['goalRequirements']}
        required = {dep for key in context['task']['requirements'] for dep in obligations[key]['requires']}
        graph = {key: deepcopy(record) for key, record in context['currentRecords'].items()
                 if record['ownerRequirement'] in required}
        dependencies = {dep['key'] for record in graph.values() for dep in record['dependencies']}
        return {'verifiedRelationships': graph,
                'supportingCatalog': {key: deepcopy(record) for key, record in context['currentRecords'].items()
                                      if key in dependencies},
                'behaviorQuestions': ['values and defaults', 'conditions and branches', 'state and order',
                                     'errors and transactions', 'data changes', 'caller differences'],
                'completion': 'Each behavior fact binds a verified relationship and exact original source evidence.'}

    def validate_extraction(self, answer):
        super().validate_extraction(answer)
        relations = {key for key, record in self.session.status()['records'].items()
                     if record['kind'] == 'relation'}
        for record in answer.get('records', []):
            if not set(record.get('dependsOn', [])) & relations:
                raise ValueError('A behavior fact must depend on a locally revalidated relationship record')
