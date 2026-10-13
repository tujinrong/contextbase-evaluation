"""Immutable evaluator artifact writes; no scoring or generator rules.

All new writes are exclusive-create. A correction keeps its old artifact,
stores the exact old bytes, and creates a separate version plus transition.
The group is not a filesystem transaction: an interrupted operation may leave
new artifacts incomplete, but it never silently overwrites the old artifact.
"""
from pathlib import Path
import datetime
import hashlib
import json

EVALUATOR_ROOT=Path(__file__).resolve().parent

def evaluator_path(path):
    resolved=Path(path).resolve()
    if resolved==EVALUATOR_ROOT or not resolved.is_relative_to(EVALUATOR_ROOT):
        raise ValueError('Evaluator artifact path must remain within evaluator-only.')
    return resolved

def digest(raw):return hashlib.sha256(raw).hexdigest()

def exclusive_bytes(path,raw):
    path=evaluator_path(path)
    if not isinstance(raw,bytes):raise TypeError('Exact bytes are required.')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(raw)
    return {'path':str(path),'sha256':digest(raw),'bytes':len(raw)}

def json_bytes(payload):
    return (json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

def exclusive_json(path,payload):return exclusive_bytes(path,json_bytes(payload))

def corrected_json(previous,new_version,transition,payload,*,reason,change_summary):
    previous=evaluator_path(previous)
    new_version=evaluator_path(new_version)
    transition=evaluator_path(transition)
    if len({previous,new_version,transition})!=3:
        raise ValueError('Old artifact, new version, and transition must use distinct paths.')
    if not reason or not change_summary:raise ValueError('Explicit correction context is required.')
    # Refuse before creating snapshots when a destination is already occupied.
    for destination in (new_version,transition):
        if destination.exists():raise FileExistsError(destination)
    old=previous.read_bytes();old_sha=digest(old)
    snapshot=evaluator_path(previous.parent/'artifact-history'/(previous.stem+'-'+old_sha+previous.suffix))
    if snapshot.exists():
        if snapshot.read_bytes()!=old:raise ValueError('Existing history snapshot bytes differ.')
        prior={'path':str(snapshot),'sha256':old_sha,'bytes':len(old)}
    else:prior=exclusive_bytes(snapshot,old)
    if previous.read_bytes()!=old:raise ValueError('Previous artifact changed while preserving it.')
    current=exclusive_json(new_version,payload)
    record={'schema':'evaluator-artifact-transition/1','classification':'EVALUATOR_ONLY',
      'generatorMayRead':False,'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'previousArtifact':{'path':str(previous),'sha256':old_sha,'bytes':len(old)},
      'previousByteSnapshot':prior,'newVersion':current,'reason':reason,
      'changeSummary':change_summary,'previousArtifactOverwritten':False,
      'exactPreviousBytesPreserved':True,'semanticAcceptanceInferred':False}
    saved=exclusive_json(transition,record)
    return {'previousSnapshot':prior,'newVersion':current,'transition':saved}
