using System.Windows.Input;

namespace StudentManagement.Wpf.Commands;

// COM-CSharp_WPF / UI-13: ICommand.Execute is the only async void boundary.
public sealed class AsyncCommand(Func<object?, Task> execute, Func<bool>? canExecute = null, Action<Exception>? onError = null) : ICommand
{
    public bool IsRunning { get; private set; }
    public event EventHandler? CanExecuteChanged;
    public bool CanExecute(object? parameter) => !IsRunning && (canExecute?.Invoke() ?? true);
    public async void Execute(object? parameter)
    {
        if (!CanExecute(parameter)) return;
        IsRunning = true; RaiseCanExecuteChanged();
        try { await execute(parameter); }
        catch (OperationCanceledException) { }
        catch (Exception ex) { onError?.Invoke(ex); }
        finally { IsRunning = false; RaiseCanExecuteChanged(); }
    }
    public void RaiseCanExecuteChanged() => CanExecuteChanged?.Invoke(this, EventArgs.Empty);
}
