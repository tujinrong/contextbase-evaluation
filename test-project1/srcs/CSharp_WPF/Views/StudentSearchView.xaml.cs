using System.Windows;
namespace StudentManagement.Wpf.Views;
public partial class StudentSearchView : Window
{
    public StudentSearchView() => InitializeComponent();
    private void MenuClick(object sender, RoutedEventArgs e) => Close();
}
