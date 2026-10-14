"""Adapt the prior generic TABLE audit to a fresh explicitly selected single TABLE."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
 original=HERE/'audit_assisted_tables_r03.py';text=original.read_text(encoding='utf8')
 changes={
 "ROOT/'assisted-tables-r03-mechanical-qa.json'":"ROOT/'assisted-operation-log-r01-mechanical-qa.json'",
 "ROOT/'binding-assisted-tables-r02.json'":"ROOT/'binding-assisted-index-oplog-r01.json'",
 "ROOT/'model-assisted-tables-r03.json'":"ROOT/'model-assisted-index-oplog-r01.json'",
 "ROOT/'xlsx-assisted-tables-r03/delivery-manifest.json'":"ROOT/'xlsx-assisted-index-oplog-r01/delivery-manifest.json'",
 "ROOT/'pdf-assisted-tables-r04/delivery-manifest.json'":"ROOT/'pdf-assisted-index-oplog-r01/delivery-manifest.json'",
 "ROOT/'html-assisted-tables-r02b/qa.json'":"ROOT/'html-assisted-index-oplog-r01/qa.json'",
 "'rootReportedRevision':'r12'":"'rootReportedRevision':'frozen-assisted06-r14'",
 "['recover_assisted_tables_r02.py','delivery_model.py','build_xlsx.mjs','verify_xlsx.py','export_pdf.py','audit_assisted_tables.py']":"['prepare_assisted_index_oplog_r01.py','delivery_model_tables_r03.py','build_xlsx.mjs','verify_xlsx.py','export_pdf_tables_r02.py','audit_assisted_operation_log_r01.py']",
 }
 for old,new in changes.items():
  assert old in text,old;text=text.replace(old,new)
 marker="    for entry,document,hdoc in zip(entries,model['documents'],html_qa['documents'],strict=True):\n"
 assert text.count(marker)==1
 text=text.replace(marker,marker+"        if entry['documentId']!='CSHARP_ASPNET-BAS-STU-03-T_OPERATION_LOG':continue\n")
 marker="    load_bound(binding)\n    report=";assert text.count(marker)==1
 text=text.replace(marker,"    assert len(outputs)==1\n    load_bound(binding)\n    report=")
 out=HERE/'audit_assisted_operation_log_r01.py'
 with out.open('x',encoding='utf8') as f:f.write(text)
 print(out)
if __name__=='__main__':main()
