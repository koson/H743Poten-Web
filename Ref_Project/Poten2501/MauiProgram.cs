using Microsoft.Extensions.Logging;
using ScottPlot.Maui;
using Poten2501.Services;
using Poten2501.Pages;
using Poten2501.Models;
using SkiaSharp.Views.Maui.Controls.Hosting;
using CommunityToolkit.Maui;
//using Poten2501.Platforms.Windows.Services;

namespace Poten2501
{
    public static class MauiProgram
    {
        public static MauiApp CreateMauiApp()
        {
            var builder = MauiApp.CreateBuilder();
            builder
                .UseMauiApp<App>()
                .UseMauiCommunityToolkit()
                .UseScottPlot()
                .UseSkiaSharp()
                .ConfigureFonts(fonts =>
                {
                    fonts.AddFont("OpenSans-Regular.ttf", "OpenSansRegular");
                    fonts.AddFont("OpenSans-Semibold.ttf", "OpenSansSemibold");
                });

#if DEBUG
    		builder.Logging.AddDebug();
#endif
            // Register the Windows serial port service
            builder.Services.AddSingleton<ISerialPortService, Poten2501.Platforms.Windows.Services.WindowsSerialPortService>();
            builder.Services.AddSingleton<MainPage>();
            builder.Services.AddSingleton<CVPage>();
            builder.Services.AddSingleton<DPVPage>();
            builder.Services.AddSingleton<CAPage>();
            builder.Services.AddSingleton<SWVPage>();

            return builder.Build();
        }
    }
}
