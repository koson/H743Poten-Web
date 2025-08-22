using Poten2501.Services;
using Poten2501.ViewModels;
using ScottPlot;
using ScottPlot.Maui;
using ScottPlot.WPF;
using System.Diagnostics;

namespace Poten2501.Pages;

public partial class SWVPage : ContentPage
{
    private MauiPlot swvPlot;
    public SWVPage(ISerialPortService serialPortService)
    {
        InitializeComponent();
        var viewModel = new SWVViewModel(SWVPlot, serialPortService);
        swvPlot = SWVPlot._mauiPlot;
        BindingContext = viewModel;
    }
    private void pickerFrequency_SelectedIndexChanged(object sender, EventArgs e)
    {
        Debug.WriteLine($"pickerFrequency_SelectedIndexChanged() = {pickerFrequency.SelectedItem}");
    }

    protected override void OnAppearing()
    {
        base.OnAppearing();
        if (BindingContext is SWVViewModel viewModel)
        {
            viewModel.SubscribeSerialPort();
        }
    }
    protected override void OnDisappearing()
    {
        base.OnDisappearing();
        if (BindingContext is SWVViewModel viewModel)
        {
            viewModel.UnsubscribeSerialPort();
        }
    }

}