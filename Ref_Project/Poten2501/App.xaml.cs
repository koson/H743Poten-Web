using Poten2501.Pages;
using Poten2501.Services;

namespace Poten2501
{
    public partial class App : Application
    {
        public App()
        {
 
            InitializeComponent();

            MainPage = new AppShell();
            //MainPage = new NavigationPage(new CVRealTimeDataPage());
        }
        protected override Window CreateWindow(IActivationState activationState)
        {
            Window window = base.CreateWindow(activationState);

            if (window != null)
            {
                window.Title = "Poten App";
            }

            return window;
        }
    }
}
