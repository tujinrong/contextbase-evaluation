"""Read Application Error(1000) events for explicit owned PID/time intervals."""
from pathlib import Path
import argparse,datetime as dt,json,sys,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import build
import win32evtlog
NS={'e':'http://schemas.microsoft.com/win/2004/08/events/event'}
def inspect(start,end,pids):
    query="*[System[(EventID=1000) and TimeCreated[@SystemTime >= '"+start+"' and @SystemTime <= '"+end+"']]]"
    handle=win32evtlog.EvtQuery('Application',win32evtlog.EvtQueryReverseDirection,query)
    matches=[]; scanned=0
    try:
        while True:
            try:events=win32evtlog.EvtNext(handle,32)
            except Exception as error:
                if getattr(error,'winerror',None)==259:break
                raise
            if not events:break
            for event in events:
                xml=ET.fromstring(win32evtlog.EvtRender(event,win32evtlog.EvtRenderEventXml));scanned+=1
                data={v.get('Name'):v.text or '' for v in xml.findall('e:EventData/e:Data',NS)}
                raw=data.get('ProcessId',data.get('FaultingProcessId',''))
                try:pid=int(raw,16) if raw.lower().startswith('0x') else int(raw)
                except ValueError:pid=None
                if pid in pids:matches.append({'pid':pid,'application':data.get('AppName',data.get('FaultingApplicationName')),'exceptionCode':data.get('ExceptionCode'),'eventRecordId':xml.findtext('e:System/e:EventRecordID',namespaces=NS)})
    finally:handle=None
    return {'channel':'Application','eventId':1000,'startUtc':start,'endUtc':end,'ownedPids':sorted(pids),'eventsScanned':scanned,'matchingErrors':matches,'status':'PASS' if not matches else 'FAIL'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--cycle',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    record=json.loads(a.cycle.read_text(encoding='utf-8-sig'));office=record['ownedOffice']
    pids={office['accessPid']}|{x['ownedPid'] for x in office.get('excel',[])}
    start=dt.datetime.fromisoformat(record['startedAt']).astimezone(dt.timezone.utc).isoformat().replace('+00:00','Z')
    end=dt.datetime.fromisoformat(record['endedAt']).astimezone(dt.timezone.utc).isoformat().replace('+00:00','Z')
    result=inspect(start,end,pids);result['artifactSha256']=record['artifactSha256']
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
