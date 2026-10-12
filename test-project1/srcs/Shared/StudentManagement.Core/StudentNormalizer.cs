using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace StudentManagement.Core;

public sealed class InputValidationException(IReadOnlyList<FieldError> errors) : Exception("ValidationFailed")
{
    public IReadOnlyList<FieldError> Errors { get; } = errors;
}
internal sealed record NormalizedStudent(Dictionary<string, object?> Values)
{
    public string Text(string key) => (string)Values[key]!;
    public DateOnly Date(string key) => (DateOnly)Values[key]!;
    public long? ClassId => (long?)Values["class_id"];
}

// COM-STU-005 N-01..12. Raw upper limits are checked before normalization.
public static class StudentNormalizer
{
    private static readonly Dictionary<string,string> Labels = new() {
        ["StudentNo"]="学籍番号",["StudentName"]="氏名",["StudentNameKana"]="氏名カナ",["BirthDateInput"]="生年月日",
        ["GenderCode"]="性別",["PostalCode"]="郵便番号",["PrefectureCode"]="都道府県",["AddressLine1"]="住所1",["AddressLine2"]="住所2",
        ["PhoneNumber"]="本人電話",["EmailAddress"]="本人メール",["AdmissionDate"]="入学日",["EnrollmentStatusCode"]="在籍区分",
        ["EnrollmentEndDate"]="卒業・退学日",["ClassId"]="クラス",["EmergencyContactName"]="緊急連絡先氏名",["RelationshipCode"]="緊急連絡先続柄",
        ["EmergencyPhoneNumber"]="緊急連絡先電話",["Remarks"]="備考",["Reason"]="確認・変更理由",["DeleteReason"]="削除理由",
        ["ClassCode"]="クラスコード",["ClassName"]="クラス名",["CodeName"]="コード名称",["GradeCode"]="学年",["Principal"]="認証主体"
    };
    internal static readonly Dictionary<string,string> PropertyNames = new() {
        ["student_no"]="StudentNo",["student_name"]="StudentName",["student_name_kana"]="StudentNameKana",["birth_date"]="BirthDateInput",
        ["gender_code"]="GenderCode",["postal_code"]="PostalCode",["prefecture_code"]="PrefectureCode",["address_line1"]="AddressLine1",["address_line2"]="AddressLine2",
        ["phone_number"]="PhoneNumber",["email_address"]="EmailAddress",["admission_date"]="AdmissionDate",["enrollment_status_code"]="EnrollmentStatusCode",
        ["enrollment_end_date"]="EnrollmentEndDate",["class_id"]="ClassId",["emergency_contact_name"]="EmergencyContactName",["relationship_code"]="RelationshipCode",
        ["emergency_phone_number"]="EmergencyPhoneNumber",["remarks"]="Remarks"
    };
    private static string Label(string field) => Labels.GetValueOrDefault(field,"入力項目");
    public static int ScalarCount(string text)
    {
        var count = 0;
        for (var i = 0; i < text.Length; i++, count++) {
            if (char.IsHighSurrogate(text[i])) {
                if (++i >= text.Length || !char.IsLowSurrogate(text[i])) throw new ArgumentException("不正なUnicodeです。");
            } else if (char.IsLowSurrogate(text[i])) throw new ArgumentException("不正なUnicodeです。");
        }
        return count;
    }
    public static string? Text(string? raw, int rawMax, int savedMax, string field, bool required = false, bool multiline = false)
    {
        raw ??= "";
        if (ScalarCount(raw) > rawMax) Fail(field, "E-STU-002", $"{Label(field)}は{rawMax}文字以内で入力してください。");
        var value = multiline ? raw.Replace("\r\n", "\n").Replace('\r', '\n') : raw;
        if (value.EnumerateRunes().Any(rune => Rune.GetUnicodeCategory(rune) == UnicodeCategory.Control && !(multiline && rune.Value == 10)))
            Fail(field, "E-STU-002", $"{Label(field)}に使用できない制御文字があります。");
        value = value.Trim();
        if (value.Length == 0) { if (required) Fail(field, "E-STU-001", $"{Label(field)}を入力してください。"); return null; }
        if (ScalarCount(value) > savedMax) Fail(field, "E-STU-002", $"{Label(field)}は{savedMax}文字以内で入力してください。");
        return value;
    }
    public static string Identifier(string? raw, int max, string field)
    {
        var value = Text(raw, max, max, field, true)!.Normalize(NormalizationForm.FormKC).ToUpperInvariant();
        if (ScalarCount(value) > max || !Regex.IsMatch(value, "^[A-Z0-9][A-Z0-9-]*$", RegexOptions.CultureInvariant))
            Fail(field, "E-STU-003", $"{Label(field)}は英数字・ハイフンで{max}文字以内にしてください。");
        return value;
    }
    public static string NameKey(string name)
    {
        var key = string.Concat(name.Normalize(NormalizationForm.FormKC).ToUpperInvariant().EnumerateRunes().Where(rune => !Rune.IsWhiteSpace(rune)));
        if (ScalarCount(key) > 160) Fail("StudentName", "E-STU-002", "氏名照合値が上限を超えています。");
        return key;
    }
    public static string Kana(string? raw, bool required = true)
    {
        var value = Text(raw, 36, 36, "StudentNameKana", required)?.Normalize(NormalizationForm.FormKC) ?? "";
        var output = new StringBuilder(); bool space = false;
        foreach (var rune in value.EnumerateRunes()) {
            if (Rune.IsWhiteSpace(rune)) { space = output.Length > 0; continue; }
            if (space) { output.Append(' '); space = false; }
            var c = rune.Value is >= 0x3041 and <= 0x3096 || rune.Value is 0x309D or 0x309E ? rune.Value + 0x60 : rune.Value;
            if (!(c is >= 0x30A1 and <= 0x30FA || c is 0x30FC or 0x30FB or 0x30FD or 0x30FE)) Fail("StudentNameKana", "E-STU-004", "氏名カナはカタカナで入力してください。");
            output.Append(new Rune(c).ToString());
        }
        var result = output.ToString();
        if (ScalarCount(result) > 18) Fail("StudentNameKana", "E-STU-002", "氏名カナは18文字以内です。");
        return result;
    }
    public static string? Phone(string? raw, string field)
    {
        var text = Text(raw, 20, 20, field)?.Normalize(NormalizationForm.FormKC);
        if (text is null) return null;
        var value = string.Concat(text.EnumerateRunes().Where(rune => !Rune.IsWhiteSpace(rune) && rune.Value is not ('-' or 0x2010 or 0x2011 or 0x2212 or '(' or ')')));
        if (!Regex.IsMatch(value, "^(0[0-9]{9,10}|\\+[1-9][0-9]{6,14})$", RegexOptions.CultureInvariant)) Fail(field, "E-STU-016", "電話番号の形式を確認してください。");
        return value;
    }
    public static string Postal(string? raw)
    {
        var text = Text(raw, 10, 10, "PostalCode", true)!.Normalize(NormalizationForm.FormKC);
        var value = string.Concat(text.EnumerateRunes().Where(rune => !Rune.IsWhiteSpace(rune) && rune.Value is not ('-' or 0x2010 or 0x2011 or 0x2212)));
        if (!Regex.IsMatch(value, "^[0-9]{7}$", RegexOptions.CultureInvariant)) Fail("PostalCode", "E-STU-015", "郵便番号は7桁で入力してください。");
        return value;
    }
    public static string? Email(string? raw)
    {
        var value = Text(raw, 60, 60, "EmailAddress");
        if (value is null) return null;
        var parts = value.Split('@');
        if (parts.Length != 2 || parts[0].Length == 0 || parts[0].Length > 64 || parts[0].StartsWith('.') || parts[0].EndsWith('.') || parts[0].Contains("..") ||
            !Regex.IsMatch(parts[0], "^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+$", RegexOptions.CultureInvariant)) Fail("EmailAddress", "E-STU-017", "メールアドレスの形式を確認してください。");
        var labels = parts[1].Split('.');
        if (labels.Length < 2 || labels.Any(label => label.Length is < 1 or > 63 || !Regex.IsMatch(label, "^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$", RegexOptions.CultureInvariant))) Fail("EmailAddress", "E-STU-017", "メールアドレスの形式を確認してください。");
        return parts[0] + "@" + parts[1].ToLowerInvariant();
    }
    public static string? Code(string? raw, int width, string field, bool required = true)
    {
        var text = Text(raw, width, width, field, required)?.Normalize(NormalizationForm.FormKC);
        if (text is not null && (text.Length != width || text.Any(c => c < '0' || c > '9'))) Fail(field, "E-STU-009", "コードを選択し直してください。");
        return text;
    }
    internal static NormalizedStudent Normalize(StudentDraft raw, DateOnly businessDay)
    {
        var values = new Dictionary<string, object?>();
        var errors = new List<FieldError>();
        void Set(string column, Func<object?> get) { try { values[column] = get(); } catch (InputValidationException e) { errors.AddRange(e.Errors); } catch (ArgumentException e) { errors.Add(ArgumentError(PropertyNames[column],e)); } }
        Set("student_no", () => Identifier(raw.StudentNo, 15, "StudentNo"));
        Set("student_name", () => Text(raw.StudentName, 8, 8, "StudentName", true));
        Set("student_name_kana", () => Kana(raw.StudentNameKana));
        Set("birth_date", () => JapaneseDateService.Parse(raw.BirthDateInput, businessDay));
        Set("gender_code", () => Code(raw.GenderCode, 1, "GenderCode"));
        Set("postal_code", () => Postal(raw.PostalCode));
        Set("prefecture_code", () => Code(raw.PrefectureCode, 2, "PrefectureCode"));
        Set("address_line1", () => Text(raw.AddressLine1, 45, 45, "AddressLine1", true));
        Set("address_line2", () => Text(raw.AddressLine2, 45, 45, "AddressLine2"));
        Set("phone_number", () => Phone(raw.PhoneNumber, "PhoneNumber"));
        Set("email_address", () => Email(raw.EmailAddress));
        Set("admission_date", () => JapaneseDateService.ParseIso(raw.AdmissionDate, businessDay));
        Set("enrollment_status_code", () => Code(raw.EnrollmentStatusCode, 2, "EnrollmentStatusCode"));
        Set("enrollment_end_date", () => string.IsNullOrEmpty(raw.EnrollmentEndDate) ? null : JapaneseDateService.ParseIso(raw.EnrollmentEndDate, businessDay));
        Set("class_id", () => raw.ClassId is <= 0 ? throw new ArgumentException("E-STU-010: クラスIDが不正です。") : raw.ClassId);
        Set("emergency_contact_name", () => Text(raw.EmergencyContactName, 8, 8, "EmergencyContactName"));
        Set("relationship_code", () => Code(raw.RelationshipCode, 2, "RelationshipCode", false));
        Set("emergency_phone_number", () => Phone(raw.EmergencyPhoneNumber, "EmergencyPhoneNumber"));
        Set("remarks", () => Text(raw.Remarks, 120, 120, "Remarks", multiline: true));
        if (errors.Count > 0) throw new InputValidationException(errors);
        values["name_key"] = NameKey((string)values["student_name"]!);
        values["kana_key"] = ((string)values["student_name_kana"]!).Replace(" ", "");
        var birth = (DateOnly)values["birth_date"]!; var admission = (DateOnly)values["admission_date"]!;
        var end = (DateOnly?)values["enrollment_end_date"];
        var status = (string)values["enrollment_status_code"]!;
        if (birth > admission) errors.Add(new("AdmissionDate", "E-STU-007", "生年月日≦入学日となるよう入力してください。"));
        if (status is not ("01" or "02" or "03" or "04")) errors.Add(new("EnrollmentStatusCode", "E-STU-009", "在籍区分が不正です。"));
        if ((status is "01" or "02") ? end is not null : end is null || end < admission) errors.Add(new("EnrollmentEndDate", "E-STU-008", "在籍区分に対応する終了日を設定してください。"));
        if (status is "01" or "02" && raw.ClassId is null) errors.Add(new("ClassId", "E-STU-012", "在学・休学はクラス必須です。"));
        if (values["phone_number"] is null && values["email_address"] is null && values["emergency_phone_number"] is null) errors.Add(new("PhoneNumber", "E-STU-018", "連絡先を1つ以上入力してください。"));
        var emergency = new[] { values["emergency_contact_name"], values["relationship_code"], values["emergency_phone_number"] }.Count(value => value is not null);
        if (emergency is not (0 or 3)) errors.Add(new("EmergencyContactName", "E-STU-019", "緊急連絡先は3項目すべて入力してください。"));
        if (errors.Count > 0) throw new InputValidationException(errors);
        return new(values);
    }
    public static string EscapeLike(string input) => input.Replace("!", "!!").Replace("%", "!%").Replace("_", "!_").Replace("[", "![");
    internal static FieldError ArgumentError(string field,ArgumentException error)
    {
        var code=error.Message.Split(':')[0];
        return Regex.IsMatch(code,"^E-(?:STU|DATE|COM|SRC|MST)-[0-9]{3}$",RegexOptions.CultureInvariant)
            ? new(field,code,error.Message) : new(field,"E-STU-002",$"{Label(field)}の文字を確認してください。");
    }
    private static void Fail(string field, string code, string message) => throw new InputValidationException([new(field, code, message)]);
}
