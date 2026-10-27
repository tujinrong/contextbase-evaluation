using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace StudentManagement.Core;

// Evidence: binary export modUnicode.TextValue/ScalarCount/IsWhite and
// modJapaneseDate.StrictIso/ParseBirthDate. Business limits are scalar counts.
public static class TextRules
{
    public static int ScalarCount(string s)
    {
        var count=0;
        for(var i=0;i<s.Length;i++,count++)
        {
            if(char.IsHighSurrogate(s[i]))
            {
                if(i+1>=s.Length || !char.IsLowSurrogate(s[i+1])) throw Error("E-STU-002");
                i++;
            }
            else if(char.IsLowSurrogate(s[i])) throw Error("E-STU-002");
        }
        return count;
    }
    public static bool IsWhite(char c) => c is >= '\u0009' and <= '\u000d' or '\u0020' or '\u0085' or '\u00a0' or '\u1680'
        or >= '\u2000' and <= '\u200a' or '\u2028' or '\u2029' or '\u202f' or '\u205f' or '\u3000';
    public static string TrimUnicode(string s)
    {
        var a=0;var b=s.Length;
        while(a<b && IsWhite(s[a]))a++;
        while(b>a && IsWhite(s[b-1]))b--;
        return s[a..b];
    }
    public static string WithoutWhite(string s) => new(s.Where(c=>!IsWhite(c)).ToArray());
    public static string Nfkc(string s) { ScalarCount(s); return s.Normalize(NormalizationForm.FormKC); }
    public static bool Match(string s,string pattern) => Regex.IsMatch(s,pattern,RegexOptions.CultureInvariant,TimeSpan.FromSeconds(1));
    public static string? Text(string? raw,int maxRaw,int maxSaved,string kind,string? field=null)
    {
        var s=raw??"";
        if(ScalarCount(s)>maxRaw)throw Error("E-STU-002",field);
        foreach(var c in s)
            if(c=='\0' || (c<32 && !(kind=="memo" && c is '\r' or '\n')) || c is >= '\u007f' and <= '\u009f')throw Error("E-STU-002",field);
        s=TrimUnicode(s);
        switch(kind)
        {
            case "number":case "code":s=Nfkc(s).ToUpperInvariant();break;
            case "nameKey":s=WithoutWhite(Nfkc(s).ToUpperInvariant());break;
            case "kana":
                var sb=new StringBuilder();var lastSpace=false;
                foreach(var ch in Nfkc(s))
                {
                    var c=ch;
                    if(c is >= '\u3041' and <= '\u3096' or '\u309d' or '\u309e')c=(char)(c+0x60);
                    if(IsWhite(c)){if(!lastSpace)sb.Append(' ');lastSpace=true;}
                    else
                    {
                        if(!(c is >= '\u30a1' and <= '\u30fa' or '\u30fc' or '\u30fb' or '\u30fd' or '\u30fe'))throw Error("E-STU-004",field);
                        sb.Append(c);lastSpace=false;
                    }
                }
                s=TrimUnicode(sb.ToString());break;
            case "phone":case "postal":
                s=WithoutWhite(Nfkc(s).Replace("-","").Replace("\u2010","").Replace("\u2011","").Replace("\u2212",""));
                if(kind=="phone")s=s.Replace("(","").Replace(")","");
                break;
            case "memo":s=s.Replace("\r\n","\n").Replace('\r','\n');break;
            case "email":var at=s.IndexOf('@');if(at>=0)s=s[..(at+1)]+s[(at+1)..].ToLowerInvariant();break;
        }
        if(ScalarCount(s)>maxSaved)throw Error("E-STU-002",field);
        return s.Length==0?null:s;
    }
    public static int PositiveId(int value)
    {if(value<1)throw Error("E-COM-003");return value;}
    public static int PositiveId(string raw)
    {
        if(!Match(raw,"^[0-9]{1,10}$")||!int.TryParse(raw,NumberStyles.None,CultureInfo.InvariantCulture,out var n)||n<1)throw Error("E-COM-003");
        return n;
    }
    public static int Integer(string? raw,bool positive=false)
    {
        var s=Nfkc(raw??"0");
        if(!Match(s,"^[0-9]{1,10}$") || !int.TryParse(s,NumberStyles.None,CultureInfo.InvariantCulture,out var n) || (positive&&n<1))throw Error("E-COM-003");
        return n;
    }
    public static BusinessException Error(string code,string? field=null) => new(code,code,field);
}

public static class JapaneseDate
{
    public static string FormatBirthDate(string iso)
    {
        var p=BirthParts(iso);
        var label=p.Era switch {"REIWA"=>"令和","HEISEI"=>"平成","SHOWA"=>"昭和","TAISHO"=>"大正",_=>"明治"};
        return $"{label}{(p.Year=="1"?"元":p.Year)}年{p.Month}月{p.Day}日";
    }
    public static string? StrictIso(string? raw,bool required)
    {
        var s=raw??"";
        if(TextRules.ScalarCount(s)>10)throw TextRules.Error("E-STU-005");
        if(s==""&&!required)return null;
        s=TextRules.Nfkc(s);
        if(!TextRules.Match(s,"^[0-9]{4}-[0-9]{2}-[0-9]{2}$") || !DateOnly.TryParseExact(s,"yyyy-MM-dd",CultureInfo.InvariantCulture,DateTimeStyles.None,out _))throw TextRules.Error("E-STU-005");
        return s;
    }
    public static string ParseBirthDate(string? era,string? year,string? month,string? day,string today)
    {
        era??="";year??="";month??="";day??="";
        if(TextRules.ScalarCount(era)>10||TextRules.ScalarCount(year)>4||TextRules.ScalarCount(month)>2||TextRules.ScalarCount(day)>2)throw TextRules.Error("E-DATE-001");
        year=TextRules.Nfkc(year);month=TextRules.Nfkc(month);day=TextRules.Nfkc(day);
        if(year=="元")year="1";
        if(!TextRules.Match(year,"^[0-9]{1,4}$")||!TextRules.Match(month,"^[0-9]{1,2}$")||!TextRules.Match(day,"^[0-9]{1,2}$"))throw TextRules.Error("E-DATE-001");
        var y=int.Parse(year,CultureInfo.InvariantCulture);
        var (offset,first,last)=era switch
        {"MEIJI"=>(1867,"1900-01-01","1912-07-29"),"TAISHO"=>(1911,"1912-07-30","1926-12-24"),
         "SHOWA"=>(1925,"1926-12-25","1989-01-07"),"HEISEI"=>(1988,"1989-01-08","2019-04-30"),
         "REIWA"=>(2018,"2019-05-01",today),_=>throw TextRules.Error("E-DATE-001")};
        if(y<1||y+offset>9999)throw TextRules.Error("E-DATE-001");
        var s=$"{y+offset:0000}-{int.Parse(month,CultureInfo.InvariantCulture):00}-{int.Parse(day,CultureInfo.InvariantCulture):00}";
        s=StrictIso(s,true)!;
        if(string.CompareOrdinal(s,first)<0||string.CompareOrdinal(s,last)>0)throw TextRules.Error("E-DATE-001");
        if(string.CompareOrdinal(s,"1900-01-01")<0||string.CompareOrdinal(s,today)>0)throw TextRules.Error("E-DATE-002");
        return s;
    }
    public static (string Era,string Year,string Month,string Day) BirthParts(string iso)
    {
        StrictIso(iso,true);
        var (era,offset)=string.CompareOrdinal(iso,"2019-05-01")>=0?("REIWA",2018):string.CompareOrdinal(iso,"1989-01-08")>=0?("HEISEI",1988):
            string.CompareOrdinal(iso,"1926-12-25")>=0?("SHOWA",1925):string.CompareOrdinal(iso,"1912-07-30")>=0?("TAISHO",1911):("MEIJI",1867);
        return(era,(int.Parse(iso[..4],CultureInfo.InvariantCulture)-offset).ToString(CultureInfo.InvariantCulture),iso[5..7],iso[8..10]);
    }
}
