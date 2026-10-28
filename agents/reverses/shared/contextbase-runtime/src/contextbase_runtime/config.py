"""Project profiles for paths and publication, without cross-agent execution."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import json
import os
from pathlib import Path
import tomllib
import uuid

from . import contracts
from .handoff import PAYLOAD, validate_lineage, validate_catalog_policy
from .paths import safe_path
from .sources import _json

VERSION = 'contextbase-project/1'
PREVIOUS = {'relationship': 'discovery', 'behavior': 'relationship'}


def overlap(left, right):
    return left == right or left in right.parents or right in left.parents


def read_json(path):
    path = safe_path(Path(path))
    if path.stat().st_size > 32_000_000:
        raise ValueError('Project JSON input exceeds the read limit')
    return _json(path)


def _atomic_json(path, value, temporary_root):
    temporary = safe_path(temporary_root / ('publish-' + uuid.uuid4().hex + '.json'))
    try:
        with temporary.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, safe_path(path))
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def _publication_lock(directory):
    temporary = safe_path(directory / '.tmp')
    temporary.mkdir(parents=True, exist_ok=True)
    lock = safe_path(temporary / 'publication.lock')
    try:
        handle = lock.open('x', encoding='ascii')
    except FileExistsError as exc:
        raise ValueError('Another publication is active; inspect a stale publication lock before recovery') from exc
    try:
        with handle:
            handle.write(str(os.getpid()))
            handle.flush()
            os.fsync(handle.fileno())
            yield temporary
    finally:
        lock.unlink(missing_ok=True)


@dataclass(frozen=True)
class ProjectProfile:
    config_path: Path
    name: str
    source: Path
    request_path: Path
    output_root: Path
    work_root: Path
    request: dict
    context_mode: str = 'full'

    @classmethod
    def load(cls, config_path, name=None):
        path = safe_path(Path(config_path))
        if path.stat().st_size > 1_000_000:
            raise ValueError('Project configuration exceeds the read limit')
        with path.open('rb') as stream:
            document = tomllib.load(stream)
        if (set(document) != {'schema', 'default_profile', 'profiles'}
                or document['schema'] != VERSION or not isinstance(document['default_profile'], str)
                or not isinstance(document['profiles'], dict) or not document['profiles']):
            raise ValueError('A contextbase-project/1 configuration with named profiles is required')
        selected = document['default_profile'] if name is None else name
        if selected not in document['profiles']:
            raise ValueError('Unknown project profile: ' + str(selected))
        section = document['profiles'][selected]
        required = {'source', 'request', 'output', 'work'}
        if (not isinstance(section, dict) or not required.issubset(section)
                or set(section) - required - {'context_mode'}
                or any(not isinstance(section[key], str) or not section[key].strip() for key in required)):
            raise ValueError('A profile requires source, request, output and work paths')
        context_mode = section.get('context_mode', 'full')
        if not isinstance(context_mode, str) or context_mode not in {'full', 'evidence', 'incremental'}:
            raise ValueError('Profile context_mode must be full, evidence or incremental')

        def resolve(key):
            value = Path(section[key])
            return safe_path(value if value.is_absolute() else path.parent / value)

        source, request_path, output, work = (resolve(key) for key in ('source', 'request', 'output', 'work'))
        if any(overlap(left, right) for left, right in ((source, work), (source, output), (work, output))):
            raise ValueError('Configured source, work and output trees must be disjoint')
        if any(overlap(tree, item) for tree in (work, output) for item in (path, request_path)):
            raise ValueError('Configuration and request inputs must be outside work and output trees')
        request = read_json(request_path)
        contracts.validate_request(request)
        return cls(path, selected, source, request_path, output, work, request, context_mode)

    def work(self, agent_name):
        return safe_path(self.work_root / agent_name)

    def output(self, agent_name):
        return safe_path(self.output_root / agent_name / 'contextbase.json')

    def binding(self, agent_name):
        return {'schema': 'contextbase-target/1', 'profile': self.name,
                'projectId': self.request['projectId'], 'source': str(self.source),
                'requestSha256': contracts.digest(self.request), 'outputRoot': str(self.output_root),
                'agent': agent_name}

    def describe(self, agent_type):
        previous = PREVIOUS.get(agent_type.stage)
        return {'profile': self.name, 'source': str(self.source), 'request': str(self.request_path),
                'work': str(self.work(agent_type.name)), 'output': str(self.output(agent_type.name)),
                'handoff': str(self.output(previous + '-agent')) if previous else None,
                'sourceMode': 'sealed-snapshot-on-init', 'contextMode': self.context_mode,
                'agent': agent_type.name}

    def _validate_context_mode(self, agent):
        expected = {}
        if self.context_mode == 'evidence':
            from .evidence_dialog import VERSION as EVIDENCE_POLICY
            expected['evidencePolicy'] = EVIDENCE_POLICY
        elif self.context_mode == 'incremental':
            from .incremental import VERSION as INCREMENTAL_POLICY
            expected['incrementalPolicy'] = INCREMENTAL_POLICY
        elif self.context_mode != 'full':
            raise ValueError('Unknown project context_mode')
        actual = {key: agent.session.config[key] for key in ('evidencePolicy', 'incrementalPolicy')
                  if key in agent.session.config}
        if actual != expected:
            raise ValueError('Project context_mode differs from the initialized workspace; '
                             'select a separate work directory and initialize it with the matching mode')

    def bind(self, agent):
        self._validate_context_mode(agent)
        agent.session.store.put('project.json', self.binding(agent.name))

    def validate_workspace(self, agent, *, check_upstream=False):
        if not agent.session.store.path('project.json').exists():
            raise ValueError('Workspace was not initialized with this project profile')
        if (agent.session.store.get('project.json') != self.binding(agent.name)
                or agent.session.config['request'] != self.request
                or agent.session.source.manifest['sourceRoot'] != str(self.source)):
            raise ValueError('Project profile, source, request or output changed; select a separate work directory')
        self._validate_context_mode(agent)
        if check_upstream:
            self.validate_upstream(agent)

    def _result(self, agent_name):
        artifact = self.output(agent_name)
        if not artifact.exists():
            return None
        marker = safe_path(artifact.parent / 'target.json')
        if not marker.exists() or read_json(marker) != self.binding(agent_name):
            raise ValueError('Upstream result belongs to a different profile/source/goal; export the matching predecessor')
        envelope = read_json(artifact)
        self._validate_envelope(envelope, agent_name)
        return envelope

    def upstream(self, agent_type):
        previous = PREVIOUS.get(agent_type.stage)
        if previous is None:
            return None
        envelope = self._result(previous + '-agent')
        if envelope is not None and previous == 'relationship':
            ancestor = self._result('discovery-agent')
            if ancestor is not None:
                # Audit is not a version binding: withdrawing acceptance can
                # leave it unchanged. Match the exact imported ancestor instead.
                if envelope['payload']['premises']['discovery'] != ancestor['sha256']:
                    raise ValueError('Stale prerequisite: relationship predates the current discovery result; '
                                     'revalidate in a separate work directory')
        return envelope

    def validate_upstream(self, agent):
        if agent.stage not in PREVIOUS or not agent.session.store.path('incoming.json').exists():
            return
        current = self.upstream(agent)
        imported = agent.session.store.get('incoming.json')
        if current is None or current['sha256'] != imported['sha256']:
            raise ValueError('Stale prerequisite: the configured predecessor changed or is missing; '
                             're-import into a separate work directory')

    def receive_if_ready(self, agent):
        state = agent.session._state()
        if (state['status'] != 'active' or agent.stage not in PREVIOUS or state['revision']
                or agent.session.store.path('incoming.json').exists()):
            return
        incoming = self.upstream(agent)
        if incoming is not None:
            from .handoff import receive
            receive(agent, incoming)

    def _validate_envelope(self, envelope, agent_name):
        if (not isinstance(envelope, dict) or set(envelope) != {'sha256', 'payload'}
                or envelope['sha256'] != contracts.digest(envelope['payload'])):
            raise ValueError('Configured result content fingerprint mismatch')
        contracts.validate(envelope['payload'], PAYLOAD)
        validate_lineage(envelope['payload'])
        validate_catalog_policy(envelope['payload'])
        if (envelope['payload']['producer'] + '-agent' != agent_name
                or envelope['payload']['request'] != self.request):
            raise ValueError('Configured result producer or original request does not match this target')

    def publish(self, agent):
        self.validate_workspace(agent, check_upstream=True)
        envelope = agent.export()
        self._validate_envelope(envelope, agent.name)
        output = self.output(agent.name)
        marker = safe_path(output.parent / 'target.json')
        owner = self.binding(agent.name)
        with _publication_lock(output.parent) as temporary:
            self.validate_upstream(agent)
            if marker.exists():
                if read_json(marker) != owner:
                    raise ValueError('Output belongs to another profile/source/goal; configure a separate output directory')
            elif output.exists():
                raise ValueError('Existing result has no target ownership; configure a separate output directory')
            else:
                _atomic_json(marker, owner, temporary)
            existing = None
            if output.exists():
                existing = read_json(output)
                self._validate_envelope(existing, agent.name)
            if existing != envelope:
                _atomic_json(output, envelope, temporary)
        return {'status': 'exported', 'profile': self.name, 'output': str(output),
                'sha256': envelope['sha256'], 'unchanged': existing == envelope}
