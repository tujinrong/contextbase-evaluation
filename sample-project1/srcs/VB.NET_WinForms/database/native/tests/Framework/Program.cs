using System;
using System.Collections.Generic;
using System.Data.SqlTypes;
using System.Text;
using System.Xml;
using StudentManagement.Native;

internal static class Program
{
    private static int count;
    private static void Check(bool ok,string name) {count++;Console.WriteLine(count+"\t"+(ok?"PASS":"FAIL")+"\t"+name);if(!ok)throw new Exception(name);}
    private static string Wire(Dictionary<string,string> input) {
        var buffer=new StringBuilder();
        using(var writer=XmlWriter.Create(buffer,new XmlWriterSettings{OmitXmlDeclaration=true,NewLineHandling=NewLineHandling.Entitize})) {
            writer.WriteStartElement("raw");foreach(var item in input){writer.WriteStartElement(item.Key);if(item.Value==null)writer.WriteAttributeString("null","true");else writer.WriteString(item.Value);writer.WriteEndElement();}writer.WriteEndElement();
        }
        return buffer.ToString();
    }
    private static XmlDocument Normalize(Dictionary<string,string> input) {var doc=new XmlDocument();doc.LoadXml(NativeNormalizer.NormalizeRaw(new SqlString(Wire(input)),new SqlDateTime(new DateTime(2026,10,12))).Value);return doc;}
    private static string Value(XmlDocument doc,string key) {return doc.SelectSingleNode("/normalized/values/"+key)?.InnerText;}
    private static void Main() {
        Console.WriteLine("CLR runtime="+Environment.Version+", assembly="+typeof(NativeNormalizer).Assembly.Location);
        var input=new Dictionary<string,string>{{"student_no","ｓ２０２６-０１"},{"student_name","山田 太郎"},{"student_name_kana","やまだ　たろう"},{"birth_era","HEISEI"},{"birth_year","１５"},{"birth_month","０４"},{"birth_day","０２"},{"gender_code","０"},{"postal_code","１００－００００"},{"prefecture_code","１３"},{"address_line1","東京都見本町１"},{"address_line2",null},{"phone_number","０３－１２３４－５６７８"},{"email_address","Student@EXAMPLE.INVALID"},{"admission_date","２０２６-０４-０１"},{"enrollment_status_code","０１"},{"enrollment_end_date",null},{"class_id","1"},{"emergency_contact_name",null},{"relationship_code",null},{"emergency_phone_number",null},{"remarks",null},{"school_year","2026"},{"grade_code","００"},{"reason",null}};
        var doc=Normalize(input);
        Check(doc.DocumentElement.GetAttribute("ok")=="true","actual net472 DLL SQLFunction wrapper baseline");
        Check(Value(doc,"student_no")=="S2026-01","Framework NFKC identifier");
        Check(Value(doc,"student_name")=="山田 太郎","display text remains raw");
        Check(Value(doc,"student_name_kana")=="ヤマダ タロウ","Framework kana and space folding");
        Check(Value(doc,"birth_date")=="2003-04-02","Framework era four-part input");
        Check(Value(doc,"email_address")=="Student@example.invalid","Framework email local/domain case");
        Check(doc.SelectSingleNode("/normalized/values/relationship_category/@null").Value=="true","Framework optional relationship NULL");
        input["school_year"]="02026";Check(Normalize(input).DocumentElement.GetAttribute("code")=="E-DATE-003","Framework raw five-digit school year rejected");
        input["school_year"]="２０２６";Check(Normalize(input).SelectSingleNode("/normalized/hints/school_year").InnerText=="2026","Framework raw4 fullwidth school year common NFKC");
        input["school_year"]="026";Check(Normalize(input).DocumentElement.GetAttribute("code")=="E-DATE-003","Framework short school year rejected");
        input["school_year"]=null;Check(Normalize(input).DocumentElement.GetAttribute("ok")=="true","Framework optional school year NULL accepted");input["school_year"]="2026";
        input["student_name"]=new StringBuilder().Insert(0,"𠮷",8).ToString();Check(Normalize(input).DocumentElement.GetAttribute("ok")=="true","eight supplementary scalars accepted");
        input["student_name"]+="𠮷";Check(Normalize(input).DocumentElement.GetAttribute("code")=="E-STU-002","nine supplementary scalars rejected");input["student_name"]="山田 太郎";
        input["student_name_kana"]=new StringBuilder().Insert(0,"ｶﾞ",18).ToString();Check(Normalize(input).DocumentElement.GetAttribute("ok")=="true","Framework raw36/saved18 halfwidth kana");
        input["student_name_kana"]+="ｶ";Check(Normalize(input).DocumentElement.GetAttribute("max")=="36","Framework raw max metadata");input["student_name_kana"]="やまだ　たろう";
        input["birth_era"]="REIWA";input["birth_year"]="元";input["birth_month"]="04";input["birth_day"]="30";Check(Normalize(input).DocumentElement.GetAttribute("code")=="E-DATE-001","Framework era-start boundary rejected");
        Check(NativeNormalizer.NormalizeRaw(SqlString.Null,new SqlDateTime(new DateTime(2026,10,12))).Value.Contains("E-COM-003"),"SQL NULL wire rejected by deployed wrapper");
        Check(NativeNormalizer.NormalizeReason(new SqlString(" 確認理由 ")).Value.Contains("確認理由"),"actual Framework reason wrapper");
        var cls=new Dictionary<string,string>{{"school_year","2026"},{"grade_code","００"},{"class_code","ａ-１"},{"class_name","１年Ａ組"},{"valid_from","2026-04-01"},{"valid_to","2027-03-31"},{"capacity",null},{"display_order","0"},{"is_active","true"},{"remarks",null},{"reason",null}};
        doc.LoadXml(NativeNormalizer.NormalizeClass(new SqlString(Wire(cls))).Value);Check(Value(doc,"class_code")=="A-1","actual Framework class wrapper and NFKC");
        cls["school_year"]="02026";doc.LoadXml(NativeNormalizer.NormalizeClass(new SqlString(Wire(cls))).Value);Check(doc.DocumentElement.GetAttribute("code")=="E-DATE-003","Framework class raw five-digit school year rejected");
        cls["school_year"]="２０２６";doc.LoadXml(NativeNormalizer.NormalizeClass(new SqlString(Wire(cls))).Value);Check(Value(doc,"school_year")=="2026","Framework class raw4 fullwidth school year common NFKC");cls["school_year"]="2026";
        var code=new Dictionary<string,string>{{"category_id","GRADE"},{"code_value","０１"},{"code_name","１年"},{"display_order","1"},{"is_active","true"},{"valid_from","2026-04-01"},{"valid_to",null},{"remarks",null},{"reason",null}};
        doc.LoadXml(NativeNormalizer.NormalizeCode(new SqlString(Wire(code))).Value);Check(Value(doc,"code_value")=="01","actual Framework code wrapper and NFKC");
        Check(!NativeNormalizer.NormalizeRaw(new SqlString("<!DOCTYPE raw [<!ENTITY e SYSTEM 'file:///never-read'>]><raw/>"),new SqlDateTime(new DateTime(2026,10,12))).Value.Contains("ok=\"true\""),"Framework DTD input rejected");
        Console.WriteLine("PASS: "+count+" actual .NET Framework assembly assertions (SQL Server hosting not exercised)");
    }
}
