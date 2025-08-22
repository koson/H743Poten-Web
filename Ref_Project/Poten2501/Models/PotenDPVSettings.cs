using CommunityToolkit.Mvvm.ComponentModel;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Poten2501.Models
{
    public class PotenDPVSettings
    {
        public int NoOfSegments;
        public string InitialDirection;
        public double InitialPotentialVolt;
        public double FinalPotentialVolt;
        public double LowerPotentialVolt;
        public double UpperPotentialVolt;
        public double DifferentialPulseHeight;
        public double DifferentialPulseWidth;
        public double DifferentialPulsePeriod;
        public double DifferentialPulseIncrement;
        public double DifferentialPulsePrePulseWidth;
        public double DifferentialPulsePostPulseWidth;
    }
}
