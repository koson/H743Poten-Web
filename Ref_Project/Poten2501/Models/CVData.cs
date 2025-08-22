using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Poten2501.Models
{
    internal class CVData
    {
        public int Index { get; set; }
        public double TimeStamp { get; set; }
        public double REVoltage { get; set; }
        public double WEVoltage { get; set; }
        public double WECurrentRange { get; set; }
        public int CycleNo { get; set; }
    }
}

/* 1. Preamble : "CV"
 * 2. Timestamp (milliseconds)
 * 3. RE Potential
 * 4. WE Potential
 * 5. WE Current range
 * 6. Cycle Number
 */
