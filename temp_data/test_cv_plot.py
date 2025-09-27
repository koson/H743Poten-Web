#!/usr/bin/env python3
"""
Plot CV data from H743 measurement to analyze 100kΩ resistor behavior
"""

import json
import matplotlib.pyplot as plt
import numpy as np

# CV Data from H743 measurement
cv_data = {
    "data": {
        "completed": True,
        "points": [
            {"current": 0.00009122642517089844, "cycle": 1, "direction": "forward", "potential": -0.49986557960510253, "timestamp": 1758953945.0612588},
            {"current": 0.0000972374153137207, "cycle": 1, "direction": "forward", "potential": -0.4698091983795166, "timestamp": 1758953945.3618226},
            {"current": 0.00010123714447021485, "cycle": 1, "direction": "forward", "potential": -0.499882435798645, "timestamp": 1758953945.5618024},
            {"current": 0.0001052483606338501, "cycle": 1, "direction": "forward", "potential": -0.4798269271850586, "timestamp": 1758953945.7623575},
            {"current": 0.00010925933361053467, "cycle": 1, "direction": "forward", "potential": -0.45977139472961426, "timestamp": 1758953945.9629128},
            {"current": 0.0000932624340057373, "cycle": 1, "direction": "forward", "potential": -0.4397562026977539, "timestamp": 1758953946.1630647},
            {"current": 0.00009727212429046632, "cycle": 1, "direction": "forward", "potential": -0.41970679759979246, "timestamp": 1758953946.3635588},
            {"current": 0.00010128031730651856, "cycle": 1, "direction": "forward", "potential": -0.399662184715271, "timestamp": 1758953946.564005},
            {"current": 0.00010528642177581788, "cycle": 1, "direction": "forward", "potential": -0.3796314001083374, "timestamp": 1758953946.7643127},
            {"current": 0.00010929308891296388, "cycle": 1, "direction": "forward", "potential": -0.35959796905517577, "timestamp": 1758953946.964647},
            {"current": 0.00009330479145050049, "cycle": 1, "direction": "forward", "potential": -0.33953964710235596, "timestamp": 1758953947.1652303},
            {"current": 0.00009730737209320069, "cycle": 1, "direction": "forward", "potential": -0.31952652931213377, "timestamp": 1758953947.3653615},
            {"current": 0.00010132099151611329, "cycle": 1, "direction": "forward", "potential": -0.29946370124816896, "timestamp": 1758953947.5659897},
            {"current": 0.00010532278060913086, "cycle": 1, "direction": "forward", "potential": -0.27945404052734374, "timestamp": 1758953947.7660863},
            {"current": 0.00010933269023895264, "cycle": 1, "direction": "forward", "potential": -0.2594040632247925, "timestamp": 1758953947.966586},
            {"current": 0.0000933372735977173, "cycle": 1, "direction": "forward", "potential": -0.23938205242156985, "timestamp": 1758953948.1668062},
            {"current": 0.00009734690189361572, "cycle": 1, "direction": "forward", "potential": -0.2193328380584717, "timestamp": 1758953948.3672984},
            {"current": 0.00010135382652282715, "cycle": 1, "direction": "forward", "potential": -0.1992948532104492, "timestamp": 1758953948.5676782},
            {"current": 0.00010536187171936036, "cycle": 1, "direction": "forward", "potential": -0.17925429344177246, "timestamp": 1758953948.7680838},
            {"current": 0.00010936595439910889, "cycle": 1, "direction": "forward", "potential": -0.1592334985733032, "timestamp": 1758953948.9682918},
            {"current": 0.00009337496757507325, "cycle": 1, "direction": "forward", "potential": -0.1391887664794922, "timestamp": 1758953949.168739},
            {"current": 0.00009738320350646973, "cycle": 1, "direction": "forward", "potential": -0.11914727687835691, "timestamp": 1758953949.369154},
            {"current": 0.00037606356688764993, "cycle": 1, "direction": "forward", "potential": -0.09908177852630617, "timestamp": 1758953949.569809},
            {"current": 0.0005409533707648931, "cycle": 1, "direction": "forward", "potential": -0.07902350425720217, "timestamp": 1758953949.7703917},
            {"current": 0.0007156466554441903, "cycle": 1, "direction": "forward", "potential": -0.058975982666015614, "timestamp": 1758953949.970867},
            {"current": 0.000852850332286357, "cycle": 1, "direction": "forward", "potential": -0.038922500610351574, "timestamp": 1758953950.1714017},
            {"current": 0.0009624438820364393, "cycle": 1, "direction": "forward", "potential": -0.01887378692626951, "timestamp": 1758953950.3718889},
            {"current": 0.001001308772772398, "cycle": 1, "direction": "forward", "potential": 0.0011991977691649947, "timestamp": 1758953950.5726187},
            {"current": 0.000961452123905005, "cycle": 1, "direction": "forward", "potential": 0.021213412284851074, "timestamp": 1758953950.7727609},
            {"current": 0.0008529268018091786, "cycle": 1, "direction": "forward", "potential": 0.04126019477844234, "timestamp": 1758953950.9732287},
            {"current": 0.0006801116897732607, "cycle": 1, "direction": "forward", "potential": 0.061314845085144065, "timestamp": 1758953951.1737752},
            {"current": 0.0005133500650538909, "cycle": 1, "direction": "forward", "potential": 0.08135776519775395, "timestamp": 1758953951.3742044},
            {"current": 0.00010149391651153565, "cycle": 1, "direction": "forward", "potential": 0.10140180587768555, "timestamp": 1758953951.5746448},
            {"current": 0.000105505108833313, "cycle": 1, "direction": "forward", "potential": 0.12145829200744629, "timestamp": 1758953951.7752097},
            {"current": 0.00010951457500457764, "cycle": 1, "direction": "forward", "potential": 0.1415052652359009, "timestamp": 1758953951.9756794},
        ]
    }
}

# Extract data
points = cv_data["data"]["points"]
potentials = [p["potential"] for p in points]
currents = [p["current"] * 1e6 for p in points]  # Convert to microamps

# Create plot
plt.figure(figsize=(12, 8))

# Plot the CV data
plt.subplot(2, 1, 1)
plt.plot(potentials, currents, 'b.-', linewidth=2, markersize=4, label='H743 Measurement')

# Plot theoretical 100kΩ line
theoretical_potentials = np.linspace(-0.5, 0.5, 100)
theoretical_currents = (theoretical_potentials / 100000) * 1e6  # I = V/R in microamps
plt.plot(theoretical_potentials, theoretical_currents, 'r--', linewidth=2, label='100kΩ Theory (I=V/R)')

plt.xlabel('Potential (V)')
plt.ylabel('Current (μA)')
plt.title('CV Measurement: H743 vs 100kΩ Theory')
plt.grid(True, alpha=0.3)
plt.legend()

# Zoom in around zero crossing
plt.subplot(2, 1, 2)
# Filter data around zero crossing (-0.2V to +0.2V)
zero_region_pot = [p for p in potentials if -0.2 <= p <= 0.2]
zero_region_cur = [currents[i] for i, p in enumerate(potentials) if -0.2 <= p <= 0.2]

plt.plot(zero_region_pot, zero_region_cur, 'b.-', linewidth=2, markersize=6, label='H743 Measurement')
theoretical_zero = np.linspace(-0.2, 0.2, 50)
theoretical_zero_cur = (theoretical_zero / 100000) * 1e6
plt.plot(theoretical_zero, theoretical_zero_cur, 'r--', linewidth=2, label='100kΩ Theory')

plt.xlabel('Potential (V)')
plt.ylabel('Current (μA)')
plt.title('Zoom: Zero Crossing Region')
plt.grid(True, alpha=0.3)
plt.legend()

plt.tight_layout()
plt.savefig('h743_cv_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

# Calculate actual resistance
print("=== CV Analysis Results ===")
print(f"Data points: {len(points)}")
print(f"Potential range: {min(potentials):.3f}V to {max(potentials):.3f}V")
print(f"Current range: {min(currents):.1f}μA to {max(currents):.1f}μA")

# Calculate resistance from linear region (excluding near-zero region where there might be nonlinearity)
linear_points = [(p, c) for p, c in zip(potentials, currents) if abs(p) > 0.1]
if linear_points:
    V_linear = [p[0] for p in linear_points]
    I_linear = [p[1] for p in linear_points]
    
    # Simple linear regression: R = V/I (average)
    resistances = [abs(v / (i * 1e-6)) for v, i in zip(V_linear, I_linear) if i != 0]
    if resistances:
        avg_resistance = np.mean(resistances)
        std_resistance = np.std(resistances)
        print(f"\nCalculated resistance (linear region):")
        print(f"Average: {avg_resistance:.0f} Ω")
        print(f"Std dev: {std_resistance:.0f} Ω")
        print(f"Expected: 100,000 Ω")
        print(f"Ratio: {avg_resistance/100000:.2f}x expected")

print("\n=== Analysis ===")
print("1. The current is much higher than expected for 100kΩ")
print("2. Shows some nonlinearity near zero crossing")
print("3. Possible causes:")
print("   - Resistor value is not actually 100kΩ")
print("   - Leakage current in the system")
print("   - Capacitive effects")
print("   - Calibration issues with H743")