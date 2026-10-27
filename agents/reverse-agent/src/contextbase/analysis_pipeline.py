"""Optional composition through the three independent agents' public interface."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def run(source, work, request, *, timeout=1800, inline_sources=False):
    from contextbase_discovery import DiscoveryAgent
    from contextbase_relationship import RelationshipAgent
    from contextbase_behavior import BehaviorAgent
    from contextbase_runtime.cli import load
    from contextbase_runtime.paths import safe_path

    source, work = safe_path(Path(source)), safe_path(Path(work))
    if source == work or source in work.parents or work in source.parents:
        raise ValueError('Pipeline source and work trees must be disjoint')
    if work.exists():
        raise ValueError('Pipeline requires a fresh work directory; resume agents independently')
    request = load(Path(request)) if not isinstance(request, dict) else request
    from contextbase_runtime import contracts
    contracts.validate_request(request)
    obligations = request['goal']['requirements']
    scopes = list(dict.fromkeys(item['scope'] for item in obligations))
    results, handoffs = [], []
    for scope in scopes:
        handoff = None
        # A local slice advances before unrelated catalogs are completed.
        local_work = work / contracts.digest(scope)[:16]
        for agent_type in (DiscoveryAgent, RelationshipAgent, BehaviorAgent):
            identifiers = [item['id'] for item in obligations
                           if item['scope'] == scope and item['stage'] == agent_type.stage]
            if not identifiers:
                continue
            agent = agent_type.create(source, local_work / agent_type.stage, request, handoff=handoff)
            result = agent.run(requirements=identifiers, timeout=timeout, inline_sources=inline_sources)
            results.append({'agent': agent.name, 'scope': scope, 'result': result})
            if result['status'] != 'complete':
                return {'status': result['status'], 'agents': results, 'handoffs': handoffs}
            handoff = agent.export()
        handoffs.append({'scope': scope, 'handoff': handoff})
    return {'status': 'complete', 'agents': results, 'handoffs': handoffs}


def main(argv=None):
    parser = argparse.ArgumentParser(description='独立3Agentを公開契約だけで任意に直列実行する')
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=1800)
    parser.add_argument('--inline-sources', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = run(args.source, args.work, args.request, timeout=args.timeout,
                     inline_sources=args.inline_sources)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['status'] == 'complete' else 2
    except ImportError as exc:
        print(json.dumps({'status': 'failed', 'error': 'Install the independent agent packages: ' + str(exc)}))
        return 1
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}, ensure_ascii=False))
        return 1
    except KeyboardInterrupt:
        return 130
