using System.Globalization;
using System.Text;

namespace StudentManagement.Core;

// COM-STU-007 DATE-R01..06; explicit era boundaries, independent of OS calendar.
public static class JapaneseDateService
{
    private sealed record Era(string Id, string Name, int Offset, DateOnly Start, DateOnly End);
    private static readonly Era[] Eras = [
        new("REIWA", "令和", 2018, new(2019,5,1), DateOnly.MaxValue),
        new("HEISEI", "平成", 1988, new(1989,1,8), new(2019,4,30)),
        new("SHOWA", "昭和", 1925, new(1926,12,25), new(1989,1,7)),
        new("TAISHO", "大正", 1911, new(1912,7,30), new(1926,12,24)),
        new("MEIJI", "明治", 1867, new(1900,1,1), new(1912,7,29))
    ];
    public static DateOnly Parse(BirthDateInput input, DateOnly businessDay)
    {
        var era = Eras.SingleOrDefault(era => era.Id == input.Era);
        if (era is null) throw new ArgumentException("E-DATE-001: 生年月日の元号を確認してください。");
        var yearText = input.Year.Normalize(NormalizationForm.FormKC);
        var year = yearText == "元" ? 1 : Number(yearText, 4);
        var month = Number(input.Month.Normalize(NormalizationForm.FormKC), 2);
        var day = Number(input.Day.Normalize(NormalizationForm.FormKC), 2);
        DateOnly date;
        try { date = new(checked(era.Offset + year), month, day); }
        catch (ArgumentOutOfRangeException) { throw new ArgumentException("E-STU-005: 生年月日に正しい日付を入力してください。"); }
        if (date < era.Start || date > era.End || date > businessDay)
            throw new ArgumentException("E-DATE-001: 生年月日の元号・年・月・日を確認してください。");
        var reverse = ToInput(date);
        if (reverse.Era != input.Era || int.Parse(reverse.Year, CultureInfo.InvariantCulture) != year)
            throw new ArgumentException("E-DATE-001: 元号境界が一致しません。");
        return date;
    }
    private static int Number(string text, int maximum)
    {
        if (text.Length is 0 || text.Length > maximum || text.Any(c => c < '0' || c > '9') || !int.TryParse(text, out var value) || value <= 0)
            throw new ArgumentException("E-DATE-001: 正の整数を入力してください。");
        return value;
    }
    public static BirthDateInput ToInput(DateOnly date)
    {
        var era = Eras.FirstOrDefault(era => date >= era.Start && date <= era.End)
            ?? throw new ArgumentOutOfRangeException(nameof(date), "DATE-R01下限外です。");
        return new(era.Id, (date.Year - era.Offset).ToString(CultureInfo.InvariantCulture), date.Month.ToString("00"), date.Day.ToString("00"));
    }
    public static string ToWareki(DateOnly date)
    {
        var input = ToInput(date);
        return $"{Eras.Single(era => era.Id == input.Era).Name}{(input.Year == "1" ? "元" : input.Year)}年{input.Month}月{input.Day}日";
    }
    public static DateOnly ParseIso(string raw, DateOnly businessDay, bool historical = true)
    {
        var text = raw.Normalize(NormalizationForm.FormKC);
        if (text.Length != 10 || !DateOnly.TryParseExact(text, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var date))
            throw new ArgumentException("E-STU-005: 正しい西暦日付を入力してください。");
        if (date < new DateOnly(1900, 1, 1) || historical && date > businessDay)
            throw new ArgumentException("E-DATE-002: 日付が許容範囲外です。");
        return date;
    }
    public static int SchoolYear(DateOnly day) => day.Month < 4 ? day.Year - 1 : day.Year;
}
