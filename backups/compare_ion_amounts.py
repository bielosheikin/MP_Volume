#!/usr/bin/env python
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation, FARADAY_CONSTANT

def analyze_ion_charges():
    """Analyze each ion's contribution to the total charge in detail"""
    print("\n==== DETAILED ION CHARGE ANALYSIS ====")
    
    # Create simulation
    sim = Simulation()
    
    # Initial state - before set_ion_amounts
    print("\nINITIAL STATE (before set_ion_amounts):")
    print(f"Vesicle volume: {sim.vesicle.volume:.20e} L")
    print(f"Vesicle init_charge: {sim.vesicle.init_charge:.20e} C")
    print(f"Vesicle charge: {sim.vesicle.charge:.20e} C")
    
    # Print each ion's concentration
    print("\nION CONCENTRATIONS:")
    print(f"{'Ion':<5} {'Elem.Charge':<12} {'Init Conc (M)':<20} {'Current Conc (M)':<20}")
    print("-" * 60)
    
    total_ionic_charge_conc = 0.0
    for ion in sim.all_species:
        charge_conc = ion.elementary_charge * ion.init_vesicle_conc
        total_ionic_charge_conc += charge_conc
        print(f"{ion.display_name:<5} {ion.elementary_charge:<12} {ion.init_vesicle_conc:.20e} {ion.vesicle_conc if ion.vesicle_conc is not None else 'None':<20}")
    
    print(f"\nTotal sum(charge * concentration): {total_ionic_charge_conc:.20e} mol/L")
    
    # Set ion amounts
    sim.set_ion_amounts()
    
    # Calculate unaccounted ion amount
    sim.get_unaccounted_ion_amount()
    
    # Print each ion's amount and contribution to charge
    print("\nION AMOUNTS AFTER set_ion_amounts:")
    print(f"{'Ion':<5} {'Elem.Charge':<12} {'Amount (mol)':<25} {'Charge Contrib (mol)':<25}")
    print("-" * 70)
    
    total_ionic_charge_amount = 0.0
    for ion in sim.all_species:
        charge_amount = ion.elementary_charge * ion.vesicle_amount
        total_ionic_charge_amount += charge_amount
        print(f"{ion.display_name:<5} {ion.elementary_charge:<12} {ion.vesicle_amount:.20e} {charge_amount:.20e}")
    
    print(f"\nTotal sum(charge * amount): {total_ionic_charge_amount:.20e} mol")
    print(f"Unaccounted ion amount: {sim.unaccounted_ion_amounts:.20e} mol")
    
    # Calculate total charge
    total_charge_in_moles = total_ionic_charge_amount + sim.unaccounted_ion_amounts
    total_charge_in_coulombs = total_charge_in_moles * FARADAY_CONSTANT
    
    print(f"\nTOTAL CHARGE CALCULATION:")
    print(f"Sum(ion_charge * amount): {total_ionic_charge_amount:.20e} mol")
    print(f"Unaccounted ion amount: {sim.unaccounted_ion_amounts:.20e} mol")
    print(f"Total charge in moles: {total_charge_in_moles:.20e} mol")
    print(f"FARADAY_CONSTANT: {FARADAY_CONSTANT:.20e} C/mol")
    print(f"Total charge in Coulombs: {total_charge_in_coulombs:.20e} C")
    print(f"Vesicle charge: {sim.vesicle.charge:.20e} C")
    print(f"Difference: {total_charge_in_coulombs - sim.vesicle.charge:.20e} C")
    
    # Update simulation state and check charge again
    sim.update_simulation_state()
    print(f"\nAfter update_simulation_state, charge = {sim.vesicle.charge:.20e} C")
    
    # Expected vesicle charge from formula in update_charge
    expected_charge = ((sum(ion.elementary_charge * ion.vesicle_amount for ion in sim.all_species) +
                       sim.unaccounted_ion_amounts) *
                       FARADAY_CONSTANT)
    
    print(f"Expected charge from update_charge formula: {expected_charge:.20e} C")
    print(f"Difference: {expected_charge - sim.vesicle.charge:.20e} C")
    
    # For comparison with C++ implementation
    print("\nFOR COMPARISON WITH C++ IMPLEMENTATION:")
    print("The following values should be checked against C++ debug output:")
    print(f"1. Each ion's amount and elementary charge")
    print(f"2. Sum of ion_charge * amount: {total_ionic_charge_amount:.20e} mol")
    print(f"3. Unaccounted ion amount: {sim.unaccounted_ion_amounts:.20e} mol")
    print(f"4. Total charge in Coulombs: {total_charge_in_coulombs:.20e} C")
    
    # What C++ log should show for each ion
    print("\nIn C++ debug output, look for:")
    for ion in sim.all_species:
        print(f"Ion: {ion.display_name}")
        print(f"  Elementary charge: {ion.elementary_charge}")
        print(f"  Vesicle amount: {ion.vesicle_amount:.20e} mol")
        print(f"  Charge * Amount: {ion.elementary_charge * ion.vesicle_amount:.20e} mol")

def main():
    analyze_ion_charges()

if __name__ == "__main__":
    main() 