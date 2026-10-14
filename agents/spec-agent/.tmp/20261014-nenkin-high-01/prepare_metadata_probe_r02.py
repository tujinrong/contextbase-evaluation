from pathlib import Path
import ast, hashlib
ROOT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01/independent-audit')
old = ROOT / 'probe_writer_metadata_r05.py'
source = old.read_text(encoding='utf-8')
source = source.replace("sys.dont_write_bytecode = True", "sys.dont_write_bytecode = True\nsys.path.insert(0, r'D:/開発/contextbase-evaluation/agents/reverse-agent/.tmp/20261013-rerun-12h/engine-runtime-deps')\nfrom jsonschema import Draft202012Validator\nimport jsonschema\nassert Path(jsonschema.__file__).resolve().is_relative_to(Path(sys.path[0]).resolve())", 1)
source = source.replace("writer-metadata-r05-toy'", "writer-metadata-r05-toy-r02'", 1)
source = source.replace("writer-metadata-r05-bounded-probes-r01.json'", "writer-metadata-r05-bounded-probes-r02.json'", 1)
source = source.replace("    except Exception as exc:\n        result = 'REJECTED'", "    except (ModuleNotFoundError, ImportError):\n        raise\n    except Exception as exc:\n        result = 'REJECTED'", 1)
source = source.replace("'frozenCoreOrLoadedPromptModified':False,'providerStarts':0,", "'frozenCoreOrLoadedPromptModified':False,'providerStarts':0,\n    'jsonschemaImportedFrom':str(Path(jsonschema.__file__).resolve()),\n    'jsonschemaImportSha256':hashlib.sha256(Path(jsonschema.__file__).read_bytes()).hexdigest(),\n    'priorProbeInvalidated':'r01 was an invalid -I dependency environment; all negative results there were import failures, not behavioral validation',", 1)
ast.parse(source)
new = ROOT / 'probe_writer_metadata_r05_r02.py'
with new.open('x', encoding='utf-8', newline='\n') as f:
    f.write(source)
print(hashlib.sha256(new.read_bytes()).hexdigest())
