using System.IO.Ports;
using Poten2501.Services;
using Poten2501.ViewModels;
using Windows.ApplicationModel.Calls;
using ScottPlot;
using Microsoft.Maui.Controls;
using Poten2501.CustomControls;
using Poten2501.Models;


namespace Poten2501.Pages;
public partial class CVPage : ContentPage
{
    public CVPage(ISerialPortService serialPortService)
    {
        InitializeComponent();
        BindingContext = new CVViewModel(serialPortService);
        entNoOfCycle.Text = "11";
        //SWeepRateMilliVoltPerSec.Text = "100";  //mVps
        entPointPerSecond.Text = "5";
        //entCurrentRangrAmp.Text = "1";
        entBeginPotentialVolt.Text = "-0.4";
        entLowerPotentialVolt.Text = "-0.4";
        entUpperPotentialVolt.Text = "0.7";
        entIdlePotentialVolt.Text = "0";
        entIdleTimeSecond.Text = "10";
    }

    private void entCurrentGain_SelectedIndexChanged(object sender, EventArgs e)
    {
        string CurrRange = (sender as Picker)?.SelectedItem?.ToString();
        if (BindingContext is CVViewModel viewModel)
        {
            viewModel.UpdateCurrentRangeCommand.Execute(CurrRange);
        }
    }

    protected override void OnAppearing()
    {
        base.OnAppearing();
        if (BindingContext is CVViewModel viewModel)
        {
            viewModel.SubscribeSerialPort();
        }
    }
    protected override void OnDisappearing()
    {
        base.OnDisappearing();
        if (BindingContext is CVViewModel viewModel)
        {
            viewModel.UnsubscribeSerialPort();
        }
    }
}
