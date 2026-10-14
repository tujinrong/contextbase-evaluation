"""Capture only unchanged, independently approved AI HTML as inert offline views."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import os
from bs4 import BeautifulSoup
from contextbase.ai import capsule
from contextbase.ai import rendering

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))

def signature(markup):
    soup = BeautifulSoup(markup, 'html.parser')
    return [(tag.name, sorted((key, tuple(value) if isinstance(value, list) else value)
            for key, value in tag.attrs.items()),
            tag.get_text() if tag.name not in ('style','head','html') else None)
            for tag in soup.find_all(True)]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pin', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--deadline', default='2026-10-13T20:15:58Z')
    args=parser.parse_args()
    if datetime.now(timezone.utc) >= datetime.fromisoformat(args.deadline.replace('Z','+00:00')):
        raise TimeoutError('User deadline reached')
    pin_path=capsule.safe_path(args.pin)
    pin_before=pin_path.read_bytes()
    pin=json.loads(pin_before)
    if pin['independentReviewApproved'] is not True or pin['findings'] or pin['unresolved']:
        raise ValueError('An approved independent meaning review is required')
    bound={pin['canonicalMarkdown']:pin['parentSha256'], pin['projectionFile']:pin['projectionSha256'],
           pin['independentReview']:pin['independentReviewSha256'], pin['result']:pin['resultSha256'],
           pin['before']:pin['beforeSha256'], pin['after']:pin['afterSha256']}
    for entry in pin['html']:
        if entry['aiHtmlVerbatim'] is not True:
            raise ValueError('Only verbatim AI state HTML is accepted')
        bound[entry['path']]=entry['sha256']
    if len(pin['html']) != 4 or len({e['stateId'] for e in pin['html']}) != 4:
        raise ValueError('Exactly four distinct approved states are required')
    if any(sha(capsule.safe_path(Path(path))) != digest for path,digest in bound.items()):
        raise ValueError('One approved input changed before capture')
    destination=capsule.safe_path(args.destination)
    if destination.exists():
        raise FileExistsError('Fresh immutable capture directory required')
    destination.mkdir(parents=True)
    records=[]
    requests=[]
    with rendering._playwright_runtime(destination/'runtime') as playwright:
        browser=playwright.chromium.launch(executable_path=os.environ['CONTEXTBASE_CHROMIUM_EXE'],headless=True)
        context=browser.new_context(java_script_enabled=False, viewport={'width':1440,'height':1000},device_scale_factor=1)
        def abort(route):
            requests.append(route.request.url)
            route.abort()
        context.route('**/*',abort)
        try:
            for entry in pin['html']:
                if datetime.now(timezone.utc) >= datetime.fromisoformat(args.deadline.replace('Z','+00:00')):
                    raise TimeoutError('User deadline reached during capture')
                source=capsule.safe_path(Path(entry['path']))
                original=source.read_text(encoding='utf-8')
                safe,removed=rendering._sanitize(original, source.parent, source.parent)
                if removed or signature(original) != signature(safe):
                    raise ValueError('Sanitizer would alter approved state structure or text: '+entry['stateId'])
                page=context.new_page()
                page.set_default_timeout(30000)
                try:
                    page.set_content(safe,wait_until='load',timeout=30000)
                    data=rendering._capture(page)
                    info=rendering._png_info(data)
                    if not info['nonblank']:
                        raise ValueError('Blank state capture')
                    target=destination/(entry['stateId']+'.png')
                    target.write_bytes(data)
                    derived=destination/(entry['stateId']+'.html')
                    derived.write_text(safe,encoding='utf-8')
                    records.append({'stateId':entry['stateId'],'path':str(target),'sha256':sha(target),
                        'width':info['width'],'height':info['height'],'scale':1,
                        'aiHtmlPath':str(source),'aiHtmlSha256':entry['sha256'],
                        'sanitizedHtmlPath':str(derived),'sanitizedHtmlSha256':sha(derived),
                        'sanitizerRemoved':removed,'textAndControlStructureUnchanged':True,
                        'actuallyReviewed':False})
                finally:
                    page.close()
        finally:
            context.close()
            browser.close()
    if requests:
        raise ValueError('Approved state attempted resource requests: '+repr(requests))
    if pin_path.read_bytes()!=pin_before or any(sha(capsule.safe_path(Path(p)))!=d for p,d in bound.items()):
        raise ValueError('Approved inputs changed during capture')
    receipt={'schema':'reverse-agent-state-static-capture/1','createdAt':datetime.now(timezone.utc).isoformat(),
        'documentId':pin['documentId'],'referenceMode':pin['mode'],
        'canonicalDocumentPath':pin['canonicalMarkdown'],'documentSha256':pin['parentSha256'],
        'sourceSnapshotSha256':pin['capsuleManifestSha256'], 'exportPinSha256':sha(pin_path),
        'independentMeaningReviewSha256':pin['independentReviewSha256'],
        'rendererPath':str(Path(rendering.__file__).resolve()),'rendererSha256':sha(Path(rendering.__file__)),
        'javaScriptEnabled':False,'externalRequests':requests,'images':records,
        'inputHashesUnchanged':True,'nativeApproval':False,'originalApplicationExecuted':False,
        'pixelEquivalenceToRunningApplicationVerified':False,'finalQualified':False}
    result=destination/'capture.json'
    result.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'documentId':pin['documentId'],'states':len(records),'images':[r['path'] for r in records],
        'nativeApproval':False,'externalRequests':len(requests)}))

if __name__=='__main__':
    main()
