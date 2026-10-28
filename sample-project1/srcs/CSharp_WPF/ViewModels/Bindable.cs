using System.Collections;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace StudentManagement.Wpf.ViewModels;

public abstract class Bindable : INotifyPropertyChanged, INotifyDataErrorInfo
{
    private readonly Dictionary<string, string[]> errors = [];
    public event PropertyChangedEventHandler? PropertyChanged;
    public event EventHandler<DataErrorsChangedEventArgs>? ErrorsChanged;
    public bool HasErrors => errors.Count > 0;
    public IEnumerable GetErrors(string? propertyName) => propertyName is null ? errors.Values.SelectMany(x => x) : errors.GetValueOrDefault(propertyName) ?? [];
    protected void Changed([CallerMemberName] string? name = null) => PropertyChanged?.Invoke(this, new(name));
    protected bool Set<T>(ref T field, T value, [CallerMemberName] string? name = null)
    {
        if (EqualityComparer<T>.Default.Equals(field, value)) return false;
        field = value; Changed(name); return true;
    }
    public void SetError(string property, params string[] messages)
    {
        if (messages.Length == 0) errors.Remove(property); else errors[property] = messages;
        ErrorsChanged?.Invoke(this, new(property)); Changed(nameof(HasErrors));
    }
    public void ClearErrors()
    {
        var fields = errors.Keys.ToArray(); errors.Clear();
        foreach (var field in fields) ErrorsChanged?.Invoke(this, new(field));
        Changed(nameof(HasErrors));
    }
}
