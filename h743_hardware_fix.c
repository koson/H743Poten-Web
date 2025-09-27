
// H743 Current Range Hardware Fix
// ===============================


/* CRITICAL ISSUE DETECTED: Range 0 and Range 1 have identical slopes
 * This indicates a hardware configuration problem in the TIA circuit
 */

// Hardware checks required:
// 1. Verify TIA resistor values
//    - Range 0: Should be 1kΩ
//    - Range 1: Should be 10kΩ
//    - Range 2: Should be 100kΩ  
//    - Range 3: Should be 1MΩ

// 2. Check current range switching logic
#define CURRENT_RANGE_0    0  // 1kΩ TIA, ±1mA range
#define CURRENT_RANGE_1    1  // 10kΩ TIA, ±100µA range
#define CURRENT_RANGE_2    2  // 100kΩ TIA, ±10µA range
#define CURRENT_RANGE_3    3  // 1MΩ TIA, ±1µA range

// 3. TIA gain verification function
void verify_tia_configuration(void) {
    // Test each range with known test current
    float test_current_ua = 50.0;  // 50µA test signal
    
    // Range 0: Expected output ~50mV (50µA × 1kΩ)
    set_current_range(CURRENT_RANGE_0);
    float output_range_0 = read_tia_output_mv();
    
    // Range 1: Expected output ~500mV (50µA × 10kΩ)  
    set_current_range(CURRENT_RANGE_1);
    float output_range_1 = read_tia_output_mv();
    
    // Check if Range 1 is ~10x more sensitive than Range 0
    float sensitivity_ratio = output_range_1 / output_range_0;
    
    if (fabs(sensitivity_ratio - 10.0) > 2.0) {
        // HARDWARE ERROR: TIA configuration problem
        printf("ERROR: TIA sensitivity ratio = %.2f (expected ~10.0)\n", sensitivity_ratio);
        printf("Check TIA resistor values and switching circuit\n");
    }
}

// 4. Software compensation (temporary fix)
float apply_range_correction(int range, float raw_current_ua) {
    // Temporary software correction until hardware is fixed
    const float correction_factors[] = {
        1.0,    // Range 0: No correction needed
        1.0,    // Range 1: Should be 10x more sensitive - FIX HARDWARE
        10.0,   // Range 2: Estimated correction
        100.0   // Range 3: Estimated correction
    };
    
    if (range >= 0 && range <= 3) {
        return raw_current_ua / correction_factors[range];
    }
    return raw_current_ua;
}

// 5. Recommended hardware modifications:
/*
 * Check schematic for:
 * - TIA feedback resistor values (R_TIA_0 = 1kΩ, R_TIA_1 = 10kΩ, etc.)
 * - Current range selection multiplexer/switches
 * - ADC reference voltage (should be stable 3.3V or 2.5V)
 * - Op-amp specifications and power supply
 * - PCB layout for noise and crosstalk
 */
