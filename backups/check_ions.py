#!/usr/bin/env python
import sys
from pathlib import Path
import inspect

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation

def main():
    # Create a simulation
    sim = Simulation()
    
    # Print the actual implementation of get_unaccounted_ion_amount 
    print("\n==== IMPLEMENTATION OF get_unaccounted_ion_amount ====")
    print(inspect.getsource(sim.get_unaccounted_ion_amount))
    
    # Print initial state
    print("\n==== INITIAL STATE ====")
    print(f"Volume: {sim.vesicle.volume} L")
    print(f"Area: {sim.vesicle.area} m²")
    print(f"Capacitance: {sim.vesicle.capacitance} F") 
    print(f"Init Charge: {sim.vesicle.init_charge} C")
    print(f"Charge: {sim.vesicle.charge} C")
    print(f"Voltage: {sim.vesicle.voltage} V")
    
    # Print ions before setting amounts
    print("\n==== IONS BEFORE set_ion_amounts ====")
    total_ionic_charge_conc = 0.0
    for ion in sim.all_species:
        charge_conc = ion.elementary_charge * ion.init_vesicle_conc
        total_ionic_charge_conc += charge_conc
        print(f"Ion: {ion.display_name}")
        print(f"  Elementary Charge: {ion.elementary_charge}")
        print(f"  Initial Vesicle Concentration: {ion.init_vesicle_conc} M")
        print(f"  Charge * Concentration: {charge_conc} mol/L")
        print(f"  Current Amount: {ion.vesicle_amount} mol")
        
    print(f"\nTotal sum(charge * concentration): {total_ionic_charge_conc} mol/L")
    
    # Set ion amounts
    sim.set_ion_amounts()
    
    # Print ions after setting amounts
    print("\n==== IONS AFTER set_ion_amounts ====")
    total_ionic_charge_amount = 0.0
    for ion in sim.all_species:
        charge_amount = ion.elementary_charge * ion.vesicle_amount
        total_ionic_charge_amount += charge_amount
        print(f"Ion: {ion.display_name}")
        print(f"  Initial Vesicle Concentration: {ion.init_vesicle_conc} M")
        print(f"  Current Vesicle Concentration: {ion.vesicle_conc} M")
        print(f"  Current Amount: {ion.vesicle_amount} mol")
        print(f"  Charge * Amount: {charge_amount} mol")
        
    print(f"\nTotal sum(charge * amount): {total_ionic_charge_amount} mol")
    
    # Calculate unaccounted ions
    sim.get_unaccounted_ion_amount()
    print(f"\nUnaccounted ion amount: {sim.unaccounted_ion_amounts} mol")
    
    # Compute what the final charge should be
    total_charge_in_moles = total_ionic_charge_amount + sim.unaccounted_ion_amounts
    print(f"Total charge (ions + unaccounted) in moles: {total_charge_in_moles} mol")
    
    # Constant from sim.py
    FARADAY_CONSTANT = 96485.33212  # C/mol
    total_charge_in_coulombs = total_charge_in_moles * FARADAY_CONSTANT
    print(f"Total charge in Coulombs: {total_charge_in_coulombs} C")
    
    # Calculate expected init charge in moles
    init_charge_in_moles = sim.vesicle.init_charge / FARADAY_CONSTANT
    print(f"Initial charge in moles (init_charge/FARADAY): {init_charge_in_moles} mol")
    
    # Calculate sum(ion.elem_charge * ion.init_conc) * volume
    init_ionic_charge_in_moles = total_ionic_charge_conc * sim.vesicle.init_volume
    print(f"Initial ionic charge in moles (sum(z*c)*V): {init_ionic_charge_in_moles} mol")

    # Calculate with the 1000 factor explicitly
    init_ionic_charge_with_1000 = total_ionic_charge_conc * 1000 * sim.vesicle.init_volume
    print(f"Initial ionic charge with 1000 factor (sum(z*c)*1000*V): {init_ionic_charge_with_1000} mol")
    
    # Calculate expected unaccounted ion amount
    expected_unaccounted = init_charge_in_moles - init_ionic_charge_in_moles
    expected_unaccounted_with_1000 = init_charge_in_moles - init_ionic_charge_with_1000
    print(f"Expected unaccounted (without 1000): {expected_unaccounted} mol")
    print(f"Expected unaccounted (with 1000): {expected_unaccounted_with_1000} mol")
    
    # Update simulation state
    sim.update_simulation_state()
    print(f"\nAfter update_simulation_state, charge = {sim.vesicle.charge} C")

if __name__ == "__main__":
    main() 