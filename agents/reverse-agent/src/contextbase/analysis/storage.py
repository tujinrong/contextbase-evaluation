"""Exclusive artifacts and an atomic pointer in a host-owned workspace.

Content hashes detect damage and stale bindings. They are not signatures against
a local actor who can rewrite both an artifact and its seal. The host must own
the workspace; provider roles receive read-only snapshot access, not store access.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import uuid

from ..ai.capsule import material_path, safe_path
from .contracts import digest


class ArtifactStore:
    def __init__(self, root: Path):
        self.root = safe_path(root)

    def path(self, relative: str) -> Path:
        return material_path(self.root, relative)

    def put(self, relative: str, payload: dict) -> None:
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if self.get(relative) == payload:
                return
            raise ValueError('Immutable analysis artifact already exists: ' + relative)
        envelope = {'sha256': digest(payload), 'payload': payload}
        temporary = target.with_name(target.name + '.pending-' + uuid.uuid4().hex)
        try:
            with temporary.open('x', encoding='utf-8', newline='\n') as handle:
                json.dump(envelope, handle, ensure_ascii=False, sort_keys=True, allow_nan=False)
                handle.write('\n')
                handle.flush()
                os.fsync(handle.fileno())
            # Link publishes a completed file exclusively; replace would allow
            # another writer's immutable artifact to be overwritten.
            try:
                os.link(temporary, target)
            except FileExistsError:
                if self.get(relative) != payload:
                    raise ValueError('Immutable analysis artifact collision: ' + relative)
        finally:
            temporary.unlink(missing_ok=True)

    def get(self, relative: str) -> dict:
        path = self.path(relative)
        if path.stat().st_size > 32_000_000:
            raise ValueError('Analysis artifact exceeds the read limit')
        envelope = json.loads(path.read_text(encoding='utf-8'))
        if set(envelope) != {'sha256', 'payload'} or digest(envelope['payload']) != envelope['sha256']:
            raise ValueError('Analysis artifact integrity mismatch: ' + relative)
        return envelope['payload']

    def save_state(self, payload: dict) -> None:
        """The old pointer survives failure before replace; orphan artifacts are harmless."""
        temporary = 'state-' + uuid.uuid4().hex + '.tmp'
        self.put(temporary, payload)
        try:
            os.replace(self.path(temporary), self.path('state.json'))
        finally:
            self.path(temporary).unlink(missing_ok=True)

    @contextmanager
    def transaction(self):
        lock = self.path('session.lock')
        try:
            handle = lock.open('x', encoding='ascii')
        except FileExistsError as exc:
            raise ValueError('Another session writer is active; inspect a stale lock before recovery') from exc
        try:
            with handle:
                handle.write(str(os.getpid()))
                handle.flush()
                os.fsync(handle.fileno())
                yield self.get('state.json')
        finally:
            lock.unlink(missing_ok=True)
