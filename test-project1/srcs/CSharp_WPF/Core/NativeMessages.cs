using System.Globalization;
namespace StudentManagement.Core;
// Generated exclusively from this project spec/共通/05_チェック・メッセージ設計.md.
public static class NativeMessages
{
    private static readonly Dictionary<string,string> Catalog=new() {
        ["I-SRC-001"]="該当する学生がありません。",
        ["I-STU-001"]="学生を登録しました。（学籍番号：{studentNo}）",
        ["I-STU-002"]="学生情報を更新しました。",
        ["I-STU-003"]="学生情報を論理削除しました。",
        ["I-STU-004"]="変更内容がありません。",
        ["W-SRC-001"]="検索結果が10,000件を超えています。検索条件を追加してください。",
        ["W-SRC-002"]="検索条件の保持期限が切れました。条件を再指定してください。",
        ["W-STU-101"]="同じ生年月日で氏名または氏名カナが一致する学生が{count}件あります。別人であることを確認してください。",
        ["W-STU-102"]="入力内容または重複候補が変わりました。もう一度確認してください。",
        ["W-STU-103"]="変更内容を破棄して戻りますか。",
        ["W-STU-104"]="入力内容を取り消しますか。",
        ["W-STU-105"]="この学生を論理削除します。削除後は通常検索できません。よろしいですか。",
        ["W-STU-106"]="所属クラスが利用期間外です。住所等は変更できますが、クラスの見直しが必要です。",
        ["W-STU-107"]="選択条件が変わったためクラスの選択を解除しました。",
        ["W-STU-108"]="登録可能なクラスがありません。クラスマスタを確認してください。",
        ["W-STU-109"]="最新情報を再読み込みすると入力中の変更は破棄されます。続行しますか。",
        ["W-MST-001"]="同じ年度・学年に同名のクラスがあります。クラスコードと名称を確認してください。",
        ["E-STU-001"]="{field}を入力してください。",
        ["E-STU-002"]="{field}は{max}文字以内の使用可能な文字で入力してください。",
        ["E-STU-003"]="学籍番号は半角英数字・ハイフンで15文字以内にしてください。先頭は英数字です。",
        ["E-STU-004"]="氏名カナはカタカナで入力してください。中点・長音・空白は使用できます。",
        ["E-STU-005"]="{field}に正しい日付を入力してください。",
        ["E-STU-006"]="{fromField}は{toField}以前の日付にしてください。",
        ["E-STU-007"]="生年月日・入学日は本日以前とし、生年月日≦入学日となるよう入力してください。",
        ["E-STU-008"]="在籍区分に対応する卒業・退学日を設定してください。",
        ["E-STU-009"]="{field}のコードが存在しません。選択し直してください。",
        ["E-STU-010"]="指定したクラスが存在しません。選択し直してください。",
        ["E-STU-011"]="{field}は現在使用できないコードです。選択し直してください。",
        ["E-STU-012"]="在学・休学の学生はクラスを選択してください。",
        ["E-STU-013"]="このクラスには新たに所属できません。利用可否と利用期間を確認してください。",
        ["E-STU-014"]="年度・学年と選択したクラスが一致していません。",
        ["E-STU-015"]="郵便番号は7桁の数字で入力してください。",
        ["E-STU-016"]="{field}の形式が正しくありません。国内10～11桁または国番号付きの番号を入力してください。",
        ["E-STU-017"]="メールアドレスの形式が正しくありません。",
        ["E-STU-018"]="本人電話、本人メール、緊急連絡先電話のいずれかを入力してください。",
        ["E-STU-019"]="緊急連絡先は氏名・続柄・電話番号をすべて入力してください。",
        ["E-STU-020"]="削除理由を60文字以内で入力してください。",
        ["E-STU-101"]="この学籍番号は使用済みです。入力を確認してください。直前の送信結果が不明な場合は検索で登録状況を確認してください。",
        ["E-STU-102"]="クラスの定員を超えるため保存できません。別のクラスを選択してください。",
        ["E-STU-103"]="対象の学生が見つからないか、既に削除されています。",
        ["E-STU-104"]="登録済みの学籍番号は変更できません。",
        ["E-STU-105"]="他の操作で更新されています。入力内容を控え、最新情報を再読み込みしてください。",
        ["E-STU-106"]="卒業・退学からの在籍区分変更には管理者権限と変更理由が必要です。",
        ["E-STU-107"]="確認・変更理由を60文字以内で入力してください。",
        ["E-SRC-001"]="未所属のみを検索する場合、年度・学年・クラスは指定できません。",
        ["E-SRC-002"]="検索条件または表示指定が正しくありません。",
        ["E-MST-001"]="マスタの初期設定が不足しています。管理者に連絡してください。",
        ["E-MST-002"]="このコードまたはクラスコードは既に登録されています。",
        ["E-MST-003"]="参照中または保護対象のため、このマスタ変更はできません。",
        ["E-MST-004"]="定員または利用期間が現在の所属状況と整合しません。",
        ["E-COM-001"]="ログインの有効期限が切れました。再度ログインしてください。",
        ["E-COM-002"]="この操作を行う権限がありません。",
        ["E-COM-003"]="画面情報が無効です。画面を開き直してください。",
        ["E-COM-004"]="処理を完了できませんでした。受付番号：{correlationId}",
        ["E-STU-108"]="最終所属クラスの利用期間が学生の在籍期間と重なっていません。クラスまたは在籍日付を確認してください。",
        ["E-DATE-001"]="生年月日の元号・年・月・日を確認してください。",
        ["E-DATE-002"]="{field}は{minDate}から{maxDate}までの日付で入力してください。",
        ["E-DATE-003"]="{field}は西暦4桁の{minYear}年から{maxYear}年で指定してください。",
    };
    private static readonly Dictionary<string,string> Labels=new() {
        ["StudentNo"]="学籍番号",
        ["StudentName"]="氏名",
        ["StudentNameKana"]="氏名カナ",
        ["BirthDateInput"]="生年月日",
        ["GenderCode"]="性別",
        ["PostalCode"]="郵便番号",
        ["PrefectureCode"]="都道府県",
        ["AddressLine1"]="住所1",
        ["AddressLine2"]="住所2",
        ["PhoneNumber"]="本人電話",
        ["EmailAddress"]="本人メール",
        ["AdmissionDate"]="入学日",
        ["EnrollmentStatusCode"]="在籍区分",
        ["EnrollmentEndDate"]="卒業・退学日",
        ["ClassId"]="クラス",
        ["EmergencyContactName"]="緊急連絡先氏名",
        ["RelationshipCode"]="緊急連絡先続柄",
        ["EmergencyPhoneNumber"]="緊急連絡先電話",
        ["Remarks"]="備考",
        ["Reason"]="確認・変更理由",
        ["SchoolYear"]="年度",
        ["GradeCode"]="学年",
        ["ClassCode"]="クラスコード",
        ["ClassName"]="クラス名",
        ["CodeName"]="コード名称",
        ["CodeValue"]="コード値",
        ["CategoryId"]="コード分類",
        ["ValidFrom"]="開始日",
        ["ValidTo"]="終了日",
    };
    public static string Resolve(string code,string field="",int? maximum=null,Guid? requestId=null)
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
    }
}
