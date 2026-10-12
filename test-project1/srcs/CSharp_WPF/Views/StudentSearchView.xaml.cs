using System.Windows;
using System.Windows.Controls;
using StudentManagement.Wpf.ViewModels;
namespace StudentManagement.Wpf.Views;
public partial class StudentSearchView : Window
{
    private bool refreshing;
    public StudentSearchView() => InitializeComponent();
    private void FilterChanged(object sender, SelectionChangedEventArgs e) { if (refreshing || !IsLoaded) return; refreshing = true; try { (DataContext as StudentSearchViewModel)?.RefreshClasses(); } finally { refreshing = false; } }
    private void ClassChanged(object sender, SelectionChangedEventArgs e) { if (!refreshing && IsLoaded) (DataContext as StudentSearchViewModel)?.SelectClass(); }
    private void UnassignedChanged(object sender, RoutedEventArgs e) { if (IsLoaded) (DataContext as StudentSearchViewModel)?.RefreshClasses(); }
    private void MenuClick(object sender, RoutedEventArgs e) => Close();
}
