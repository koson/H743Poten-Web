using Poten2501.Services;
using Poten2501.ViewModels;

namespace Poten2501
{
    public partial class MainPage : ContentPage
    {
 

        public MainPage(ISerialPortService serialPortService)
        {
            InitializeComponent();
            BindingContext = new MainPageViewModel(serialPortService);
        }

 
    }

}
