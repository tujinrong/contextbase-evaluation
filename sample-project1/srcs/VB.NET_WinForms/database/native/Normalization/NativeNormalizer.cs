using System;
using System.Collections.Generic;
using System.Data.SqlTypes;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Xml;
#if !BOUNDARY_TEST
using Microsoft.SqlServer.Server;
#endif

namespace StudentManagement.Native
{
    // SQLCLR .NET Framework: no file/network/native access and no database access.
    public static class NativeNormalizer
    {
        private static readonly string[] RawFields = {
            "student_no","student_name","student_name_kana","birth_era","birth_year","birth_month","birth_day",
            "gender_code","postal_code","prefecture_code","address_line1","address_line2","phone_number","email_address",
            "admission_date","enrollment_status_code","enrollment_end_date","class_id","emergency_contact_name","relationship_code",
            "emergency_phone_number","remarks","school_year","grade_code","reason"
        };
        private sealed class Invalid : Exception
        {
            public readonly string Field, Code;
            public readonly int? Maximum;
            public Invalid(string field,string code,int? maximum=null) { Field=field; Code=code;Maximum=maximum; }
        }
#if !BOUNDARY_TEST
        [SqlFunction(IsDeterministic=true,IsPrecise=true,DataAccess=DataAccessKind.None,SystemDataAccess=SystemDataAccessKind.None)]
        public static SqlString NormalizeRaw(SqlString raw,SqlDateTime businessDay)
        {
            if (raw.IsNull || businessDay.IsNull) return new SqlString(Error("","E-COM-003"));
            return new SqlString(NormalizeText(raw.Value,businessDay.Value.Date));
        }
        [SqlFunction(IsDeterministic=true,IsPrecise=true,DataAccess=DataAccessKind.None,SystemDataAccess=SystemDataAccessKind.None)]
        public static SqlString NormalizeReason(SqlString raw) { return new SqlString(ReasonText(raw.IsNull?null:raw.Value)); }
        [SqlFunction(IsDeterministic=true,IsPrecise=true,DataAccess=DataAccessKind.None,SystemDataAccess=SystemDataAccessKind.None)]
        public static SqlString NormalizeClass(SqlString raw) {return new SqlString(MasterText(raw.IsNull?null:raw.Value,true));}
        [SqlFunction(IsDeterministic=true,IsPrecise=true,DataAccess=DataAccessKind.None,SystemDataAccess=SystemDataAccessKind.None)]
        public static SqlString NormalizeCode(SqlString raw) {return new SqlString(MasterText(raw.IsNull?null:raw.Value,false));}
#endif
        public static string ReasonText(string raw)
        {
            try {var value=Text(raw,60,60,"reason",true,true);var doc=new XmlDocument();var root=doc.CreateElement("normalized");doc.AppendChild(root);root.SetAttribute("ok","true");Append(doc,root,"hints",new Dictionary<string,string>{{"reason",value}});return doc.OuterXml;}
            catch (Invalid) {return Error("reason","E-STU-020");}
        }
        public static string MasterText(string raw,bool isClass)
        {
            try {
                var fields=isClass?new[]{"school_year","grade_code","class_code","class_name","valid_from","valid_to","capacity","display_order","is_active","remarks","reason"}:new[]{"category_id","code_value","code_name","display_order","is_active","valid_from","valid_to","remarks","reason"};
                var input=ReadRaw(raw,fields);var values=new Dictionary<string,string>();
                if(isClass) {
                    values.Add("school_year",SchoolYear(input["school_year"],true));
                    values.Add("grade_code",Code(input["grade_code"],2,"grade_code",true));
                    values.Add("class_code",Identifier(input["class_code"],9,"class_code"));
                    values.Add("class_name",Text(input["class_name"],18,18,"class_name",true));
                    values.Add("capacity",Integer(input["capacity"],1,9999,"capacity",true));
                } else {
                    var category=Text(input["category_id"],24,24,"category_id",true);
                    if(!new[]{"GENDER","PREFECTURE","ENROLLMENT_STATUS","RELATIONSHIP","GRADE"}.Contains(category))throw new Invalid("category_id","E-MST-003");
                    values.Add("category_id",category);
                    var code=Text(input["code_value"],10,10,"code_value",true).Normalize(NormalizationForm.FormKC);
                    if(code.Any(c=>c<'0'||c>'9') || code.Length>10)throw new Invalid("code_value","E-STU-009");
                    values.Add("code_value",code);values.Add("code_name",Text(input["code_name"],12,12,"code_name",true));
                }
                values.Add("display_order",Integer(input["display_order"],0,int.MaxValue,"display_order",false));
                if(input["is_active"]!="true" && input["is_active"]!="false")throw new Invalid("is_active","E-COM-003");
                values.Add("is_active",input["is_active"]=="true"?"1":"0");
                var from=Date(input["valid_from"],"valid_from",DateTime.MaxValue.Date);
                var to=string.IsNullOrEmpty(input["valid_to"])?(DateTime?)null:Date(input["valid_to"],"valid_to",DateTime.MaxValue.Date);
                if(to<from || isClass && (to==null || from<new DateTime(int.Parse(values["school_year"],CultureInfo.InvariantCulture),4,1) || to>new DateTime(int.Parse(values["school_year"],CultureInfo.InvariantCulture)+1,3,31)))throw new Invalid("valid_to","E-MST-004");
                values.Add("valid_from",Iso(from));values.Add("valid_to",to==null?null:Iso(to.Value));
                values.Add("remarks",Text(input["remarks"],120,120,"remarks",false,true));
                var reason=Text(input["reason"],60,60,"reason",false,true);
                var doc=new XmlDocument();var root=doc.CreateElement("normalized");doc.AppendChild(root);root.SetAttribute("ok","true");
                Append(doc,root,"values",values);Append(doc,root,"hints",new Dictionary<string,string>{{"reason",reason}});return doc.OuterXml;
            } catch(Invalid error) {return Error(error.Field,error.Code,error.Maximum);}
            catch(Exception error) when(error is XmlException || error is ArgumentException || error is OverflowException) {return Error("","E-COM-003");}
        }
        private static string Integer(string raw,long minimum,long maximum,string field,bool optional)
        {
            if(string.IsNullOrEmpty(raw)) {if(optional)return null;throw new Invalid(field,"E-MST-004");}
            if(raw.Length>10)throw new Invalid(field,"E-MST-004");raw=raw.Normalize(NormalizationForm.FormKC);long n;
            if(raw.Any(c=>c<'0'||c>'9') || !long.TryParse(raw,NumberStyles.None,CultureInfo.InvariantCulture,out n) || n<minimum || n>maximum)throw new Invalid(field,"E-MST-004");
            return n.ToString(CultureInfo.InvariantCulture);
        }
        private static Dictionary<string,string> ReadRaw(string raw,string[] fields)
        {
            if(raw==null || raw.Length>32768 || raw.IndexOf('\r')>=0)throw new Invalid("","E-COM-003");
            var doc=new XmlDocument {XmlResolver=null};
            using(var reader=XmlReader.Create(new StringReader(raw),new XmlReaderSettings {DtdProcessing=DtdProcessing.Prohibit,XmlResolver=null,MaxCharactersInDocument=32768}))doc.Load(reader);
            if(doc.DocumentElement==null || doc.DocumentElement.Name!="raw" || doc.DocumentElement.Attributes.Count!=0)throw new Invalid("","E-COM-003");
            var result=new Dictionary<string,string>();
            foreach(XmlNode child in doc.DocumentElement.ChildNodes) {
                var e=child as XmlElement;
                if(e==null || !fields.Contains(e.Name) || result.ContainsKey(e.Name) || e.Attributes.Count>1 || e.ChildNodes.Cast<XmlNode>().Any(n=>n.NodeType!=XmlNodeType.Text && n.NodeType!=XmlNodeType.Whitespace && n.NodeType!=XmlNodeType.SignificantWhitespace))throw new Invalid("","E-COM-003");
                if(e.Attributes.Count==1 && (e.Attributes[0].Name!="null" || e.Attributes[0].Value!="true" || e.InnerText!=""))throw new Invalid(e.Name,"E-COM-003");
                result.Add(e.Name,e.HasAttribute("null")?null:e.InnerText);
            }
            if(result.Count!=fields.Length)throw new Invalid("","E-COM-003");return result;
        }
        public static string NormalizeText(string raw,DateTime businessDay)
        {
            try {
                if (raw==null || raw.Length>32768 || raw.IndexOf('\r')>=0) throw new Invalid("","E-COM-003");
                var doc=new XmlDocument { XmlResolver=null };
                using (var reader=XmlReader.Create(new StringReader(raw),new XmlReaderSettings { DtdProcessing=DtdProcessing.Prohibit,XmlResolver=null,MaxCharactersInDocument=32768 }))
                    doc.Load(reader);
                if (doc.DocumentElement==null || doc.DocumentElement.Name!="raw" || doc.DocumentElement.Attributes.Count!=0) throw new Invalid("","E-COM-003");
                var input=new Dictionary<string,string>(StringComparer.Ordinal);
                foreach (XmlNode child in doc.DocumentElement.ChildNodes) {
                    var element=child as XmlElement;
                    if (element==null || !RawFields.Contains(element.Name) || input.ContainsKey(element.Name)) throw new Invalid("","E-COM-003");
                    if (element.ChildNodes.Cast<XmlNode>().Any(n=>n.NodeType!=XmlNodeType.Text && n.NodeType!=XmlNodeType.Whitespace && n.NodeType!=XmlNodeType.SignificantWhitespace)) throw new Invalid(element.Name,"E-COM-003");
                    if (element.Attributes.Count>1 || element.Attributes.Count==1 && (element.Attributes[0].Name!="null" || element.Attributes[0].Value!="true" || element.InnerText!="")) throw new Invalid(element.Name,"E-COM-003");
                    input.Add(element.Name,element.HasAttribute("null")?null:element.InnerText);
                }
                if (input.Count!=RawFields.Length) throw new Invalid("","E-COM-003");
                var values=new Dictionary<string,string>(StringComparer.Ordinal);
                values.Add("student_no",Identifier(input["student_no"],15,"student_no"));
                values.Add("student_name",Text(input["student_name"],8,8,"student_name",true));
                values.Add("student_name_kana",Kana(input["student_name_kana"]));
                var birth=Birth(input,businessDay);
                values.Add("birth_date",Iso(birth));
                values.Add("gender_code",Code(input["gender_code"],1,"gender_code",true));
                values.Add("postal_code",Postal(input["postal_code"]));
                values.Add("prefecture_code",Code(input["prefecture_code"],2,"prefecture_code",true));
                values.Add("address_line1",Text(input["address_line1"],45,45,"address_line1",true));
                values.Add("address_line2",Text(input["address_line2"],45,45,"address_line2",false));
                values.Add("phone_number",Phone(input["phone_number"],"phone_number"));
                values.Add("email_address",Email(input["email_address"]));
                var admission=Date(input["admission_date"],"admission_date",businessDay);
                values.Add("admission_date",Iso(admission));
                values.Add("enrollment_status_code",Code(input["enrollment_status_code"],2,"enrollment_status_code",true));
                var end=string.IsNullOrEmpty(input["enrollment_end_date"])?(DateTime?)null:Date(input["enrollment_end_date"],"enrollment_end_date",businessDay);
                values.Add("enrollment_end_date",end==null?null:Iso(end.Value));
                values.Add("class_id",Id(input["class_id"],"class_id",long.MaxValue));
                values.Add("emergency_contact_name",Text(input["emergency_contact_name"],8,8,"emergency_contact_name",false));
                values.Add("relationship_code",Code(input["relationship_code"],2,"relationship_code",false));
                values.Add("emergency_phone_number",Phone(input["emergency_phone_number"],"emergency_phone_number"));
                values.Add("remarks",Text(input["remarks"],120,120,"remarks",false,true));
                values.Add("name_key",WithoutSpaces(values["student_name"].Normalize(NormalizationForm.FormKC).ToUpperInvariant()));
                if (Scalars(values["name_key"])>160) throw new Invalid("student_name","E-STU-002");
                values.Add("kana_key",values["student_name_kana"].Replace(" ",""));
                values.Add("relationship_category",values["relationship_code"]==null?null:"RELATIONSHIP");
                var status=values["enrollment_status_code"];
                if (birth>admission) throw new Invalid("admission_date","E-STU-007");
                if (!new[]{"01","02","03","04"}.Contains(status)) throw new Invalid("enrollment_status_code","E-STU-009");
                var active=status=="01" || status=="02";
                if (active?end!=null:end==null || end<admission) throw new Invalid("enrollment_end_date","E-STU-008");
                if (active && values["class_id"]==null) throw new Invalid("class_id","E-STU-012");
                if (values["phone_number"]==null && values["email_address"]==null && values["emergency_phone_number"]==null) throw new Invalid("phone_number","E-STU-018");
                var emergency=new[]{"emergency_contact_name","relationship_code","emergency_phone_number"}.Count(k=>values[k]!=null);
                if (emergency!=0 && emergency!=3) throw new Invalid("emergency_contact_name","E-STU-019");
                var hints=new Dictionary<string,string>();
                hints.Add("school_year",SchoolYear(input["school_year"]));
                hints.Add("grade_code",Code(input["grade_code"],2,"grade_code",false));
                hints.Add("reason",Text(input["reason"],60,60,"reason",false,true));
                var output=new XmlDocument(); var root=output.CreateElement("normalized"); output.AppendChild(root); root.SetAttribute("ok","true");
                Append(output,root,"values",values); Append(output,root,"hints",hints);
                return output.OuterXml;
            } catch (Invalid error) { return Error(error.Field,error.Code,error.Maximum); }
            catch (Exception error) when (error is ArgumentException || error is XmlException || error is OverflowException) { return Error("","E-COM-003"); }
        }
        private static void Append(XmlDocument doc,XmlElement root,string name,Dictionary<string,string> values)
        {
            var parent=doc.CreateElement(name); root.AppendChild(parent);
            foreach (var pair in values.OrderBy(p=>p.Key,StringComparer.Ordinal)) { var e=doc.CreateElement(pair.Key); if (pair.Value==null) e.SetAttribute("null","true"); else e.InnerText=pair.Value; parent.AppendChild(e); }
        }
        private static string Error(string field,string code,int? maximum=null)
        {
            var doc=new XmlDocument();var e=doc.CreateElement("normalized");doc.AppendChild(e);e.SetAttribute("ok","false");e.SetAttribute("field",field);e.SetAttribute("code",code);if(maximum!=null)e.SetAttribute("max",maximum.Value.ToString(CultureInfo.InvariantCulture));return doc.OuterXml;
        }
        public static int Scalars(string text)
        {
            int count=0;
            for (int i=0;i<text.Length;i++,count++) {
                if (char.IsHighSurrogate(text[i])) { if (++i>=text.Length || !char.IsLowSurrogate(text[i])) throw new Invalid("","E-STU-002"); }
                else if (char.IsLowSurrogate(text[i])) throw new Invalid("","E-STU-002");
            }
            return count;
        }
        private static string Text(string raw,int rawMax,int savedMax,string field,bool required,bool multiline=false)
        {
            raw=raw??"";if (Scalars(raw)>rawMax) throw new Invalid(field,"E-STU-002",rawMax);
            var value=multiline?raw.Replace("\r\n","\n").Replace('\r','\n'):raw;
            foreach (char c in value) if (char.GetUnicodeCategory(c)==UnicodeCategory.Control && !(multiline && c=='\n')) throw new Invalid(field,"E-STU-002",rawMax);
            value=value.Trim();if (value.Length==0) {if(required) throw new Invalid(field,"E-STU-001");return null;}
            if (Scalars(value)>savedMax) throw new Invalid(field,"E-STU-002",savedMax);return value;
        }
        private static string Identifier(string raw,int maximum,string field)
        {
            var value=Text(raw,maximum,maximum,field,true).Normalize(NormalizationForm.FormKC).ToUpperInvariant();
            if (Scalars(value)>maximum || !Regex.IsMatch(value,"^[A-Z0-9][A-Z0-9-]*$",RegexOptions.CultureInvariant)) throw new Invalid(field,"E-STU-003");return value;
        }
        private static string WithoutSpaces(string value) {return new string(value.Where(c=>!char.IsWhiteSpace(c)).ToArray());}
        private static string Kana(string raw)
        {
            var value=Text(raw,36,36,"student_name_kana",true).Normalize(NormalizationForm.FormKC);var b=new StringBuilder();bool space=false;
            foreach (char source in value) {
                if(char.IsWhiteSpace(source)) {space=b.Length>0;continue;}if(space){b.Append(' ');space=false;}
                int c=source;if(c>=0x3041 && c<=0x3096 || c==0x309D || c==0x309E)c+=0x60;
                if (!(c>=0x30A1 && c<=0x30FA || c==0x30FC || c==0x30FB || c==0x30FD || c==0x30FE)) throw new Invalid("student_name_kana","E-STU-004");b.Append((char)c);
            }
            var result=b.ToString();if(Scalars(result)>18)throw new Invalid("student_name_kana","E-STU-002",18);return result;
        }
        private static string Phone(string raw,string field)
        {
            var text=Text(raw,20,20,field,false);if(text==null)return null;text=text.Normalize(NormalizationForm.FormKC);
            var value=new string(text.Where(c=>!char.IsWhiteSpace(c) && c!='-' && c!=0x2010 && c!=0x2011 && c!=0x2212 && c!='(' && c!=')').ToArray());
            if(!Regex.IsMatch(value,@"^(0[0-9]{9,10}|\+[1-9][0-9]{6,14})$",RegexOptions.CultureInvariant))throw new Invalid(field,"E-STU-016");return value;
        }
        private static string Postal(string raw)
        {
            var text=Text(raw,10,10,"postal_code",true).Normalize(NormalizationForm.FormKC);
            var value=new string(text.Where(c=>!char.IsWhiteSpace(c) && c!='-' && c!=0x2010 && c!=0x2011 && c!=0x2212).ToArray());
            if(!Regex.IsMatch(value,"^[0-9]{7}$",RegexOptions.CultureInvariant))throw new Invalid("postal_code","E-STU-015");return value;
        }
        private static string Email(string raw)
        {
            var value=Text(raw,60,60,"email_address",false);if(value==null)return null;var p=value.Split('@');
            if(p.Length!=2 || p[0].Length==0 || p[0].StartsWith(".") || p[0].EndsWith(".") || p[0].Contains("..") || !Regex.IsMatch(p[0],"^[A-Za-z0-9.!#$%&'*+/=?^_\\x60{|}~-]+$",RegexOptions.CultureInvariant))throw new Invalid("email_address","E-STU-017");
            var labels=p[1].Split('.');if(labels.Length<2 || labels.Any(s=>s.Length<1 || s.Length>63 || !Regex.IsMatch(s,"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$",RegexOptions.CultureInvariant)))throw new Invalid("email_address","E-STU-017");
            return p[0]+"@"+p[1].ToLowerInvariant();
        }
        private static string Code(string raw,int width,string field,bool required)
        {
            var value=Text(raw,width,width,field,required);if(value==null)return null;value=value.Normalize(NormalizationForm.FormKC);
            if(value.Length!=width || value.Any(c=>c<'0'||c>'9'))throw new Invalid(field,"E-STU-009");return value;
        }
        private static string SchoolYear(string raw,bool required=false)
        {
            if(raw==null) {if(required)throw new Invalid("school_year","E-DATE-003",4);return null;}
            if(Scalars(raw)>4)throw new Invalid("school_year","E-DATE-003",4);
            raw=raw.Normalize(NormalizationForm.FormKC).Trim();
            if(raw.Length==0) {if(required)throw new Invalid("school_year","E-DATE-003",4);return null;}
            int value;
            // REG-016 / CHK-034: raw scalar limit precedes common NFKC and ASCII yyyy parsing.
            if(raw.Length!=4 || raw.Any(c=>c<'0'||c>'9') || !int.TryParse(raw,NumberStyles.None,CultureInfo.InvariantCulture,out value) || value<1900 || value>9998)
                throw new Invalid("school_year","E-DATE-003",4);
            return raw;
        }
        private static string Id(string raw,string field,long maximum)
        {
            if(string.IsNullOrEmpty(raw))return null;long value;
            if(raw.Length>19 || raw.Any(c=>c<'0'||c>'9') || !long.TryParse(raw,NumberStyles.None,CultureInfo.InvariantCulture,out value) || value<=0 || value>maximum)throw new Invalid(field,field=="school_year"?"E-DATE-003":"E-COM-003");
            return value.ToString(CultureInfo.InvariantCulture);
        }
        private static string Iso(DateTime day) {return day.ToString("yyyy-MM-dd",CultureInfo.InvariantCulture);}
        private static DateTime Date(string raw,string field,DateTime businessDay)
        {
            if(raw==null || Scalars(raw)>10)throw new Invalid(field,"E-STU-005");raw=raw.Normalize(NormalizationForm.FormKC);
            DateTime date;if(!Regex.IsMatch(raw,"^[0-9]{4}-[0-9]{2}-[0-9]{2}$") || !DateTime.TryParseExact(raw,"yyyy-MM-dd",CultureInfo.InvariantCulture,DateTimeStyles.None,out date))throw new Invalid(field,"E-STU-005");
            if(date<new DateTime(1900,1,1) || date>businessDay)throw new Invalid(field,"E-DATE-002");return date.Date;
        }
        private static int Number(string raw,int max)
        {
            if(raw==null || raw.Length==0 || raw.Length>max)throw new Invalid("birth_date","E-DATE-001");var value=raw.Normalize(NormalizationForm.FormKC);
            int n;if(value.Length>max || value.Any(c=>c<'0'||c>'9') || !int.TryParse(value,out n) || n<=0)throw new Invalid("birth_date","E-DATE-001");return n;
        }
        private static DateTime Birth(Dictionary<string,string> raw,DateTime businessDay)
        {
            string era=raw["birth_era"];int offset;DateTime start,end;
            switch(era) {
                case "MEIJI":offset=1867;start=new DateTime(1900,1,1);end=new DateTime(1912,7,29);break;
                case "TAISHO":offset=1911;start=new DateTime(1912,7,30);end=new DateTime(1926,12,24);break;
                case "SHOWA":offset=1925;start=new DateTime(1926,12,25);end=new DateTime(1989,1,7);break;
                case "HEISEI":offset=1988;start=new DateTime(1989,1,8);end=new DateTime(2019,4,30);break;
                case "REIWA":offset=2018;start=new DateTime(2019,5,1);end=DateTime.MaxValue.Date;break;
                default:throw new Invalid("birth_date","E-DATE-001");
            }
            var year=raw["birth_year"]!=null && raw["birth_year"].Normalize(NormalizationForm.FormKC)=="元"?1:Number(raw["birth_year"],4);
            DateTime date;try {date=new DateTime(checked(offset+year),Number(raw["birth_month"],2),Number(raw["birth_day"],2));}catch(ArgumentOutOfRangeException){throw new Invalid("birth_date","E-STU-005");}
            if(date<start || date>end || date>businessDay.Date)throw new Invalid("birth_date","E-DATE-001");return date;
        }
    }
}
