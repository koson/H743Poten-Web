using Poten2501.Models;
using Poten2501.Services;
using Poten2501.ViewModels;
using ScottPlot;
using ScottPlot.Maui;

namespace Poten2501.Pages;

public partial class DPVPage : ContentPage
{
    private MauiPlot myPlot;
    public DPVPage(ISerialPortService serialPortService)
    {
        
        InitializeComponent();
        BindingContext = new DPVPageViewModel(DPVPlot, serialPortService);
        InitializeDefaultValues();
        myPlot = DPVPlot._mauiPlot;
    }

    private void InitializeDefaultValues()
    {
        if (BindingContext is DPVPageViewModel viewModel)
        {
            entNoOfSegments.Text = "1";
            entScanRate.Text = "0.1";                           // Volt per second
            entInitialPotentialVolt.Text = "-0.2";              // Volt
            entFinalPotentialVolt.Text = "0.5";                 // Volt
            entInitialPotentialVolt.Text = "-0.5";              // Volt
            entFinalPotentialVolt.Text = "0.5";                 // Volt
            entLowerPotentialVolt.Text = "0.0";                 // Volt
            entUpperPotentialVolt.Text = "0.0";                 // Volt
            entDifferentialPulseHeight.Text = "0.050";          // Volt
            entDifferentialPulseWidth.Text = "0.050";           // SEC
            entDifferentialPulsePeriod.Text = "0.1";            // SEC
            entDifferentialPulseIncrement.Text = "0.010";       // Volt
            entDifferentialPulsePrePulseWidth.Text = "0.0";     // SEC
            entDifferentialPulsePostPulseWidth.Text = "0.0";    // SEC
            viewModel = EnableEntries(viewModel, true);

        }
    }

    private static DPVPageViewModel EnableEntries(DPVPageViewModel viewModel, bool value)
    {
        viewModel.IsEntryNoOfSegmentsEnabled = value;
        viewModel.IsEntryInitialPotentialVoltEnabled = value;
        viewModel.IsEntryFinalPotentialVoltEnabled = value;
        viewModel.IsEntryLowerPotentialVoltEnabled = value;
        viewModel.IsEntryUpperPotentialVoltEnabled = value;
        viewModel.IsEntryDifferentialPulseHeightEnabled = value;
        viewModel.IsEntryDifferentialPulseWidthEnabled = value;
        viewModel.IsEntryDifferentialPulsePeriodEnabled = value;
        viewModel.IsEntryDifferentialPulseIncrementEnabled = value;
        viewModel.IsEntryDifferentialPulsePrePulseWidthEnabled = value;
        viewModel.IsEntryDifferentialPulsePostPulseWidthEnabled = value;
        return viewModel;
    }

    private void Entry_Completed(object sender, EventArgs e)
    {
        if (sender is Entry entry && BindingContext is DPVPageViewModel viewModel)
        {
            switch (entry.StyleId)
            {
                case nameof(viewModel.NoOfSegments):
                    viewModel.NoOfSegments = entry.Text;
                    viewModel.UpdateNoOfSegmentsCommand.Execute(null);
                    break;
                case nameof(viewModel.InitialPotentialVolt):
                    viewModel.InitialPotentialVolt = entry.Text;
                    viewModel.UpdateInitialPotentialVoltCommand.Execute(null);
                    break;
                case nameof(viewModel.FinalPotentialVolt):
                    viewModel.FinalPotentialVolt = entry.Text;
                    viewModel.UpdateFinalPotentialVoltCommand.Execute(null);
                    break;
                case nameof(viewModel.LowerPotentialVolt):
                    viewModel.LowerPotentialVolt = entry.Text;
                    viewModel.UpdateLowerPotentialVoltCommand.Execute(null);
                    break;
                case nameof(viewModel.UpperPotentialVolt):
                    viewModel.UpperPotentialVolt = entry.Text;
                    viewModel.UpdateUpperPotentialVoltCommand.Execute(null);
                    break;
                case nameof(viewModel.DifferentialPulseHeight):
                    viewModel.DifferentialPulseHeight = entry.Text;
                    viewModel.UpdateDifferentialPulseHeightCommand.Execute(null);
                    break;
                case nameof(viewModel.DifferentialPulseWidth):
                    viewModel.DifferentialPulseWidth = entry.Text;
                    viewModel.UpdateDifferentialPulseWidthCommand.Execute(null);
                    break;
                case nameof(viewModel.DifferentialPulsePeriod):
                    viewModel.DifferentialPulsePeriod = entry.Text;
                    viewModel.UpdateDifferentialPulsePeriodCommand.Execute(null);
                    break;
                case nameof(viewModel.DifferentialPulseIncrement):
                    viewModel.DifferentialPulseIncrement = entry.Text;
                    viewModel.UpdateDifferentialPulseIncrementCommand.Execute(null);
                    break;
                case nameof(viewModel.DifferentialPulsePrePulseWidth):
                    viewModel.DifferentialPulsePrePulseWidth = entry.Text;
                    viewModel.UpdateDifferentialPulsePrePulseWidthCommand.Execute(null);
                    break;
                case nameof(viewModel.DifferentialPulsePostPulseWidth):
                    viewModel.DifferentialPulsePostPulseWidth = entry.Text;
                    viewModel.UpdateDifferentialPulsePostPulseWidthCommand.Execute(null);
                    break;
            }
        }
    }

    private void entCurrentGain_SelectedIndexChanged(object sender, EventArgs e)
    {
        string CurrRange = (sender as Picker)?.SelectedItem?.ToString();
        if (BindingContext is DPVPageViewModel viewModel)
        {
            viewModel.UpdateCurrentRangeCommand.Execute(CurrRange);
        }
    }
}


/* references
 * https://pineresearch.com/shop/kb/software/methods-and-techniques/voltammetric-methods/differential-pulse-voltammetry-dpv/
 */