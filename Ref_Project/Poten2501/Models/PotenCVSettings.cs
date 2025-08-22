using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Poten2501.Models
{
    public class PotenCVSettings
    {
        public double MinVoltage { get; set; }
        public double MaxVoltage { get; set; }
        public int NoOfCycles { get; internal set; }
    }
}
