#!/usr/bin/env python
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation, FARADAY_CONSTANT

def analyze_ion_contributions():
    """Analyze each ion's contribution to the total charge calculation"""
    print("\n==== ION CONTRIBUTION ANALYSIS ====")
    
    # Create simulation
    sim = Simulation()
    
    # Set ion amounts
    sim.set_ion_amounts()
    
    # Calculate unaccounted ion amount
    sim.get_unaccounted_ion_amount()
    
    # Print each ion's amount and contribution to charge
    print("\nION CONTRIBUTIONS TO TOTAL CHARGE:")
    print(f"{'Ion':<5} {'Elem.Charge':<12} {'Amount (mol)':<25} {'Charge Contrib (mol)':<25} {'% of Total':<15}")
    print("-" * 85)
    
    # Calculate total ionic charge amount
    total_ionic_charge_amount = sum(ion.elementary_charge * ion.vesicle_amount for ion in sim.all_species)
    
    # Calculate percentage contribution for each ion
    for ion in sorted(sim.all_species, key=lambda i: abs(i.elementary_charge * i.vesicle_amount), reverse=True):
        charge_amount = ion.elementary_charge * ion.vesicle_amount
        percentage = (charge_amount / total_ionic_charge_amount) * 100 if total_ionic_charge_amount != 0 else 0
        print(f"{ion.display_name:<5} {ion.elementary_charge:<12} {ion.vesicle_amount:.20e} {charge_amount:.20e} {percentage:+.2f}%")
    
    print("-" * 85)
    print(f"TOTAL: {'':<12} {'':<25} {total_ionic_charge_amount:.20e} 100.00%")
    
    # Calculate unaccounted ion amount and total charge
    print(f"\nUnaccounted ion amount: {sim.unaccounted_ion_amounts:.20e} mol")
    total_charge_in_moles = total_ionic_charge_amount + sim.unaccounted_ion_amounts
    total_charge_in_coulombs = total_charge_in_moles * FARADAY_CONSTANT
    print(f"Total charge in moles: {total_charge_in_moles:.20e} mol")
    print(f"Total charge in Coulombs: {total_charge_in_coulombs:.20e} C")
    
    # What if analysis - missing ions
    print("\n==== WHAT IF ANALYSIS - MISSING IONS ====")
    
    for missing_ion in sim.all_species:
        # Calculate total charge without this ion
        reduced_ionic_charge = total_ionic_charge_amount - (missing_ion.elementary_charge * missing_ion.vesicle_amount)
        reduced_total_charge = reduced_ionic_charge + sim.unaccounted_ion_amounts
        reduced_charge_in_coulombs = reduced_total_charge * FARADAY_CONSTANT
        
        # Calculate the percentage difference
        charge_diff = total_charge_in_coulombs - reduced_charge_in_coulombs
        percentage_diff = (charge_diff / total_charge_in_coulombs) * 100
        
        print(f"Without {missing_ion.display_name} ion:")
        print(f"  Charge reduction: {charge_diff:.20e} C ({percentage_diff:.2f}%)")
        print(f"  New total charge: {reduced_charge_in_coulombs:.20e} C")
    
    # What C++ would need to match Python
    print("\n==== C++ IMPLEMENTATION RECOMMENDATIONS ====")
    print("Based on this analysis, to match the Python calculation in C++, make sure:")
    
    # Sort ions by importance
    ions_by_importance = sorted(sim.all_species, key=lambda i: abs(i.elementary_charge * i.vesicle_amount), reverse=True)
    
    print("1. All the following ions are included in the charge calculation (in order of importance):")
    for ion in ions_by_importance:
        contribution = ion.elementary_charge * ion.vesicle_amount
        percentage = (contribution / total_ionic_charge_amount) * 100 if total_ionic_charge_amount != 0 else 0
        print(f"   - {ion.display_name}: contributes {percentage:.2f}% of ionic charge")
    
    print("2. The unaccounted ion amount is correctly calculated with the 1000 factor:")
    print(f"   unaccounted_ion_amount = {sim.unaccounted_ion_amounts:.20e} mol")
    
    print("3. The total charge calculation uses the FARADAY_CONSTANT:")
    print(f"   total_charge = (sum_ionic_charge + unaccounted_ion_amount) * {FARADAY_CONSTANT}")

def main():
    analyze_ion_contributions()

if __name__ == "__main__":
    main() 