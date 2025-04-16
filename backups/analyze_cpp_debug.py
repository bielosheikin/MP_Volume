#!/usr/bin/env python
import sys
import inspect
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation, FARADAY_CONSTANT

def analyze_unaccounted_ion():
    """Analyze the calculation of unaccounted ion amount"""
    print("\n==== UNACCOUNTED ION CALCULATION ANALYSIS ====")
    
    # Create simulation
    sim = Simulation()
    
    # Get the actual implementation
    print("Implementation of get_unaccounted_ion_amount:")
    print(inspect.getsource(sim.get_unaccounted_ion_amount))
    
    # Perform calculation step by step
    init_charge = sim.vesicle.init_charge
    init_charge_moles = init_charge / FARADAY_CONSTANT
    
    # Calculate the sum of ion charge * concentration
    total_charge_conc = sum(ion.elementary_charge * ion.init_vesicle_conc for ion in sim.all_species)
    
    # Calculate with and without 1000 factor
    volume = sim.vesicle.init_volume
    
    # Calculate by directly translating the line in code
    direct_calculation = ((init_charge / FARADAY_CONSTANT) - 
                        (total_charge_conc) * 1000 * volume)
    
    # Calculate various ways to see where the discrepancy comes from
    calculation_without_1000 = init_charge_moles - (total_charge_conc * volume)
    calculation_with_1000 = init_charge_moles - (total_charge_conc * 1000 * volume)
    
    # Calculate with 1000 factor applied differently - this would match C++
    calculation_1000_outside = init_charge_moles - (total_charge_conc * volume * 1000)
    
    # Actual call to the method
    sim.get_unaccounted_ion_amount()
    actual_result = sim.unaccounted_ion_amounts
    
    # Print all values
    print(f"\nInit charge: {init_charge} C")
    print(f"Init charge in moles: {init_charge_moles} mol")
    print(f"Total ionic charge concentration: {total_charge_conc} mol/L")
    print(f"Init volume: {volume} L")
    
    print(f"\nDirect calculation (from code): {direct_calculation} mol")
    print(f"Calculation without 1000 factor: {calculation_without_1000} mol")
    print(f"Calculation with 1000 factor: {calculation_with_1000} mol")
    print(f"Calculation with 1000 outside parentheses: {calculation_1000_outside} mol")
    print(f"Actual result from get_unaccounted_ion_amount: {actual_result} mol")
    
    # Check what happens when multiplying by 1000
    factor_effect = -(total_charge_conc * volume)
    factor_effect_with_1000 = -(total_charge_conc * 1000 * volume)
    
    print(f"\nNegative ionic charge in moles without 1000: {factor_effect} mol")
    print(f"Negative ionic charge in moles with 1000: {factor_effect_with_1000} mol")
    print(f"Difference due to 1000 factor: {factor_effect_with_1000 - factor_effect} mol")
    
    # Print the correct formula used in C++ vs Python
    print("\nPython formula (current):")
    print(f"  unaccounted_ion_amount = (init_charge/FARADAY) - (total_ion_charge_conc * 1000 * init_volume)")
    print("\nC++ formula (corrected):")
    print(f"  unaccounted_ion_amount = (init_charge/FARADAY) - (total_ion_charge_conc * init_volume)")
    
    # Calculate what the error would be
    if actual_result == calculation_with_1000:
        print("\nConclusion: Python implementation correctly uses the 1000 factor as in the code.")
    else:
        print("\nWarning: Python implementation result doesn't match expected calculation!")
    
    # For debugging, check the ion amounts result
    sim.set_ion_amounts()
    ionic_charge_amount = sum(ion.elementary_charge * ion.vesicle_amount for ion in sim.all_species)
    total_charge = (ionic_charge_amount + actual_result) * FARADAY_CONSTANT
    
    print(f"\nAfter set_ion_amounts:")
    print(f"  Sum of ion charge * amount: {ionic_charge_amount} mol")
    print(f"  Total charge (with unaccounted): {total_charge} C")
    print(f"  Vesicle charge: {sim.vesicle.charge} C")
    
    if abs(total_charge - sim.vesicle.charge) < 1e-20:
        print("  Charge calculation is consistent!")
    else:
        print(f"  Warning: Charge differs by {total_charge - sim.vesicle.charge} C")
    
    return

def main():
    analyze_unaccounted_ion()

if __name__ == "__main__":
    main() 