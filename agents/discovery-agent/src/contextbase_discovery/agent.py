"""Own source acquisition/catalog assignment; no upstream agent dependency."""
from pathlib import PurePosixPath

from contextbase_runtime.agent import AnalysisAgent
from contextbase_runtime import catalog


class DiscoveryAgent(AnalysisAgent):
    name = 'discovery-agent'
    stage = 'discovery'
    catalog_policy = catalog.VERSION
    source_fact_policy = True
    record_kinds = frozenset({'system', 'function', 'entry', 'data', 'common', *catalog.EXTRA_KINDS})
    instruction = '''Acquire an evidence-backed system outline, user-facing function
catalog, technical entries, data targets and common processing from original
source. Use the language adapters' syntax facts and their explicit limitations.
Classify business and system functions by complete user tasks, including supported
standalone login screens and independently purposed menus. Separate their shared
implementation from the user-facing function, not one function per method. Distinguish
physical table definitions, SQL references, entities and DTOs. Check registrations,
configuration and omitted materials for catalog gaps. Report unresolved identities
instead of fabricating links or deep behavior. Return only catalog record kinds.''' + catalog.EXTRACTION_RULES

    def build_context(self, context):
        inventories = {'programs': [], 'dataDefinitions': [], 'resources': [], 'configuration': []}
        for entry in context['inventory']['files']:
            suffix = PurePosixPath(entry['path']).suffix.lower()
            if suffix in {'.cs', '.java', '.py', '.js', '.mjs', '.ts', '.c', '.cpp', '.cbl', '.cob'}:
                kind = 'programs'
            elif suffix in {'.sql', '.ddl'}:
                kind = 'dataDefinitions'
            elif suffix in {'.json', '.xml', '.slnx', '.yml', '.yaml', '.properties', '.config', '.toml'}:
                kind = 'configuration'
            else:
                kind = 'resources'
            inventories[kind].append(entry['path'])
        return {'catalogTargets': ['system outline', 'business and system functions', 'data targets', 'common processing'],
                'classificationPolicy': catalog.VERSION,
                'countingRule': 'Count classified main user functions, business and system, grouped by function area within the original scope. '
                                'Show operations, shared capabilities, entries, supporting materials and pending separately. '
                                'Inspect complete screen responsibilities, including login and menus; shared implementation does not erase an independent function. '
                                'Do not impose one function per screen, Web-only scope or any expected count.',
                'resourcesToAccountFor': inventories,
                'languageAcquisition': {'indexSha256': context['structure']['indexSha256'],
                                       'location': 'structure (one complete source-fact table set)'},
                'omittedMaterials': context['inventory']['omitted'],
                'completion': 'Every assigned scope has source evidence, coverage and explicit unresolved gaps.'}
