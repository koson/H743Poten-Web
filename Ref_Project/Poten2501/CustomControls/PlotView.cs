using ScottPlot.Maui;
using SkiaSharp.Views.Maui;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Input;

namespace Poten2501.CustomControls
{
    public class PlotView : ContentView
    {
        public static readonly BindableProperty DataXProperty = BindableProperty.Create(
            nameof(DataX), typeof(double[]), typeof(PlotView), null, propertyChanged: OnDataChanged);

        public double[] DataX
        {
            get => (double[])GetValue(DataXProperty);
            set => SetValue(DataXProperty, value);
        }

        public static readonly BindableProperty DataYProperty = BindableProperty.Create(
            nameof(DataY), typeof(double[]), typeof(PlotView), null, propertyChanged: OnDataChanged);

        public double[] DataY
        {
            get => (double[])GetValue(DataYProperty);
            set => SetValue(DataYProperty, value);
        }

        public static readonly BindableProperty AdditionalDataXProperty = BindableProperty.Create(
            nameof(AdditionalDataX), typeof(double[][]), typeof(PlotView), null, propertyChanged: OnDataChanged);

        public double[][] AdditionalDataX
        {
            get => (double[][])GetValue(AdditionalDataXProperty);
            set => SetValue(AdditionalDataXProperty, value);
        }

        public static readonly BindableProperty AdditionalDataYProperty = BindableProperty.Create(
            nameof(AdditionalDataY), typeof(double[][]), typeof(PlotView), null, propertyChanged: OnDataChanged);

        public double[][] AdditionalDataY
        {
            get => (double[][])GetValue(AdditionalDataYProperty);
            set => SetValue(AdditionalDataYProperty, value);
        }

        public MauiPlot _mauiPlot;
        public static readonly BindableProperty PointSizeProperty = BindableProperty.Create(
            nameof(PointSize), typeof(double), typeof(PlotView), 1.0, propertyChanged: OnDataChanged);

        public void Clear()
        {
            _mauiPlot.Plot.Clear();
            _mauiPlot.Refresh();
        }

        public MauiPlot Plot => _mauiPlot;

        public double PointSize
        {
            get => (double)GetValue(PointSizeProperty);
            set => SetValue(PointSizeProperty, value);
        }

        private static void OnDataChanged(BindableObject bindable, object oldValue, object newValue)
        {
            if (bindable is PlotView plotView && plotView._mauiPlot != null)
            {
                plotView.UpdatePlot();
            }
        }

        // Removed the line that references the non-existent 'Configuration' property
        // and replaced it with a comment to indicate the issue.

        public PlotView()
        {
            _mauiPlot = new MauiPlot();
            _mauiPlot.Margin = new Thickness(0, 10, 0, 0); // Add 10 pixels margin at the top
            Content = _mauiPlot;


            // Subscribe to the Touch event
            _mauiPlot.Touch += OnTouch;
        }

        private void OnTouch(object sender, SKTouchEventArgs e)
        {
            // Log the touch event details
           // Debug.WriteLine($"Touch event detected: {e.ActionType}");

            // Example: Detect zoom gesture
            if (e.ActionType == SKTouchAction.Pressed) // Corrected to use SKTouchAction
            {
                if (e.MouseButton == SKMouseButton.Right)
                {
             //       Debug.WriteLine("Right-click detected. Applying AutoScale.");
                    _mauiPlot.Plot.Axes.AutoScale(); // Apply AutoScale
                    _mauiPlot.Refresh(); // Refresh the plot
                    e.Handled = true; // Mark the event as handled
                    return;
                }
                else
                {
               //     Debug.WriteLine("Pinch gesture detected (zooming).");
                    _isUserZooming = true; // Set the zooming flag
                }
            }
            else if (e.ActionType == SKTouchAction.Moved) // Corrected to use SKTouchAction
            {
                //Debug.WriteLine("Pan gesture detected.");
            }
            else if (e.ActionType == SKTouchAction.Released) // Corrected to use SKTouchAction
            {
                //Debug.WriteLine("Touch released.");
            }
        }

        private bool _isUserZooming = false;

 

        private void UpdatePlot()
        {
            _mauiPlot.Plot.Clear(); // Clear existing plot

            // Plot the main data series
            if (DataX != null && DataY != null && DataX.Length == DataY.Length)
            {
                var sp = _mauiPlot.Plot.Add.Scatter(DataX, DataY);
                //sp.Smooth = true;
                sp.MarkerSize = (float)PointSize; // Set point size
                sp.LineWidth = 2; // Set line width
            }

            // Plot additional data series
            if (AdditionalDataX != null && AdditionalDataY != null && AdditionalDataX.Length == AdditionalDataY.Length)
            {
                for (int i = 0; i < AdditionalDataX.Length; i++)
                {
                    if (AdditionalDataX[i] != null && AdditionalDataY[i] != null && AdditionalDataX[i].Length == AdditionalDataY[i].Length)
                    {
                        var sp = _mauiPlot.Plot.Add.Scatter(AdditionalDataX[i], AdditionalDataY[i]);
                        //sp.Smooth = true;
                        sp.MarkerSize = (float)PointSize; // Set point size
                    }
                }
            }

            // Apply auto-scaling only if the user has not zoomed
            if (!_isUserZooming)
            {
                _mauiPlot.Plot.Axes.AutoScale();
            }

            _mauiPlot.Refresh();
        }
    }
}
