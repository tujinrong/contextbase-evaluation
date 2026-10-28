using System.Windows;
using StudentManagement.Wpf.ViewModels;
using StudentManagement.Wpf.Views;

namespace StudentManagement.Wpf.Services;

public sealed class NavigationService(IStudentGateway gateway)
{
    public async Task<string> OpenEditorAsync(long? id)
    {
        var vm = new StudentEditViewModel(gateway, new DialogService(), id);
        var view = new StudentEditView { DataContext = vm, Owner = Application.Current.MainWindow };
        vm.CloseRequested = view.Close;
        view.Closing += (_, e) => e.Cancel = !vm.CanClose();
        view.Closed += (_, _) => vm.Dispose();
        view.Loaded += async (_, _) => await vm.InitializeAsync();
        view.ShowDialog();
        return await Task.FromResult(vm.ResultNotice);
    }
}
