"""Helper bytes are bound by the semantic capability, independently of Python engine custody."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from contextbase_runtime import controller
from contextbase_runtime.facts import FactIndex
from contextbase_runtime.semantic_calls import SemanticCallIndex
from contextbase_runtime.sources import SourceAccess
from contextbase_runtime.storage import ArtifactStore


class SemanticHelperInvalidationTests(unittest.TestCase):
    def test_changed_helper_invalidates_existing_queries_without_changing_generic_engine(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='semantic-helper-version-', dir=home) as directory:
            root = Path(directory)
            original = root / 'input'
            original.mkdir()
            (original / 'A.cs').write_text('class A { void Go() { Target(); } void Target() {} }', encoding='utf-8')
            (original / 'A.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
                '<TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>', encoding='utf-8')
            source = SourceAccess.create(original, root / 'snapshot', project_id='helper-version',
                                         allowed_paths=['.'], excluded_paths=[])
            store = ArtifactStore(root / 'cache')
            facts = FactIndex.open(source, store)
            index = SemanticCallIndex.open(facts, store, project='A.csproj')
            (root / 'semantic.json').write_text(json.dumps(index.document), encoding='utf-8')
            package = root / 'changed-runtime/contextbase_runtime'
            shutil.copytree(Path(controller.__file__).parent, package,
                            ignore=shutil.ignore_patterns('__pycache__'))
            helper = package / 'dotnet/SemanticCalls.cs'
            helper.write_text(helper.read_text('utf-8') + '\n// Changed trusted helper version.\n', encoding='utf-8')
            script = '''
import json,sys
from pathlib import Path
from contextbase_runtime.controller import engine_fingerprint
from contextbase_runtime.sources import SourceAccess
from contextbase_runtime.storage import ArtifactStore
from contextbase_runtime.facts import FactIndex
from contextbase_runtime.semantic_calls import SemanticCallIndex
from contextbase_runtime.evidence import EvidenceAccess
root=Path(sys.argv[1])
assert engine_fingerprint()==sys.argv[2], 'Generic engine must not depend on an optional helper resource'
source=SourceAccess.open(root/'snapshot'); facts=FactIndex.open(source,ArtifactStore(root/'cache'))
semantic=SemanticCallIndex(json.loads((root/'semantic.json').read_text('utf-8')),facts)
facts.semantic_index=semantic
task={'id':'reader','contextId':'fresh','snapshotId':source.snapshot_id,
      'semanticPolicy':'contextbase-semantic-evidence/1','semanticIndexSha256':semantic.sha256}
try:
    EvidenceAccess(source,facts,task)
except ValueError as error:
    assert 'binding changed' in str(error), str(error)
else:
    raise AssertionError('Changed helper was silently accepted for old semantic delivery')
'''
            env = {**os.environ, 'PYTHONPATH': str(package.parent), 'PYTHONDONTWRITEBYTECODE': '1'}
            result = subprocess.run([sys.executable, '-c', script, str(root), controller.engine_fingerprint()],
                                    capture_output=True, text=True, encoding='utf-8', env=env, timeout=60)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
