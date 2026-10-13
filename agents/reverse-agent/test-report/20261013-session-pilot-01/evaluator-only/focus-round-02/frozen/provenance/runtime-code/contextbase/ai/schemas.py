"""Artifact shapes, independent of application domain and implementation language."""

def obj(properties, required=None):
    return {'type': 'object', 'properties': properties,
            'required': list(properties) if required is None else required,
            'additionalProperties': False}

def arr(item):
    return {'type': 'array', 'items': item}

TEXT = {'type': 'string'}
REFERENCE = obj({'path': TEXT, 'startLine': {'type': 'integer'}, 'endLine': {'type': 'integer'}})
DOCUMENT = obj({'id': TEXT, 'path': TEXT, 'title': TEXT, 'kind': TEXT,
                'sourcePaths': arr(TEXT), 'responsibilities': arr(TEXT)})
PLAN = obj({'systemSummary': TEXT, 'documents': arr(DOCUMENT), 'unresolved': arr(TEXT)})
FACT = obj({'id': TEXT, 'topic': TEXT, 'statement': TEXT,
            'basis': {'type': 'string', 'enum': ['observed-source', 'reference-design']},
            'references': arr(REFERENCE)})
ANALYSIS = obj({'documentId': TEXT, 'sourcePathsRead': arr(TEXT), 'facts': arr(FACT),
                'unresolved': arr(TEXT), 'coverageNotes': arr(TEXT)})
DRAFT = obj({'documentId': TEXT, 'path': TEXT, 'content': TEXT,
             'factCorrections': arr(TEXT), 'unresolved': arr(TEXT)})
FINDING = obj({'severity': {'type': 'string', 'enum': ['critical', 'major', 'minor']},
               'documentLocation': TEXT, 'defect': TEXT, 'repairDirection': TEXT,
               'references': arr(REFERENCE)})
REVIEW = obj({'documentId': TEXT, 'approved': {'type': 'boolean'},
              'findings': arr(FINDING), 'unresolved': arr(TEXT)})
