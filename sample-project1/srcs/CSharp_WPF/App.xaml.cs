using System.Windows;
using StudentManagement.Wpf.Services;
using StudentManagement.Wpf.Views;
using StudentManagement.Wpf.ViewModels;

namespace StudentManagement.Wpf;

public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        try
        {
            var gateway = StudentGateway.Create();
            var navigation = new NavigationService(gateway);
            var vm = new StudentSearchViewModel(gateway, navigation);
            var view = new StudentSearchView { DataContext = vm };
            MainWindow = view;
            view.Closed += (_, _) => vm.Dispose();
            view.Loaded += async (_, _) => await vm.InitializeAsync();
            view.Show();
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex is InvalidOperationException ? ex.Message : "起動設定を確認してください。", "学生管理", MessageBoxButton.OK, MessageBoxImage.Error);
            Shutdown(1);
        }
    }
}
