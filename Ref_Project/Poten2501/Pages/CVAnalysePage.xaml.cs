using Poten2501.ViewModels;
using System.Diagnostics;
namespace Poten2501.Pages;

public partial class CVAnalysePage : ContentPage
{
	public CVAnalysePage()
	{
		InitializeComponent();
        BindingContext = new CVAnalyzeViewModel(PlotView);
        if (BindingContext is CVAnalyzeViewModel viewModel)
        {
            viewModel.CathodicBaselineStart = 0.3;
            viewModel.AnodicBaselineStart = viewModel.AnodicBaselineEnd - 0.1;
            viewModel.CathodicBaselineEnd = viewModel.CathodicBaselineStart - 0.1;
            AnodicBaselineStartLabel.Text = viewModel.AnodicBaselineStart.ToString("F3") + "V";
            AnodicBaselineEndLabel.Text = viewModel.AnodicBaselineEnd.ToString("F3") + "V";
            CathodicBaselineStartLabel.Text = viewModel.CathodicBaselineStart.ToString("F3") + "V";
            CathodicBaselineEndLabel.Text = viewModel.CathodicBaselineEnd.ToString("F3") + "V";
        }
    }

    private void OnAnodicPeakLocationChanged(object sender, ValueChangedEventArgs e)
    {
        if (BindingContext is CVAnalyzeViewModel viewModel)
        {
            viewModel.AnodicPeakLocation = e.NewValue / 1000.0;

            if (viewModel.VoltammogramData != null)
                viewModel.PlotVoltammogramData();

            //Debug.WriteLine($"Anodic Peak Voltage: {viewModel.AnodicPeakLocation:F3} V");
            AnodicPeakLabel.Text = $"{viewModel.AnodicPeakLocation:F3} V";

            if (viewModel.AnodicPeakCurrent.HasValue)
            {
                //Debug.WriteLine($"Anodic Peak Current: {viewModel.AnodicPeakCurrent.Value:E3} A");
                AnodicPeakLabel.Text = $"{viewModel.AnodicPeakLocation:F3} V, {viewModel.AnodicPeakCurrent.Value:E3} A";
            }
        }
    }
    private void OnAnodicBaselineStartChanged(object sender, ValueChangedEventArgs e)
    {
        if (BindingContext is CVAnalyzeViewModel viewModel)
        {
            viewModel.AnodicBaselineStart = e.NewValue / 1000.0;
            if (viewModel.AnodicBaselineStart > viewModel.AnodicBaselineEnd)
                viewModel.AnodicBaselineEnd = viewModel.AnodicBaselineStart + 0.1;
            if (viewModel.VoltammogramData != null)
                viewModel.PlotVoltammogramData();
            AnodicBaselineStartLabel.Text = viewModel.AnodicBaselineStart.ToString("F3") + "V";
            if (viewModel.AnodicBaselineStartCurrent.HasValue)
            {
                //Debug.WriteLine($"Anodic Peak Current: {viewModel.AnodicBaselineStart:F3} A");
                AnodicBaselineStartLabel.Text = $"{viewModel.AnodicBaselineStart:F3} V, {viewModel.AnodicBaselineStartCurrent.Value:E3} A";
            }
        }
    }
    private void OnAnodicBaselineEndChanged(object sender, ValueChangedEventArgs e)
    {
        if (BindingContext is CVAnalyzeViewModel viewModel)
        {
            viewModel.AnodicBaselineEnd = e.NewValue / 1000.0;
            if (viewModel.AnodicBaselineStart > viewModel.AnodicBaselineEnd)
                viewModel.AnodicBaselineStart = viewModel.AnodicBaselineEnd + 0.1;
            if (viewModel.VoltammogramData != null)
                viewModel.PlotVoltammogramData();
            AnodicBaselineEndLabel.Text = viewModel.AnodicBaselineEnd.ToString("F3") + "V";
            if(viewModel.AnodicBaselineEndCurrent.HasValue)
            {
                //Debug.WriteLine($"Anodic Peak Current: {viewModel.AnodicBaselineEnd:E3} A");
                AnodicBaselineEndLabel.Text = $"{viewModel.AnodicBaselineEnd:F3} V, {viewModel.AnodicBaselineEndCurrent.Value:E3} A";
            }
        }
    }
    private void OnCathodicPeakLocationChanged(object sender, ValueChangedEventArgs e)
    {
        if (BindingContext is CVAnalyzeViewModel viewModel)
        {
            viewModel.CathodicPeakLocation = e.NewValue / 1000.0;
            if (viewModel.VoltammogramData != null)
                viewModel.PlotVoltammogramData();

            CathodicPeakLabel.Text = $"{viewModel.CathodicPeakLocation:F3} V";
            if(viewModel.CathodicPeakCurrent.HasValue)
            {
                //Debug.WriteLine($"Cathodic Peak Current: {viewModel.CathodicPeakCurrent.Value:E3} A");
                CathodicPeakLabel.Text = $"{viewModel.CathodicPeakLocation:F3} V, {viewModel.CathodicPeakCurrent.Value:E3} A";
            }

        }
    }

    private void OnCathodicBaselineStartChanged(object sender, ValueChangedEventArgs e)
    {
        if (BindingContext is CVAnalyzeViewModel viewModel)
        {
            viewModel.CathodicBaselineStart = e.NewValue / 1000.0;
            if (viewModel.CathodicBaselineStart < viewModel.CathodicBaselineEnd)
                viewModel.CathodicBaselineEnd = viewModel.CathodicBaselineStart - 0.1;
            CathodicBaselineStartLabel.Text = viewModel.CathodicBaselineStart.ToString("F3") + "V";

            if (viewModel.VoltammogramData != null)
                viewModel.PlotVoltammogramData();
        }
    }
    private void OnCathodicBaselineEndChanged(object sender, ValueChangedEventArgs e)
    {
        if (BindingContext is CVAnalyzeViewModel viewModel)
        {
            viewModel.CathodicBaselineEnd = e.NewValue / 1000.0;
            if (viewModel.CathodicBaselineStart < viewModel.CathodicBaselineEnd)
                viewModel.CathodicBaselineStart = viewModel.CathodicBaselineEnd + 0.1;
            CathodicBaselineEndLabel.Text = viewModel.CathodicBaselineEnd.ToString("F3") + "V";
            if (viewModel.VoltammogramData != null)
                viewModel.PlotVoltammogramData();
        }
    }
}