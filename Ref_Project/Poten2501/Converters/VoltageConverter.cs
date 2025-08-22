using System.Diagnostics;
using System.Globalization;
namespace Poten2501.Converters
{
    public class VoltageConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            //Debug.WriteLine($"VoltageConverter called with value: {value}");

            if (value is double voltage)
            {
                return $"{voltage:F4} V";
            }
            return value;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }

    public class CurrentConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is double current)
            {
                if (Math.Abs(current) >= 1)
                {
                    return $"{current:F4} A";
                }
                else if (Math.Abs(current) >= 0.001)
                {
                    return $"{current * 1000:F4} mA";
                }
                else if (Math.Abs(current) >= 0.000001)
                {
                    return $"{current * 1000000:F4} uA";
                }
                else
                {
                    return $"{current * 1000000000:F4} nA";
                }
            }
            return value;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }

}
