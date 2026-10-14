"""Synthetic-only metadata connector regression. Never reads actual input/XLSX."""
import base64
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
import zipfile
from datetime import datetime,timezone

HELPER=Path(r"D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery\connect_print_metadata_v2_62_r01.py")
EVIDENCE=Path(__file__).parent/"print-metadata-synthetic-r02"
module_name="fresh_print_metadata_connector"
spec=importlib.util.spec_from_file_location(module_name,HELPER)
m=importlib.util.module_from_spec(spec);sys.modules[module_name]=m;spec.loader.exec_module(m)
S=m.S;R=m.R;P=m.P
head=b'<?xml version="1.0" encoding="UTF-8"?>\n'
def make_fixture(prefixed=False, empty_pr=False, existing_dn=True):
    q="s:" if prefixed else ""
    ns=f'xmlns:s="{S}"' if prefixed else f'xmlns="{S}"'
    sheet=lambda i: head+(f'<{q}worksheet {ns} xmlns:r="{R}">\n'
       + (f'<{q}sheetPr codeName="KeepCode" />\n' if empty_pr else f'<{q}sheetPr codeName="KeepCode"><{q}outlinePr summaryRight="0"/><!--keep--><{q}pageSetUpPr autoPageBreaks="0" fitToPage="0"/></{q}sheetPr>\n')
       + f'<{q}dimension ref="A1:BJ36"/>\n<{q}sheetViews><{q}sheetView workbookViewId="0"/></{q}sheetViews>\n'
       + f'<{q}cols><{q}col min="1" max="62" width="3" customWidth="1"/></{q}cols>\n'
       + f'<{q}sheetData><{q}row r="1"><{q}c r="A1" s="9" t="inlineStr"><{q}is><{q}t xml:space="preserve">01 =SUM(1) 日付 1900-01-01</{q}t></{q}is></{q}c></{q}row></{q}sheetData>\n'
       + f'<{q}mergeCells count="1"><{q}mergeCell ref="A2:B2"/></{q}mergeCells>\n'
       + f'<{q}pageMargins left="1" right="1" top="1" bottom="1" header="1" footer="1"/>\n'
       + f'<{q}pageSetup paperSize="8" orientation="portrait" fitToWidth="0" fitToHeight="9" useFirstPageNumber="1"/>\n'
       + f'<{q}headerFooter><{q}oddFooter>Keep this footer</{q}oddFooter></{q}headerFooter>\n'
       + f'<{q}drawing r:id="draw{i}"/>\n</{q}worksheet>').encode()
    names=["表紙","概要","一覧","表定義","未選択"]
    sheets="".join(f'<{q}sheet name="{name}" sheetId="{i+1}" r:id="rId{i+1}"/>' for i,name in enumerate(names))
    other=f'<{q}definedName name="Custom_KEEP" hidden="1">\'概要\'!$A$1</{q}definedName>'
    unselected=f'<{q}definedName name="_xlnm.Print_Area" localSheetId="4">\'未選択\'!$A$9:$C$10</{q}definedName>'
    selected=f'<{q}definedName name="_xlnm.Print_Area" localSheetId="0">\'表紙\'!$A$1:$B$1</{q}definedName><{q}definedName name="_xlnm.Print_Titles" localSheetId="0">$1:$9</{q}definedName>'
    dn=f'<{q}definedNames>\n {other}\n{unselected}\n{selected}\n</{q}definedNames>' if existing_dn else ""
    book=head+(f'<{q}workbook {ns} xmlns:r="{R}">\n<{q}bookViews><{q}workbookView/></{q}bookViews>\n<{q}sheets>{sheets}</{q}sheets>\n{dn}\n<{q}calcPr calcId="777"/>\n</{q}workbook>').encode()
    rels=head+(f'<Relationships xmlns="{P}">'+''.join(f'<Relationship Id="rId{i+1}" Type="{R}/worksheet" Target="worksheets/sheet{i+1}.xml"/>' for i in range(5))+'</Relationships>').encode()
    payload={"[Content_Types].xml":head+b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
      "xl/workbook.xml":book,"xl/_rels/workbook.xml.rels":rels,"xl/styles.xml":head+f'<styleSheet xmlns="{S}"/>'.encode(),
      "xl/media/unchanged.bin":b"FAKE-SYNTHETIC-MEDIA\x00\x01\xff","docProps/core.xml":head+b'<core xmlns="urn:synthetic">unchanged</core>'}
    for i in range(1,6):payload[f"xl/worksheets/sheet{i}.xml"]=sheet(i)
    return payload,other.encode(),unselected.encode()

def packed(payload,compression=zipfile.ZIP_DEFLATED):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w",compression=compression) as z:
        z.comment=b"synthetic unchanged archive comment"
        for name,data in payload.items():z.writestr(name,data)
    return buf.getvalue()

plan={"schema":m.SCHEMA,"scope":"PRINT_METADATA_ONLY","sheets":[
 {"ordinal":0,"name":"表紙","kind":"cover","lastRow":36},
 {"ordinal":1,"name":"概要","kind":"normal","lastRow":36},
 {"ordinal":2,"name":"一覧","kind":"list","columns":10,"headerRow":1,"lastRow":36},
 {"ordinal":3,"name":"表定義","kind":"table","columns":9,"headerRow":7,"lastRow":36}]}
results=[]
def positive(name,payload,other=None,unselected=None,compression=zipfile.ZIP_DEFLATED):
    raw=packed(payload,compression);out,receipt=m.connect_bytes(raw,copy.deepcopy(plan))
    _,after,_,_=m.zip_index(out)
    assert receipt["nonSelectedLocalCompressedRecordsExact"]
    assert receipt["rawXmlInverseRestorationExact"]
    assert after["xl/worksheets/sheet5.xml"]==payload["xl/worksheets/sheet5.xml"]
    if other:assert other in after["xl/workbook.xml"]
    if unselected:assert unselected in after["xl/workbook.xml"]
    root=m.parse_xml(after["xl/workbook.xml"])
    actual={}
    for container in m.children(root,S,"definedNames"):
      for n in container.children:
        if n.attrs.get("localSheetId") is not None:
          text=after["xl/workbook.xml"][n.open_end:n.end_start].decode()
          actual[(n.attrs.get("localSheetId"),n.attrs.get("name"))]=text
    assert ("0","_xlnm.Print_Titles") not in actual
    assert actual[("1","_xlnm.Print_Titles")]=="'概要'!$1:$1"
    assert actual[("2","_xlnm.Print_Titles")]=="'一覧'!$1:$1"
    assert actual[("3","_xlnm.Print_Titles")]=="'表定義'!$7:$7"
    assert "$O$6:$AU$36" in actual[("0","_xlnm.Print_Area")]
    assert "$A$1:$BJ$36" in actual[("1","_xlnm.Print_Area")]
    assert "$A$1:$J$36" in actual[("2","_xlnm.Print_Area")]
    assert "$A$1:$I$36" in actual[("3","_xlnm.Print_Area")]
    # A second identical connection is byte-idempotent, including original ZIP records.
    again,r2=m.connect_bytes(out,copy.deepcopy(plan));assert again==out
    for member,e in receipt["xmlEvidence"].items():
      reverse=after[member]
      for span in reversed(e["allowedSplices"]):
        a,b=span["outputStart"],span["outputEnd"]
        assert reverse[a:b]==base64.b64decode(span["afterBase64"])
        reverse=reverse[:a]+base64.b64decode(span["beforeBase64"])+reverse[b:]
      assert reverse==payload[member]
    results.append({"name":name,"result":"PASS","inputSha256":m.digest(raw),"outputSha256":m.digest(out),
                    "metadataIdempotent":True,"nonselectedSheetRawBytesExact":True,
                    "allNonprintLocalRecordsExact":True,"xmlInverseExact":True})
    if name=="positive_all4patterns":
      (EVIDENCE/"synthetic-source.zip").write_bytes(raw)
      (EVIDENCE/"synthetic-connected.zip").write_bytes(out)
      (EVIDENCE/"synthetic-connection-receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def negative(name,payload=None,changed_plan=None,action=None,raw=None):
    try:
        if action:action()
        else:m.connect_bytes(raw if raw is not None else packed(payload),changed_plan or copy.deepcopy(plan))
    except (ValueError,m.expat.ExpatError,zipfile.BadZipFile) as e:
        results.append({"name":name,"result":"PASS_REJECTED","reason":str(e)});return
    raise AssertionError("Unexpected acceptance: "+name)

assert not EVIDENCE.exists()
EVIDENCE.mkdir()
payload,other,unselected=make_fixture()
positive("positive_all4patterns",payload,other,unselected)
p,o,u=make_fixture(prefixed=True);positive("positive_public_parser_namespace_prefix",p,o,u)
p,o,u=make_fixture(empty_pr=True);negative("negative_selfclosing_sheetPr_nonprinting_attrs",p)
p={k:v.replace(b'<sheetPr codeName="KeepCode" />',b'<sheetPr/>') for k,v in p.items()};positive("positive_bare_selfclosing_sheetPr",p,o,u)
p,o,u=make_fixture(existing_dn=False);positive("positive_absent_definedNames",p)
positive("positive_stored_zip",payload,other,unselected,zipfile.ZIP_STORED)
p=copy.deepcopy(payload)
p["xl/_rels/workbook.xml.rels"]=p["xl/_rels/workbook.xml.rels"].replace(b'Target="worksheets/',b'Target="/xl/worksheets/')
positive("positive_absolute_pack_uri_target",p,other,unselected)
p=copy.deepcopy(payload)
for i in range(1,5):
  key=f"xl/worksheets/sheet{i}.xml"
  root=m.parse_xml(p[key])
  removals=[(n.start,n.end,b"",n.name,0) for n in root.children if m.local(n.name) in {"sheetPr","pageMargins","pageSetup"}]
  p[key],_=m.splice(p[key],removals)
positive("positive_absent_all_print_nodes",p,other,unselected)
p=copy.deepcopy(payload);p["xl/workbook.xml"]=p["xl/workbook.xml"].replace(b"<definedNames>",b"<definedNames>").replace(other,b'<definedName name="Custom_KEEP">literal &lt;pageSetup/&gt; and &amp; preserved</definedName>')
positive("positive_lexical_tag_like_defined_name_text",p,None,unselected)
for name,insert in [("negative_unknown_PI",b"<?custom not-allowed?>"),
                    ("negative_DTD",b'<!DOCTYPE workbook [<!ENTITY forbidden "x">]>')]:
 p=copy.deepcopy(payload);p["xl/workbook.xml"]=head+insert+p["xl/workbook.xml"][len(head):]
 negative(name,p)
p=copy.deepcopy(payload);p["xl/_rels/workbook.xml.rels"]=p["xl/_rels/workbook.xml.rels"].replace(b'Target="worksheets/sheet1.xml"',b'Target="https://example.invalid/file.xlsx" TargetMode="External"')
negative("negative_external_relationship",p)
p=copy.deepcopy(payload);p["xl/externalLinks/externalLink1.xml"]=head+b"<external/>";negative("negative_externalLink_member",p)
p=copy.deepcopy(payload);p["xl/vbaProject.bin"]=b"synthetic";negative("negative_vba_member",p)
p=copy.deepcopy(payload);p["[Content_Types].xml"]=p["[Content_Types].xml"].replace(b"/>",b'><Override ContentType="application/vnd.ms-excel.sheet.macroEnabled.main+xml"/></Types>')
negative("negative_macro_content_type",p)
p=copy.deepcopy(payload);p["../escape.xml"]=head+b"<escape/>";negative("negative_ZIP_path_escape",p)
p=copy.deepcopy(payload);p["xl/_rels/workbook.xml.rels"]=p["xl/_rels/workbook.xml.rels"].replace(b'Target="worksheets/sheet1.xml"',b'Target="../escape.xml"');negative("negative_relationship_descent",p)
p=copy.deepcopy(payload);p["xl/worksheets/sheet1.xml"]=p["xl/worksheets/sheet1.xml"].replace(b"<pageSetup",b"<unknownGeometry");negative("negative_unknown_source_element",p)
p=copy.deepcopy(payload);p["xl/worksheets/sheet1.xml"]=p["xl/worksheets/sheet1.xml"].replace(b"<sheetData>",b"<pageMargins/><sheetData>");negative("negative_bad_order_or_duplicate",p)
p=copy.deepcopy(payload);p["xl/workbook.xml"]=p["xl/workbook.xml"].replace(other,b'<definedName name="_xlnm.Auto_Open">RunMacro()</definedName>');negative("negative_macro_defined_name",p)
bad=copy.deepcopy(plan);bad["sheets"][0]["name"]="Wrong";negative("negative_exact_sheet_identity",payload,bad)
bad=copy.deepcopy(plan);bad["sheets"][2]["headerRow"]=2;negative("negative_LIST_header_not_1",payload,bad)
bad=copy.deepcopy(plan);bad["sheets"][3]["headerRow"]=0;negative("negative_TABLE_missing_real_header",payload,bad)
bad=copy.deepcopy(plan);bad["sheets"][3]["columns"]=8;negative("negative_TABLE_not_9",payload,bad)
bad=copy.deepcopy(plan);bad["sheets"][0]["lastRow"]=37;negative("negative_cover_bounds",payload,bad)
bad=copy.deepcopy(plan);bad["sheets"].append(copy.deepcopy(bad["sheets"][0]));negative("negative_duplicate_selection",payload,bad)
negative("negative_source_path_escape",action=lambda:m.safe_run_path(m.RUN_DELIVERY/".."/"outside.xlsx",exists=False))
negative("negative_existing_output_rejected",action=lambda:m.safe_run_path(HELPER,exists=False))
raw=packed(payload)
negative("negative_archive_trailing_bytes",raw=raw+b"BAD")
raw=bytearray(raw);off=raw.find(b"PK\x03\x04");flags=struct.unpack("<H",raw[off+6:off+8])[0];raw[off+6:off+8]=struct.pack("<H",flags|8)
negative("negative_local_data_descriptor_flag",raw=bytes(raw))
p=copy.deepcopy(payload);p["xl/_rels/workbook.xml.rels"]=p["xl/_rels/workbook.xml.rels"].replace(b'Target="worksheets/sheet5.xml"',b'Target="worksheets/sheet1.xml"');negative("negative_selected_nonselected_member_alias",p)
p=copy.deepcopy(payload);p["xl/workbook.xml"]=p["xl/workbook.xml"].replace('name="未選択"'.encode(),'name="概要"'.encode());negative("negative_duplicate_actual_sheet_name",p)
p=copy.deepcopy(payload);p["xl/worksheets/sheet1.xml"]=p["xl/worksheets/sheet1.xml"].replace(b'<outlinePr summaryRight="0"/><!--keep--><pageSetUpPr autoPageBreaks="0" fitToPage="0"/>',b'<pageSetUpPr fitToPage="0"/><outlinePr summaryRight="0"/>');negative("negative_sheetPr_source_order",p)
result={"schema":"synthetic-print-metadata-validation/1","createdUtc":datetime.now(timezone.utc).isoformat(),
 "helperPath":str(HELPER),"helperSha256":m.digest(HELPER.read_bytes()),"tests":results,
 "testCount":len(results),"allPassed":True,"realWorkbookApplied":False,"artifactAuthorExecuted":False,
 "providerExecuted":False,"markerExecuted":False,"applicationExecuted":False,
 "oldFilesChanged":False,"scope":"SYNTHETIC_PRINT_METADATA_ONLY"}
out=EVIDENCE/"result.json";out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"result":str(out),"sha256":m.digest(out.read_bytes()),"helperSha256":result["helperSha256"],"testCount":len(results),"allPassed":True},ensure_ascii=False))

