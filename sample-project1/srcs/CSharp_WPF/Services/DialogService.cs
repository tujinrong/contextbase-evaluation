using System.Windows;
using System.Windows.Controls;

namespace StudentManagement.Wpf.Services;

public sealed class DialogService
{
    public bool Discard(string message) => MessageBox.Show(message, "確認", MessageBoxButton.OKCancel, MessageBoxImage.Question, MessageBoxResult.Cancel) == MessageBoxResult.OK;
    public string? DeleteReason() => ReasonDialog("W-STU-105 この学生を論理削除します。削除後は通常検索できません。", "削除理由（60文字以内）", "論理削除する");
    public string? ConfirmDuplicate(SaveResult result)
    {
        var content = $"同一人物候補 {result.CandidateCount}件。表示は最大20件です。\n" + string.Join("\n", (result.Candidates ?? []).Select(x => $"{x.StudentNo}  {x.StudentName}  {x.BirthDateWareki}  {x.ClassName}"));
        return ReasonDialog(content, "別人確認の理由（60文字以内）", "別人と確認して続行");
    }
    private static string? ReasonDialog(string content, string prompt, string accept)
    {
        var dialog = new Window { Title = "確認", Owner = Application.Current.Windows.OfType<Window>().FirstOrDefault(x => x.IsActive), Width = 620, Height = 440, WindowStartupLocation = WindowStartupLocation.CenterOwner };
        var panel = new StackPanel { Margin = new Thickness(18) };
        panel.Children.Add(new TextBox { Text = content, IsReadOnly = true, TextWrapping = TextWrapping.Wrap, VerticalScrollBarVisibility = ScrollBarVisibility.Auto, Height = 235 });
        panel.Children.Add(new TextBlock { Text = prompt });
        var reason = new TextBox { MaxLength = 120, AcceptsReturn = true, Height = 55 }; panel.Children.Add(reason);
        string? answer = null;
        var buttons = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };
        var cancel = new Button { Content = "取消", IsCancel = true, IsDefault = true };
        var ok = new Button { Content = accept };
        ok.Click += (_, _) => { if (string.IsNullOrWhiteSpace(reason.Text) || reason.Text.EnumerateRunes().Count() > 60) { MessageBox.Show("理由を60文字以内で入力してください。"); return; } answer = reason.Text; dialog.DialogResult = true; };
        buttons.Children.Add(cancel); buttons.Children.Add(ok); panel.Children.Add(buttons); dialog.Content = panel; dialog.ShowDialog(); return answer;
    }
}
