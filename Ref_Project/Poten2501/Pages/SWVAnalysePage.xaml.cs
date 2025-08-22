using Poten2501.ViewModels;

namespace Poten2501.Pages;

public partial class SWVAnalysePage : ContentPage
{
	public SWVAnalysePage()
	{
		InitializeComponent();
        BindingContext = new SWVAnalyseViewModel(PlotView);
    }
}