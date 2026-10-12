using System.Windows;
using System.Windows.Controls;
using StudentManagement.Wpf.ViewModels;
namespace StudentManagement.Wpf.Views;
public partial class StudentEditView : Window
{
    private bool refreshing;
    public StudentEditView() => InitializeComponent();
    private void ClassChanged(object sender, SelectionChangedEventArgs e) { if (refreshing || !IsLoaded) return; refreshing = true; try { (DataContext as StudentEditViewModel)?.SelectClass(); } finally { refreshing = false; } }
}
