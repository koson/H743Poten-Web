using Poten2501.Services;
using Poten2501.ViewModels;
using ScottPlot.WPF;

namespace Poten2501.Pages;

public partial class CAPage : ContentPage
{
	public CAPage(ISerialPortService serialPortService)
    {
        InitializeComponent();

        BindingContext = new CAViewModel(CAPlot, serialPortService);
    }
    private void entCurrentGain_SelectedIndexChanged(object sender, EventArgs e)
    {
        string CurrRange = (sender as Picker)?.SelectedItem?.ToString();
        if (BindingContext is CAViewModel viewModel)
        {
            viewModel.UpdateCurrentRangeCommand.Execute(CurrRange);
        }
    }
}