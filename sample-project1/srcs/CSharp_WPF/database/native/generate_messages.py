"""Generate this WPF project's Japanese catalog from its local specification."""
from pathlib import Path
import json,re
b=Path(__file__).resolve().parents[2]
spec=b.parent.parent/'spec'/b.name
s=(spec/'共通/05_チェック・メッセージ設計.md').read_text(encoding='utf-8')
rows=[]
for line in s.splitlines():
 m=re.match(r'\| ([EIW]-[A-Z]+-\d{3}) \| (.+) \|$',line)
 if m:rows.append((m.group(1),m.group(2)))
out=['using System.Globalization;','namespace StudentManagement.Core;','// Generated exclusively from this project spec/共通/05_チェック・メッセージ設計.md.','public static class NativeMessages','{','    private static readonly Dictionary<string,string> Catalog=new() {']
for k,v in rows:out.append('        ['+json.dumps(k,ensure_ascii=False)+']='+json.dumps(v,ensure_ascii=False)+',')
out+=['    };','    private static readonly Dictionary<string,string> Labels=new() {']
labels=dict(StudentNo='学籍番号',StudentName='氏名',StudentNameKana='氏名カナ',BirthDateInput='生年月日',GenderCode='性別',PostalCode='郵便番号',PrefectureCode='都道府県',AddressLine1='住所1',AddressLine2='住所2',PhoneNumber='本人電話',EmailAddress='本人メール',AdmissionDate='入学日',EnrollmentStatusCode='在籍区分',EnrollmentEndDate='卒業・退学日',ClassId='クラス',EmergencyContactName='緊急連絡先氏名',RelationshipCode='緊急連絡先続柄',EmergencyPhoneNumber='緊急連絡先電話',Remarks='備考',Reason='確認・変更理由',SchoolYear='年度',GradeCode='学年',ClassCode='クラスコード',ClassName='クラス名',CodeName='コード名称',CodeValue='コード値',CategoryId='コード分類',ValidFrom='開始日',ValidTo='終了日')
for k,v in labels.items():out.append('        ['+json.dumps(k)+']='+json.dumps(v,ensure_ascii=False)+',')
out+=['    };',r'''    public static string Resolve(string code,string field="",int? maximum=null,Guid? requestId=null)
    {
        if(StudentNormalizer.PropertyNames.TryGetValue(field,out var property))field=property;
        field=field switch {"school_year"=>"SchoolYear","grade_code"=>"GradeCode","class_code"=>"ClassCode","class_name"=>"ClassName","code_name"=>"CodeName","code_value"=>"CodeValue","category_id"=>"CategoryId","valid_from"=>"ValidFrom","valid_to"=>"ValidTo","reason"=>"Reason",_=>field};
        var label=Labels.GetValueOrDefault(field,"入力項目");
        maximum??=field switch {"StudentNo"=>15,"StudentName" or "EmergencyContactName"=>8,"StudentNameKana"=>18,"PostalCode"=>10,"AddressLine1" or "AddressLine2"=>45,"PhoneNumber" or "EmergencyPhoneNumber"=>20,"EmailAddress" or "Reason"=>60,"Remarks"=>120,"ClassCode"=>9,"ClassName"=>18,"CodeName"=>12,_=>10};
        var day=DateOnly.FromDateTime(DateTimeOffset.UtcNow.ToOffset(TimeSpan.FromHours(9)).DateTime).ToString("yyyy-MM-dd",CultureInfo.InvariantCulture);
        var template=Catalog.GetValueOrDefault(code,"処理を確認してください。");
        if(code=="E-STU-003" && field=="ClassCode")template=template.Replace("学籍番号","クラスコード").Replace("15文字","9文字");
        return template
            .Replace("{field}",label).Replace("{max}",maximum.Value.ToString(CultureInfo.InvariantCulture))
            .Replace("{correlationId}",requestId?.ToString()??"").Replace("{minDate}","1900-01-01").Replace("{maxDate}",day)
            .Replace("{minYear}","1900").Replace("{maxYear}","9998").Replace("{fromField}","開始日").Replace("{toField}","終了日")
            .Replace("{studentNo}","").Replace("{count}","0");
    }''','}']
(b/'Core/NativeMessages.cs').write_text('\n'.join(out)+'\n',encoding='utf-8')
print('Generated '+str(len(rows))+' local Japanese messages.')
