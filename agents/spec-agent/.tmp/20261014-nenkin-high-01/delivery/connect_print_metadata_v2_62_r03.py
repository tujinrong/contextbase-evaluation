"""PRINT_METADATA_ONLY: raw XML splices, no authoring/conversion/provider/Excel.
Only a caller-pinned, own fresh Artifact XLSX under this run's delivery is eligible.
CLI emits a separate fresh file; source is never saved. Unsupported XML/ZIP -> HOLD.
Stdlib Expat proves expanded element paths and byte positions before lexical splicing.
Unmodified ZIP payload AND local compressed records remain byte exact. Central offsets
necessarily change. This program does not prove author ownership or document geometry:
the caller must supply a pinned Artifact author receipt and explicit sheet plan.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import sys
import xml.parsers.expat as expat
import zipfile
import io
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from xml.sax.saxutils import escape

SCHEMA = "print-metadata-v2-62/1"
S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
P = "http://schemas.openxmlformats.org/package/2006/relationships"
RUN_DELIVERY = Path(r"D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery")
MAX_ARCHIVE = 128_000_000
MAX_TOTAL = 256_000_000
MAX_XML = 16_000_000
SHEET_ORDER = ["sheetPr","dimension","sheetViews","sheetFormatPr","cols","sheetData",
 "sheetCalcPr","sheetProtection","protectedRanges","scenarios","autoFilter","sortState",
 "dataConsolidate","customSheetViews","mergeCells","phoneticPr","conditionalFormatting",
 "dataValidations","hyperlinks","printOptions","pageMargins","pageSetup","headerFooter",
 "rowBreaks","colBreaks","customProperties","cellWatches","ignoredErrors","smartTags",
 "drawing","legacyDrawing","legacyDrawingHF","picture","oleObjects","controls",
 "webPublishItems","tableParts","extLst"]
BOOK_ORDER = ["fileVersion","fileSharing","workbookPr","workbookProtection","bookViews",
 "sheets","functionGroups","externalReferences","definedNames","calcPr","oleSize",
 "customWorkbookViews","pivotCaches","smartTagPr","smartTagTypes","webPublishing",
 "fileRecoveryPr","webPublishObjects","extLst"]

def digest(data): return hashlib.sha256(data).hexdigest()
def require(ok, message):
    if not ok: raise ValueError("HOLD: " + message)
def local(tag):
    return tag.split("|",1)[-1]
def tag(namespace, name): return namespace + "|" + name

@dataclass
class Node:
    name: str
    attrs: dict
    start: int
    open_end: int
    empty: bool
    lexical_name: bytes
    parent: "Node | None" = None
    end_start: int = 0
    end: int = 0
    children: list = field(default_factory=list)

def tag_end(raw, start):
    require(raw[start:start+1] == b"<", "parser byte offset is not a tag")
    quote = 0
    for index in range(start+1, len(raw)):
        byte = raw[index]
        if quote:
            if byte == quote: quote = 0
        elif byte in (34,39): quote = byte
        elif byte == 62: return index+1
    raise ValueError("HOLD: unclosed XML tag")

def parse_xml(raw):
    require(len(raw) <= MAX_XML, "XML exceeds bounded size")
    require(not raw.startswith((b"\xff\xfe",b"\xfe\xff")) and b"\x00" not in raw, "only UTF-8 XML is supported")
    raw.decode("utf-8")
    parser = expat.ParserCreate(namespace_separator="|")
    parser.buffer_text = False
    stack=[]; roots=[]
    def start(name, attrs):
        pos=parser.CurrentByteIndex; stop=tag_end(raw,pos)
        opening=raw[pos:stop]
        lexical=opening[1:].split(None,1)[0].rstrip(b"/>")
        node=Node(name,attrs,pos,stop,opening.rstrip().endswith(b"/>"),lexical,stack[-1] if stack else None)
        if stack: stack[-1].children.append(node)
        else: roots.append(node)
        stack.append(node)
    def end(name):
        require(bool(stack) and stack[-1].name==name, "XML parser stack mismatch")
        node=stack.pop()
        node.end_start=node.open_end if node.empty else parser.CurrentByteIndex
        node.end=node.open_end if node.empty else tag_end(raw,node.end_start)
    def forbidden(*args): raise ValueError("HOLD: PI/DTD/entity XML is prohibited")
    def xml_decl(version, encoding, standalone):
        require(version=="1.0" and (not encoding or encoding.lower() in {"utf-8","utf8"}), "unsupported XML declaration")
    parser.StartElementHandler=start; parser.EndElementHandler=end
    parser.ProcessingInstructionHandler=forbidden
    parser.StartDoctypeDeclHandler=forbidden
    parser.EntityDeclHandler=forbidden
    parser.ExternalEntityRefHandler=forbidden
    parser.XmlDeclHandler=xml_decl
    parser.Parse(raw,True)
    require(len(roots)==1 and not stack, "exactly one XML root required")
    return roots[0]

def children(node, namespace, name):
    return [c for c in node.children if c.name == tag(namespace,name)]

def ordered_children(root, names):
    ranks={name:i for i,name in enumerate(names)}; previous=-1; counts={}
    for node in root.children:
        require(node.name.startswith(S+"|") and local(node.name) in ranks, "unknown direct XML element: "+node.name)
        rank=ranks[local(node.name)]
        require(rank>=previous, "invalid source XML element order")
        previous=rank; counts[node.name]=counts.get(node.name,0)+1
        require(counts[node.name]==1 or local(node.name)=="conditionalFormatting", "duplicate singleton XML element")
    return ranks

def qualified(root, name):
    prefix=root.lexical_name.split(b":",1)[0]+b":" if b":" in root.lexical_name else b""
    return prefix+name.encode("ascii")

def xml_element(root, name, attrs=None, text=None):
    q=qualified(root,name)
    fields=b"".join(b" "+k.encode("ascii")+b'="'+escape(str(v),{'"':"&quot;"}).encode("utf-8")+b'"' for k,v in (attrs or {}).items())
    return b"<"+q+fields+(b"/>" if text is None else b">"+escape(text).encode("utf-8")+b"</"+q+b">")

def attr_splice(raw,node,wanted):
    """Quote-aware tokens only after Expat validated this exact opening tag.
    Keep every unselected attribute token, spacing, QName and quote unchanged.
    """
    require(not node.children, "printing node unexpectedly contains child elements")
    if not node.empty: require(not raw[node.open_end:node.end_start].strip(), "printing node contains text")
    opening=raw[node.start:node.open_end]
    i=1+len(node.lexical_name); found={}; patches=[]
    while i<len(opening):
        while i<len(opening) and opening[i] in b" \t\r\n": i+=1
        if opening[i:i+1] in (b"/",b">"): break
        a=i
        while i<len(opening) and opening[i] not in b" \t\r\n=": i+=1
        key=opening[a:i].decode("utf-8")
        while opening[i] in b" \t\r\n": i+=1
        require(opening[i:i+1]==b"=", "attribute lexical boundary mismatch");i+=1
        while opening[i] in b" \t\r\n": i+=1
        quote=opening[i];require(quote in (34,39), "unquoted XML attribute");i+=1
        value_start=i
        while i<len(opening) and opening[i]!=quote:i+=1
        require(i<len(opening), "unclosed attribute")
        found[key]=True
        if key in wanted:
            value=escape(str(wanted[key]),{'\"':"&quot;","'":"&apos;"}).encode("utf-8")
            if opening[value_start:i]!=value: patches.append((value_start,i,value))
        i+=1
    additions=b"".join(b" "+k.encode("ascii")+b'="'+escape(str(v),{'"':"&quot;"}).encode()+b'"' for k,v in wanted.items() if k not in found)
    if additions:
        end=len(opening)-1
        if opening[end-1:end]==b"/":end-=1
        patches.append((end,end,additions))
    for a,b,value in sorted(patches,reverse=True):opening=opening[:a]+value+opening[b:]
    return opening

def splice(raw, operations):
    operations=sorted(operations,key=lambda x:(x[0],0 if x[0]==x[1] else 1,x[4]))
    cursor=0; out=[]; records=[]; outlen=0
    for a,b,value,reason,_ in operations:
        require(0<=cursor<=a<=b<=len(raw),"overlapping or invalid allowed XML spans")
        gap=raw[cursor:a];out.append(gap);outlen+=len(gap)
        records.append({"sourceStart":a,"sourceEnd":b,"outputStart":outlen,"outputEnd":outlen+len(value),
                        "reason":reason,"beforeBase64":base64.b64encode(raw[a:b]).decode(),
                        "afterBase64":base64.b64encode(value).decode()})
        out.append(value);outlen+=len(value);cursor=b
    out.append(raw[cursor:]);result=b"".join(out)
    reverse=result
    for record in reversed(records):
        a,b=record["outputStart"],record["outputEnd"]
        require(reverse[a:b]==base64.b64decode(record["afterBase64"]),"inverse span mismatch")
        reverse=reverse[:a]+base64.b64decode(record["beforeBase64"])+reverse[b:]
    require(reverse==raw,"raw XML inverse restoration failed")
    parse_xml(result)
    return result,records

def insert_offset(root,ranks,name):
    require(not root.empty,"self-closing root unsupported for insertion")
    rank=ranks[name]
    return next((c.start for c in root.children if ranks[local(c.name)]>rank),root.end_start)

def sheet_settings(item):
    require(type(item.get("ordinal")) is int and item["ordinal"]>=0,"sheet ordinal must be a nonnegative integer")
    require(isinstance(item.get("name"),str) and bool(item["name"]),"sheet exact name required")
    kind=item.get("kind");last=item.get("lastRow")
    require(type(last) is int and 1<=last<=1048576,"lastRow must be an explicit bounded integer")
    if kind=="cover":
        require(last==36,"cover must end at row 36")
        return "O6:AU36",None,1
    if kind=="normal":return f"A1:BJ{last}",1,0
    if kind=="list":
        columns=item.get("columns")
        require(type(columns) is int and 1<=columns<=16384,"LIST columns must be an integer in 1..16384")
        require("itemList" not in item or type(item["itemList"]) is bool,"itemList must be a boolean when declared")
        if item.get("itemList",False):
            require(columns==10,"item LIST must declare ten columns")
        require(type(item.get("headerRow")) is int and item["headerRow"]==1,"LIST header must be row 1")
        column="";number=columns
        while number:
            number,digit=divmod(number-1,26)
            column=chr(65+digit)+column
        return f"A1:{column}{last}",1,0
    if kind=="table":
        require(item.get("columns")==9,"TABLE must declare nine columns")
        header=item.get("headerRow")
        require(type(header) is int and 1<=header<=last,"TABLE requires its explicit real header row")
        return f"A1:I{last}",header,0
    raise ValueError("HOLD: unknown sheet print kind")

def patch_sheet(raw,item):
    root=parse_xml(raw);require(root.name==tag(S,"worksheet"),"selected target is not an OOXML worksheet")
    ranks=ordered_children(root,SHEET_ORDER);ops=[]
    def set_print(name,attrs):
        match=children(root,S,name)
        if match:
            node=match[0];new=attr_splice(raw,node,attrs)
            if new!=raw[node.start:node.open_end]:ops.append((node.start,node.open_end,new,"worksheet/"+name,ranks[name]))
        else:
            pos=insert_offset(root,ranks,name)
            ops.append((pos,pos,xml_element(root,name,attrs),"insert worksheet/"+name,ranks[name]))
    _,_,fit=sheet_settings(item)
    set_print("printOptions",{"horizontalCentered":"1"})
    set_print("pageMargins",{"left":"0.25","right":"0.25","top":"0.4","bottom":"0.4","header":"0.15","footer":"0.15"})
    set_print("pageSetup",{"paperSize":"9","orientation":"landscape","fitToWidth":"1","fitToHeight":str(fit)})
    prs=children(root,S,"sheetPr")
    if not prs:
        pos=insert_offset(root,ranks,"sheetPr")
        q=qualified(root,"sheetPr")
        child=xml_element(root,"pageSetUpPr",{"fitToPage":"1"})
        ops.append((pos,pos,b"<"+q+b">"+child+b"</"+q+b">","insert worksheet/sheetPr/pageSetUpPr.fitToPage",ranks["sheetPr"]))
    else:
        pr=prs[0]
        require(all(c.name in {tag(S,"tabColor"),tag(S,"outlinePr"),tag(S,"pageSetUpPr")} for c in pr.children),"unknown sheetPr element")
        pr_ranks={tag(S,"tabColor"):0,tag(S,"outlinePr"):1,tag(S,"pageSetUpPr"):2}
        require([pr_ranks[c.name] for c in pr.children]==sorted(set(pr_ranks[c.name] for c in pr.children)),"invalid/duplicate sheetPr child order")
        settings=children(pr,S,"pageSetUpPr")
        require(len(settings)<=1,"duplicate pageSetUpPr")
        if settings:
            node=settings[0];new=attr_splice(raw,node,{"fitToPage":"1"})
            if new!=raw[node.start:node.open_end]:ops.append((node.start,node.open_end,new,"worksheet/sheetPr/pageSetUpPr.fitToPage",0))
        elif pr.empty:
            require(not pr.attrs,"self-closing sheetPr with nonprinting attributes requires caller resolution")
            opening=raw[pr.start:pr.open_end];ending=opening.rfind(b"/>")
            require(ending>=0,"sheetPr self-close boundary mismatch")
            new=opening[:ending]+b">"+xml_element(root,"pageSetUpPr",{"fitToPage":"1"})+b"</"+pr.lexical_name+b">"
            ops.append((pr.start,pr.end,new,"expand worksheet/sheetPr only for pageSetUpPr.fitToPage",0))
        else:
            ops.append((pr.end_start,pr.end_start,xml_element(root,"pageSetUpPr",{"fitToPage":"1"}),"insert worksheet/sheetPr/pageSetUpPr.fitToPage",0))
    result,records=splice(raw,ops)
    final=parse_xml(result);ordered_children(final,SHEET_ORDER)
    return result,records

def absolute_area(area):
    return re.sub(r"([A-Z]+)([1-9]\d*)",r"$\1$\2",area)

def patch_workbook(raw,items):
    root=parse_xml(raw);require(root.name==tag(S,"workbook"),"not an OOXML workbook")
    ranks=ordered_children(root,BOOK_ORDER)
    dn=children(root,S,"definedNames");ops=[];seen=set();additions=[]
    expected={}
    for item in items:
        area,repeat,_=sheet_settings(item);ordinal=item["ordinal"];quoted="'"+item["name"].replace("'","''")+"'!"
        expected[(ordinal,"_xlnm.Print_Area")]=quoted+absolute_area(area)
        expected[(ordinal,"_xlnm.Print_Titles")]=quoted+f"$"+str(repeat)+":$"+str(repeat) if repeat else None
    if dn:
        container=dn[0]
        require(all(c.name==tag(S,"definedName") for c in container.children),"unknown definedNames child")
        for node in container.children:
            require(node.attrs.get("name", "").casefold() not in {"_xlnm.auto_open","_xlnm.auto_close"},"macro defined name")
            sid=node.attrs.get("localSheetId")
            key=(int(sid),node.attrs.get("name")) if sid is not None and sid.isdigit() else None
            if key in expected:
                require(key not in seen,"duplicate selected print defined name");seen.add(key)
                require(not node.children,"print definedName contains elements")
                value=expected[key]
                new=xml_element(root,"definedName",{"name":key[1],"localSheetId":str(key[0])},value) if value else b""
                if new!=raw[node.start:node.end]:ops.append((node.start,node.end,new,"workbook/definedNames/"+key[1]+"/localSheetId="+str(key[0]),0))
        for key,value in expected.items():
            if key not in seen and value:additions.append(xml_element(root,"definedName",{"name":key[1],"localSheetId":str(key[0])},value))
        if additions:
            if container.empty:
                opening=raw[container.start:container.open_end];end=opening.rfind(b"/>")
                ops.append((container.start,container.end,opening[:end]+b">"+b"".join(additions)+b"</"+container.lexical_name+b">","expand workbook/definedNames for selected print names",0))
            else:ops.append((container.end_start,container.end_start,b"".join(additions),"insert selected workbook print definedNames",0))
    else:
        for key,value in expected.items():
            if value:additions.append(xml_element(root,"definedName",{"name":key[1],"localSheetId":str(key[0])},value))
        q=qualified(root,"definedNames")
        pos=insert_offset(root,ranks,"definedNames")
        ops.append((pos,pos,b"<"+q+b">"+b"".join(additions)+b"</"+q+b">","insert workbook/definedNames selected print names only",ranks["definedNames"]))
    result,records=splice(raw,ops);ordered_children(parse_xml(result),BOOK_ORDER)
    return result,records

def zip_name(name):
    parts=name.split("/")
    core=parts[:-1] if name.endswith("/") else parts
    require(name and not name.startswith("/") and "\\" not in name and ":" not in name and bool(core) and all(p not in {"",".",".."} for p in core),"unsafe ZIP member path")
    return name

def zip_index(raw):
    require(len(raw)<=MAX_ARCHIVE,"archive exceeds bounded size")
    end=raw.rfind(b"PK\x05\x06")
    require(end>=0 and end+22<=len(raw),"missing classic ZIP end record")
    values=struct.unpack("<4s4H2IH",raw[end:end+22]);_,disk,cddisk,diskn,total,size,start,comment=values
    require(disk==cddisk==0 and diskn==total and total<65535 and start+size==end and end+22+comment==len(raw),"multi-disk/ZIP64/trailing archive data unsupported")
    records=[];pos=start;names=set()
    for _ in range(total):
        require(raw[pos:pos+4]==b"PK\x01\x02","central directory boundary mismatch")
        fields=list(struct.unpack("<4s6H3I5H2I",raw[pos:pos+46]))
        stop=pos+46+fields[10]+fields[11]+fields[12];require(stop<=end,"central record overrun")
        filename=raw[pos+46:pos+46+fields[10]]
        name=filename.decode("utf-8" if fields[3]&2048 else "cp437");zip_name(name)
        require(name not in names,"duplicate ZIP member");names.add(name)
        require(not fields[3] & (1|8|64|8192) and fields[4] in {0,8} and fields[13]==0,"encrypted/data-descriptor/unsupported ZIP member")
        extra=raw[pos+46+fields[10]:pos+46+fields[10]+fields[11]]
        x=0
        while x<len(extra):
            require(x+4<=len(extra),"malformed ZIP extra")
            ident,length=struct.unpack("<2H",extra[x:x+4]);require(ident!=1 and x+4+length<=len(extra),"ZIP64/malformed ZIP extra unsupported");x+=4+length
        off=fields[16];require(off+30<=start,"local record outside local region")
        lf=list(struct.unpack("<4s5H3I2H",raw[off:off+30]));require(lf[0]==b"PK\x03\x04","local header mismatch")
        head_end=off+30+lf[9]+lf[10];local_end=head_end+lf[7]
        require(raw[off+30:off+30+lf[9]]==filename and [lf[2],lf[3],lf[6],lf[7],lf[8]]==[fields[3],fields[4],fields[7],fields[8],fields[9]],"local/central metadata mismatch")
        require(local_end<=start,"local payload overrun")
        records.append({"name":name,"central":raw[pos:stop],"centralFields":fields,"localFields":lf,"localStart":off,"headerEnd":head_end,"localEnd":local_end,"local":raw[off:local_end]})
        pos=stop
    require(pos==end,"central directory size mismatch")
    cursor=0
    for record in sorted(records,key=lambda r:r["localStart"]):
        require(record["localStart"]==cursor,"archive prefix/local gaps/overlapping records unsupported");cursor=record["localEnd"]
    require(cursor==start,"unaccounted local ZIP bytes")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        require(len(archive.infolist())==len(records) and sum(i.file_size for i in archive.infolist())<=MAX_TOTAL,"archive entry/size bound")
        require(archive.testzip() is None,"ZIP CRC failure")
        payload={r["name"]:archive.read(r["name"]) for r in records}
    for name,data in payload.items():
        lowered=name.lower()
        require(not any(s in lowered for s in ("vba","macrosheet","externallink")),"macros or external links prohibited")
        if name.endswith((".xml",".rels")):
            root=parse_xml(data)
            require(not any("macroenabled" in value.lower() for node in walk(root) for value in node.attrs.values()),"macro-enabled content type")
            for node in walk(root):
                if local(node.name)=="Relationship":
                    require(node.attrs.get("TargetMode","").strip().casefold()!="external" and "externallink" not in node.attrs.get("Type","").lower(),"external relationship prohibited")
    return records,payload,raw[end:end+22],raw[end+22:]

def walk(root):
    yield root
    for child in root.children:yield from walk(child)

def rewrite_zip(raw,records,payload,replacements,end_record,comment):
    out=[];offsets={};local_evidence=[]
    for record in sorted(records,key=lambda r:r["localStart"]):
        name=record["name"];offsets[name]=sum(map(len,out))
        data=replacements.get(name)
        if data is None:block=record["local"]
        else:
            require(name.endswith(".xml"),"only selected XML may be changed")
            fields=record["localFields"][:]
            comp=zlib.compressobj(6,zlib.DEFLATED,-15) if fields[3]==8 else None
            body=comp.compress(data)+comp.flush() if comp else data
            fields[6]=zlib.crc32(data)&0xffffffff;fields[7]=len(body);fields[8]=len(data)
            rest=raw[record["localStart"]+30:record["headerEnd"]]
            block=struct.pack("<4s5H3I2H",*fields)+rest+body
        out.append(block)
        local_evidence.append({"name":name,"beforeLocalRecordSha256":digest(record["local"]),"afterLocalRecordSha256":digest(block),"unchangedLocalRecord":block==record["local"]})
    start=sum(map(len,out));central=[]
    for record in records:
        fields=record["centralFields"][:];fields[16]=offsets[record["name"]]
        if record["name"] in replacements:
            data=replacements[record["name"]];block=next(out[i] for i,r in enumerate(sorted(records,key=lambda r:r["localStart"])) if r["name"]==record["name"])
            lf=struct.unpack("<4s5H3I2H",block[:30]);fields[7],fields[8],fields[9]=lf[6],lf[7],lf[8]
        central.append(struct.pack("<4s6H3I5H2I",*fields)+record["central"][46:])
    cd=b"".join(central);end=list(struct.unpack("<4s4H2IH",end_record));end[5]=len(cd);end[6]=start
    result=b"".join(out)+cd+struct.pack("<4s4H2IH",*end)+comment
    _,after,_,_=zip_index(result)
    require(set(after)==set(payload),"ZIP member identities changed")
    for name,before in payload.items():
        require(after[name]==replacements.get(name,before),"unexpected ZIP member payload change")
    return result,local_evidence

def connect_bytes(raw,plan):
    require(plan.get("schema")==SCHEMA and plan.get("scope")=="PRINT_METADATA_ONLY","explicit print-only plan required")
    items=plan.get("sheets");require(isinstance(items,list) and bool(items),"nonempty explicit selected sheets required")
    require(len({i.get("ordinal") for i in items})==len(items) and len({i.get("name") for i in items})==len(items),"duplicate selected sheet identity")
    for item in items:sheet_settings(item)
    records,payload,end,comment=zip_index(raw)
    require("xl/workbook.xml" in payload and "xl/_rels/workbook.xml.rels" in payload,"missing workbook bindings")
    book=parse_xml(payload["xl/workbook.xml"]);require(book.name==tag(S,"workbook"),"unexpected workbook root")
    sheet_lists=children(book,S,"sheets");require(len(sheet_lists)==1,"exact workbook sheets required")
    book_sheets=sheet_lists[0].children
    require(all(n.name==tag(S,"sheet") for n in book_sheets),"unexpected sheet binding element")
    require(all(isinstance(n.attrs.get("name"),str) and n.attrs["name"] for n in book_sheets),"empty workbook sheet name")
    require(len({n.attrs["name"].casefold() for n in book_sheets})==len(book_sheets),"duplicate workbook sheet names")
    relroot=parse_xml(payload["xl/_rels/workbook.xml.rels"]);require(relroot.name==tag(P,"Relationships"),"unexpected workbook relationship root")
    rels={};target_names=set()
    for node in relroot.children:
        require(node.name==tag(P,"Relationship") and node.attrs.get("Id") not in rels,"invalid or duplicate workbook relationship")
        target=node.attrs.get("Target","")
        require(target and "\\" not in target and ":" not in target,"unsafe workbook relationship target")
        # Only direct xl-relative paths without parent descent are eligible.
        canonical=target[1:] if target.startswith("/") else "xl/"+target
        require(canonical.startswith("xl/") and all(p not in {"",".",".."} for p in canonical.split("/")),"workbook relationship descent prohibited")
        rels[node.attrs["Id"]]=node.attrs
    # A selected physical worksheet may never also represent an unselected sheet.
    for node in book_sheets:
        rid=node.attrs.get(tag(R,"id"))
        require(rid in rels and rels[rid].get("Type")==R+"/worksheet","workbook sheet relationship type mismatch")
        relative=rels[rid]["Target"]
        physical=relative[1:] if relative.startswith("/") else "xl/"+relative
        require(physical in payload and physical not in target_names,"worksheet target alias/missing member")
        target_names.add(physical)
    replacements={};xml_evidence={};selected_targets=set()
    for item in items:
        ordinal=item["ordinal"];require(ordinal<len(book_sheets),"selected ordinal absent")
        node=book_sheets[ordinal];require(node.attrs.get("name")==item["name"],"exact selected sheet name/ordinal mismatch")
        rid=node.attrs.get(tag(R,"id"));require(rid in rels and rels[rid].get("Type")==R+"/worksheet","selected worksheet relationship mismatch")
        relative=rels[rid]["Target"]
        target=relative[1:] if relative.startswith("/") else "xl/"+relative
        require(target in payload and target not in selected_targets,"missing/aliased selected worksheet")
        selected_targets.add(target)
        changed,spans=patch_sheet(payload[target],item);replacements[target]=changed
        xml_evidence[target]={"beforeSha256":digest(payload[target]),"afterSha256":digest(changed),"inverseRawBytesEqual":True,"nonPrintingRawSegmentsUnchanged":True,"allowedSplices":spans}
    changed,spans=patch_workbook(payload["xl/workbook.xml"],items);replacements["xl/workbook.xml"]=changed
    xml_evidence["xl/workbook.xml"]={"beforeSha256":digest(payload["xl/workbook.xml"]),"afterSha256":digest(changed),"inverseRawBytesEqual":True,"nonPrintingRawSegmentsUnchanged":True,"allowedSplices":spans}
    changes={name:data for name,data in replacements.items() if data!=payload[name]}
    output,local_checks=rewrite_zip(raw,records,payload,changes,end,comment)
    receipt={"schema":"print-metadata-raw-connection-receipt/1","scope":"PRINT_METADATA_ONLY",
             "inputSha256":digest(raw),"outputSha256":digest(output),"selectedSheets":items,
             "selectedXmlMembers":sorted(replacements),"modifiedXmlMembers":sorted(changes),"xmlEvidence":xml_evidence,
             "allMemberPayloads":{name:{"beforeSha256":digest(data),"afterSha256":digest(replacements.get(name,data)),"unchanged":name not in replacements or data==replacements[name]} for name,data in payload.items()},
             "localRecordEvidence":local_checks,"nonSelectedLocalCompressedRecordsExact":all(c["unchangedLocalRecord"] for c in local_checks if c["name"] not in replacements),
             "allPayloadUnchangedMembersLocalRecordExact":all(c["unchangedLocalRecord"] for c in local_checks if c["name"] not in changes),
             "zipMemberOrderPreserved":True,"nonPrintingRawXmlBytesUnchanged":True,"rawXmlInverseRestorationExact":True,
             "cellValuesTypesBordersImagesMergesNotAuthoredOrChanged":True,
             "sourceAuthorOwnershipVerifiedByThisProgram":False,
             "formalApproval":False,"semanticApproval":False,"wholeDocumentApproval":False,"adoption":False,"published":False,
             "providerExecuted":False,"applicationExecuted":False,
             "limitations":["Caller must verify own fresh Artifact authorship and sheet geometry; lastRow/headerRow are explicit metadata supplied by caller.",
              "Classic seekable ZIP only: no ZIP64, encryption, data descriptors, prefix, gaps or trailing data.",
              "UTF-8 XML only; every PI, DTD/entity declaration and external relationship is rejected.",
              "Self-closing sheetPr with nonprinting attributes and non-worksheet sheet bindings are refused; no geometry inference.",
              "Unchanged local compressed records and member payloads are exact. Central-directory offsets necessarily change."]}
    return output,receipt

def safe_run_path(path, *, exists):
    root=RUN_DELIVERY.absolute()
    path=Path(os.path.abspath(path))
    require(path.is_relative_to(root),"path escapes this run delivery")
    require(root.resolve()==root,"run root has redirected resolution")
    for node in (path,*path.parents):
        if node.is_symlink():raise ValueError("HOLD: symlink run path")
        try:
            attributes=node.lstat()
        except FileNotFoundError:
            attributes=None
        if attributes is not None:
            require(not (getattr(attributes,"st_file_attributes",0) & 0x400),"reparse run path")
    require(path.resolve().is_relative_to(root),"resolved path escapes delivery")
    require(path.exists()==exists,"path existing/fresh expectation failed: "+str(path))
    if exists:require(path.is_file(),"input is not an ordinary file")
    return path

def unique_json(raw):
    def pairs(items):
        out={}
        for key,value in items:
            require(key not in out,"duplicate JSON member");out[key]=value
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda value:require(False,"non-finite JSON"))

def main(argv=None):
    parser=argparse.ArgumentParser(description="Connect pinned fresh Artifact XLSX PRINT_METADATA_ONLY to a separate fresh file")
    parser.add_argument("--plan",required=True,type=Path)
    parser.add_argument("--plan-sha256",required=True)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--receipt",required=True,type=Path)
    args=parser.parse_args(argv)
    require(Path(__file__).absolute()==RUN_DELIVERY/"connect_print_metadata_v2_62_r03.py","helper run path mismatch")
    plan_path=safe_run_path(args.plan,exists=True);plan_raw=plan_path.read_bytes()
    require(digest(plan_raw)==args.plan_sha256,"print plan SHA mismatch")
    plan=unique_json(plan_raw.decode("utf-8"))
    require(plan.get("ownedFreshArtifact") is True,"caller own-fresh-Artifact declaration required")
    source=safe_run_path(Path(plan["source"]["path"]),exists=True)
    author=safe_run_path(Path(plan["sourceAuthorReceipt"]["path"]),exists=True)
    author_raw=author.read_bytes();require(digest(author_raw)==plan["sourceAuthorReceipt"]["sha256"],"caller author receipt SHA mismatch")
    output=safe_run_path(args.output,exists=False);receipt_path=safe_run_path(args.receipt,exists=False)
    require(len({source,author,plan_path,output,receipt_path})==5,"paths must be distinct")
    require(source.suffix.lower()==output.suffix.lower()==".xlsx" and receipt_path.suffix.lower()==".json","explicit XLSX and receipt paths required")
    raw=source.read_bytes();require(digest(raw)==plan["source"]["sha256"],"source XLSX SHA mismatch")
    helper_raw=Path(__file__).read_bytes()
    connected,receipt=connect_bytes(raw,plan)
    require(source.read_bytes()==raw and author.read_bytes()==author_raw and plan_path.read_bytes()==plan_raw,"source binding changed during preparation")
    receipt.update(createdUtc=datetime.now(timezone.utc).isoformat(),sourcePath=str(source),outputPath=str(output),
                   helperPath=str(Path(__file__)),helperSha256=digest(helper_raw),
                   planPath=str(plan_path),planSha256=digest(plan_raw),
                   callerAuthorReceiptPath=str(author),callerAuthorReceiptSha256=digest(author_raw),
                   callerDeclaredOwnFreshArtifact=True,sourceUnchangedBeforeAfter=True)
    # Exclusive creation only. On receipt failure keep the fresh output as unapproved.
    with output.open("xb") as handle:handle.write(connected)
    require(source.read_bytes()==raw and author.read_bytes()==author_raw and plan_path.read_bytes()==plan_raw and Path(__file__).read_bytes()==helper_raw and output.read_bytes()==connected,"source/plan/helper/output binding changed after fresh output write")
    with receipt_path.open("x",encoding="utf-8") as handle:json.dump(receipt,handle,ensure_ascii=False,indent=2);handle.write("\n")
    print(json.dumps({"output":str(output),"sha256":digest(connected),"receipt":str(receipt_path),"receiptSha256":digest(receipt_path.read_bytes()),"scope":"PRINT_METADATA_ONLY"},ensure_ascii=False))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,expat.ExpatError,zipfile.BadZipFile) as error:
        print(str(error),file=sys.stderr);raise SystemExit(2)

