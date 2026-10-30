using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace CareerManagement.Application;

public static partial class Validation
{
    // sample-project2 DEMO credential policy confirmed by the user on 2026-10-29.
    public const int MinimumPasswordScalars = 3;
    public const int MaximumPasswordScalars = 128;
    [GeneratedRegex("^[0-9]{6}$", RegexOptions.CultureInvariant)] private static partial Regex EmployeeNoPattern();
    [GeneratedRegex("^[0-9]{2}$", RegexOptions.CultureInvariant)] private static partial Regex CodePattern();
    [GeneratedRegex("^[A-Za-z0-9]{1,20}$", RegexOptions.CultureInvariant)] private static partial Regex LoginPattern();
    [GeneratedRegex("^[0-9]{1,3}$", RegexOptions.CultureInvariant)] private static partial Regex IntegerPattern();
    [GeneratedRegex("^[ァ-ヶー・ 　]+$", RegexOptions.CultureInvariant)] private static partial Regex KanaPattern();

    public static int ScalarLength(string value)
    {
        var count = 0;
        for (var i = 0; i < value.Length; i++, count++)
        {
            if (char.IsHighSurrogate(value[i]))
            {
                if (++i >= value.Length || !char.IsLowSurrogate(value[i])) throw BusinessException.Error(5);
            }
            else if (char.IsLowSurrogate(value[i])) throw BusinessException.Error(5);
        }
        return count;
    }
    public static string? Text(string? raw, int max, bool required, string item, string label, int? row = null, bool kana = false)
    {
        if (raw is null && required) throw Field(4,item,label,row);
        if (raw is null) return null;
        if (ScalarLength(raw) > max) throw Field(5,item,label,row);
        foreach (var rune in raw.EnumerateRunes())
            if (Rune.IsControl(rune) && rune.Value is not (9 or 10 or 13)) throw Field(5,item,label,row);
        var value = raw.Replace("\r\n","\n",StringComparison.Ordinal).Replace('\r','\n').Replace('\t',' ').Trim();
        if (kana) value = value.Normalize(NormalizationForm.FormKC);
        if (value.Length == 0) { if (required) throw Field(4,item,label,row); return null; }
        if (ScalarLength(value) > max || (kana && !KanaPattern().IsMatch(value))) throw Field(5,item,label,row);
        return value;
    }
    public static BusinessException Field(int msg, string item, string label, int? row = null)
    {
        var text = Messages.Get(msg).Replace("{項目名}",label,StringComparison.Ordinal).Replace("{行番号}",row?.ToString(CultureInfo.InvariantCulture)??"",StringComparison.Ordinal);
        return new(Outcome.Of(msg,fields:[new(item,row,$"MSG-{msg:000}",text)]) with { Message=text });
    }
    public static string LoginId(string raw)
    {
        var value = Text(raw,20,true,"F01-I01","ログインID")!;
        if (!LoginPattern().IsMatch(value)) throw Field(5,"F01-I01","ログインID");
        return value.ToUpperInvariant();
    }
    public static void Password(string raw)
    {
        var count=ScalarLength(raw);
        if (count==0) throw Field(4,"F01-I02","パスワード");
        if (count is <MinimumPasswordScalars or >MaximumPasswordScalars) throw Field(5,"F01-I02","パスワード");
    }
    public static string SearchKey(string? value) => value is null ? "" : string.Concat(value.Normalize(NormalizationForm.FormKC)
        .EnumerateRunes().Where(r=>!Rune.IsWhiteSpace(r)).Select(r=>r.ToString())).ToUpperInvariant();
    public static string Code(string raw, string item)
    {
        var value=Text(raw,2,true,item,"コード")!;
        if (!CodePattern().IsMatch(value) || value=="00") throw Field(5,item,"コード（01～99）");
        return value;
    }
    public static void Category(string value)
    {
        if (value is not ("DEPARTMENT" or "EMPLOYMENT_STATUS" or "PROJECT_ROLE")) throw BusinessException.Error(16);
    }
    public static SearchCriteria Search(SearchInput raw)
    {
        var no=Text(raw.EmployeeNo,6,false,"F03-I01","社員番号");
        if(no is not null && !EmployeeNoPattern().IsMatch(no)) throw Field(5,"F03-I01","社員番号（6桁）");
        var name=Text(raw.Name,40,false,"F03-I02","氏名・カナ");
        if(ScalarLength(SearchKey(name))>40)throw Field(5,"F03-I02","氏名・カナ（正規化後40文字）");
        var dep=raw.Department.Length==0?null:raw.Department;
        var status=raw.EmploymentStatus.Length==0?null:raw.EmploymentStatus;
        if(dep is not null&&(!CodePattern().IsMatch(dep)||dep=="00"))throw BusinessException.Error(16);
        if(status is not null&&status is not("01" or "02" or "03"))throw BusinessException.Error(16);
        return new(no,name,dep,status);
    }
    // Navigation raw is not business input validation or normalization.
    public static void TechnicalRaw(SearchRaw raw)
    {
        foreach(var value in new[]{raw.EmployeeNo,raw.Name,raw.Department,raw.EmploymentStatus})TechnicalRaw(value);
    }
    public static void TechnicalRaw(string? value)
    {
        if(value is null||value.Length>16384)throw new ArgumentException("Raw text exceeds transport bounds.");
        try{ScalarLength(value);}catch(BusinessException){throw new ArgumentException("Invalid UTF-16.");}
    }
    public static EmployeeDraft Employee(EmployeeRaw raw, DateOnly businessDate)
    {
        var no=Text(raw.EmployeeNo,6,true,"F04-I01","社員番号")!;
        if(!EmployeeNoPattern().IsMatch(no)) throw Field(5,"F04-I01","社員番号（6桁）");
        var name=Text(raw.Name,40,true,"F04-I02","氏名")!;
        var kana=Text(raw.Kana,80,true,"F04-I03","氏名カナ",kana:true)!;
        var dep=Code(raw.DepartmentCode,"F04-I04");
        var status=Code(raw.EmploymentStatus,"F04-I05");
        if(status is not ("01" or "02" or "03")) throw Field(5,"F04-I05","在籍区分");
        var date=Text(raw.JoinDateRaw,10,true,"F04-I06","入社日")!;
        if(!DateOnly.TryParseExact(date,"yyyy-MM-dd",CultureInfo.InvariantCulture,DateTimeStyles.None,out var join) || join<new DateOnly(1900,1,1)||join>businessDate)
            throw Field(5,"F04-I06","入社日（1900-01-01～業務日）");
        return new(no,name,kana,dep,status,join,Text(raw.CareerSummary,1000,false,"F04-I07","職務要約"),
            Text(raw.Skills,1000,false,"F04-I08","スキル・得意分野"),Text(raw.Qualifications,1000,false,"F04-I09","保有資格"),Text(raw.SelfPr,1000,false,"F04-I10","自己PR"));
    }
    public static CareerDraft Career(CareerRaw raw, DateOnly month, int row)
    {
        if(raw.ClientRowKey==Guid.Empty||raw.CareerId is <=0) throw BusinessException.Error(25);
        var startRaw=Text(raw.StartMonthRaw,7,true,"F04-I14","開始年月",row)!;
        var endRaw=Text(raw.EndMonthRaw,7,false,"F04-I15","終了年月",row);
        static bool ParseMonth(string value,out DateOnly result) => DateOnly.TryParseExact(value+"-01","yyyy-MM-dd",CultureInfo.InvariantCulture,DateTimeStyles.None,out result);
        if(!ParseMonth(startRaw,out var start)||start<new DateOnly(1900,1,1)) throw Field(5,"F04-I14","開始年月",row);
        DateOnly? end=null;
        if(endRaw is not null) { if(!ParseMonth(endRaw,out var parsed)) throw Field(5,"F04-I15","終了年月",row); end=parsed; }
        if(start>month||end>month||end<start) throw Field(7,"F04-I14","年月",row);
        var company=Text(raw.CompanyName,100,true,"F04-I16","会社名",row)!;
        var project=Text(raw.ProjectName,100,true,"F04-I17","案件名",row)!;
        var description=Text(raw.Description,1000,true,"F04-I18","業務概要",row)!;
        var duties=Text(raw.Duties,1000,true,"F04-I19","担当業務",row)!;
        var achievements=Text(raw.Achievements,1000,false,"F04-I20","実績・成果",row);
        var technology=Text(raw.Technologies,500,false,"F04-I21","技術環境",row);
        var role=Code(raw.RoleCode,"F04-I23");
        var team=Text(raw.TeamSizeRaw,3,true,"F04-I24","チーム人数",row)!;
        if(!IntegerPattern().IsMatch(team)||!short.TryParse(team,NumberStyles.None,CultureInfo.InvariantCulture,out var teamSize)||teamSize is <1 or >999) throw Field(5,"F04-I24","チーム人数（1～999）",row);
        var phases=Text(raw.Phases,200,false,"F04-I22","担当工程",row);
        return new(raw.CareerId,raw.ClientRowKey,new(start,end,company,project,description,duties,achievements,technology,phases,role,teamSize));
    }
    public static CareerDraft[] Careers(CareerRaw[] raw, DateOnly month)
    {
        if(raw.Length>20) throw BusinessException.Error(18);
        if(raw.Select(x=>x.ClientRowKey).Distinct().Count()!=raw.Length) throw BusinessException.Error(25);
        var rows=raw.Select((x,i)=>Career(x,month,i+1)).ToArray();
        var seen=new HashSet<CareerValues>();
        for(var i=0;i<rows.Length;i++) if(!seen.Add(rows[i].Values)) throw Field(26,"F04-I13","経歴",i+1);
        return rows;
    }
    public static void ChildSet(EmployeeSnapshot? snapshot,IReadOnlyList<CareerDraft> careers,IReadOnlyList<long> removed)
    {
        var retained=careers.Where(x=>x.CareerId.HasValue).Select(x=>x.CareerId!.Value).ToArray();
        if(retained.Distinct().Count()!=retained.Length||removed.Distinct().Count()!=removed.Count||removed.Any(x=>x<=0)||retained.Intersect(removed).Any()) throw BusinessException.Error(25);
        var loaded=snapshot?.Careers.Select(x=>x.CareerId!.Value).ToHashSet()??[];
        if(!loaded.SetEquals(retained.Concat(removed))) throw BusinessException.Error(25);
    }
    public static void Reference(IReadOnlyList<CodeRow> codes,string category,string code,string? original)
    {
        var found=codes.Where(x=>x.Category==category&&x.Code==code).ToArray();
        if(found.Length!=1) throw BusinessException.Error(16);
        if(!found[0].Enabled && code!=original) throw BusinessException.Error(16);
    }
    public static void FixedCodes(IReadOnlyList<CodeRow> rows)
    {
        string[] names=["在職","休職","退職"];
        var fixedRows=rows.Where(x=>x.Category=="EMPLOYMENT_STATUS").OrderBy(x=>x.Code,StringComparer.Ordinal).ToArray();
        if(fixedRows.Length!=3) throw BusinessException.Error(20,"Corrupt");
        for(var i=0;i<3;i++) if(fixedRows[i].Code!=$"0{i+1}"||fixedRows[i].Name!=names[i]||fixedRows[i].SortOrder!=i+1||!fixedRows[i].Enabled) throw BusinessException.Error(20,"Corrupt");
        if(rows.GroupBy(x=>x.Category).Any(x=>x.Count()>99)||rows.Any(x=>x.Revision<1||x.SortOrder is <1 or >999||ScalarLength(x.Name)>40||x.Name.Length==0)) throw BusinessException.Error(20,"Corrupt");
    }
    public static CodeDraft CodeInput(CodeSaveInput raw)
    {
        Category(raw.Category);
        if(raw.Category=="EMPLOYMENT_STATUS") throw BusinessException.Error(23);
        var code=Code(raw.Code,"F06-I03");
        var name=Text(raw.Name,40,true,"F06-I04","名称")!;
        var sort=Text(raw.SortOrderRaw,3,true,"F06-I05","並び順")!;
        if(!IntegerPattern().IsMatch(sort)||!short.TryParse(sort,NumberStyles.None,CultureInfo.InvariantCulture,out var value)||value is <1 or >999) throw Field(5,"F06-I05","並び順（1～999）");
        return new(raw.Category,code,name,value,raw.Enabled);
    }
}
