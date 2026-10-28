using System.Windows;
using System.Windows.Controls;
using StudentManagement.Wpf.ViewModels;
namespace StudentManagement.Wpf.Views;
public partial class StudentEditView : Window
{
    private bool refreshing;
    private (UIElement Label, UIElement Value)[] basicFields = [];
    public StudentEditView()
    {
        InitializeComponent();
        basicFields = BasicGrid.Children.Cast<UIElement>().Chunk(2).Select(pair => (pair[0], pair[1])).ToArray();
        foreach (var container in EditorColumns.Children.OfType<UserControl>())
            foreach (var group in ((StackPanel)container.Content).Children.OfType<GroupBox>())
                if (group.Content is Grid fields)
                {
                    fields.ColumnDefinitions[0].Width = new GridLength(92);
                    var rows = fields.Children.Cast<UIElement>().Max(Grid.GetRow) + 1;
                    while (fields.RowDefinitions.Count < rows) fields.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto, MinHeight = 38 });
                    foreach (var value in fields.Children.OfType<FrameworkElement>().Where(child => Grid.GetColumn(child) == 1)) value.Margin = new Thickness(5,2,0,2);
                }
        Loaded += (_, _) => ReflowFields();
    }
    private void Reflow(object sender, SizeChangedEventArgs e) => ReflowFields();
    private void ReflowFields()
    {
        if (basicFields.Length == 0) return;
        var width = Math.Max(0, ActualWidth - 40);
        var columns = width >= 1120 ? 3 : width >= 800 ? 2 : 1;
        BasicGrid.ColumnDefinitions.Clear(); BasicGrid.RowDefinitions.Clear();
        for (var column = 0; column < columns; column++)
        {
            BasicGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(92) });
            BasicGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        }
        for (var row = 0; row < (basicFields.Length + columns - 1) / columns; row++) BasicGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto, MinHeight = 38 });
        for (var index = 0; index < basicFields.Length; index++)
        {
            var (label, value) = basicFields[index];
            Grid.SetRow(label, index / columns); Grid.SetColumn(label, index % columns * 2);
            Grid.SetRow(value, index / columns); Grid.SetColumn(value, index % columns * 2 + 1);
            ((FrameworkElement)value).Margin = new Thickness(5,2,index % columns == columns - 1 ? 0 : 12,2);
        }
        EditorColumns.ColumnDefinitions.Clear(); EditorColumns.RowDefinitions.Clear();
        for (var column = 0; column < columns; column++) EditorColumns.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1,GridUnitType.Star) });
        for (var row = 0; row < (EditorColumns.Children.Count + columns - 1) / columns; row++) EditorColumns.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        for (var index = 0; index < EditorColumns.Children.Count; index++)
        {
            var child = (FrameworkElement)EditorColumns.Children[index];
            Grid.SetColumn(child,index % columns); Grid.SetRow(child,index / columns);
            child.Margin = new Thickness(0,0,index % columns == columns - 1 ? 0 : 7,0);
        }
    }
    private void ClassChanged(object sender, SelectionChangedEventArgs e) { if (refreshing || !IsLoaded) return; refreshing = true; try { (DataContext as StudentEditViewModel)?.SelectClass(); } finally { refreshing = false; } }
}
