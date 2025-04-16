#!/usr/bin/env python
import sys
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation
from src.backend.default_ion_species import default_ion_species

def inspect_simulation_creation():
    """Inspect how a simulation is created and how it loads ion species"""
    print("\n==== SIMULATION CREATION INSPECTION ====")
    
    # Create a minimal simulation
    sim = Simulation()
    
    # Inspect the ion species list
    print(f"\nFound {len(sim.all_species)} ion species in default simulation:")
    for i, ion in enumerate(sim.all_species):
        print(f"{i+1}. {ion.display_name}: charge={ion.elementary_charge}, init_conc={ion.init_vesicle_conc} M")
    
    # Check where ion species are created
    print("\nChecking source of default_ion_species:")
    for name, config in default_ion_species.items():
        print(f"{name}: {config}")
    
    # Check how sim.species and sim.all_species are populated
    print("\nChecking sim.species vs sim.all_species:")
    print(f"sim.species (dict): {len(sim.species)} items")
    print(f"sim.all_species (list): {len(sim.all_species)} items")
    
    # Check if all keys in sim.species are present in sim.all_species
    keys_in_species = set(sim.species.keys())
    names_in_all_species = {ion.display_name for ion in sim.all_species}
    
    print(f"\nKeys in sim.species: {keys_in_species}")
    print(f"Names in sim.all_species: {names_in_all_species}")
    
    missing_in_all = keys_in_species - names_in_all_species
    if missing_in_all:
        print(f"WARNING: The following ions are in sim.species but missing from sim.all_species: {missing_in_all}")
    
    missing_in_dict = names_in_all_species - keys_in_species
    if missing_in_dict:
        print(f"WARNING: The following ions are in sim.all_species but missing from sim.species: {missing_in_dict}")

def simulate_cpp_species_map():
    """Simulate how species are mapped in C++ implementation"""
    print("\n==== C++ SPECIES MAP SIMULATION ====")
    
    # Create a simulation with default parameters
    sim = Simulation()
    
    # Extract species data in C++ format
    species_data = {}
    for ion in sim.all_species:
        species_data[ion.display_name] = {
            "elementary_charge": ion.elementary_charge,
            "init_vesicle_conc": ion.init_vesicle_conc,
            "exterior_conc": ion.exterior_conc,
            "vesicle_conc": ion.vesicle_conc if hasattr(ion, 'vesicle_conc') else None,
            "vesicle_amount": ion.vesicle_amount if hasattr(ion, 'vesicle_amount') else None
        }
    
    print("C++ style species map would contain:")
    for name, data in species_data.items():
        print(f"{name}: {data}")
    
    # Simulate C++ loop over species
    print("\nSimulating C++ loop over species for updateCharge():")
    total_ionic_charge = 0.0
    
    for name, data in species_data.items():
        # Set vesicle_amount (simulating the results after setIonAmounts())
        # This would be called before updateCharge() in both implementations
        if data["vesicle_amount"] is None:
            init_volume = 9.202772079915702e-18  # Default vesicle volume in liters
            data["vesicle_amount"] = data["init_vesicle_conc"] * 1000 * init_volume
        
        # Calculate contribution to total charge
        charge = data["elementary_charge"]
        amount = data["vesicle_amount"]
        contribution = charge * amount
        total_ionic_charge += contribution
        
        print(f"  {name}: {charge} * {amount} = {contribution} mol")
    
    print(f"Total ionic charge: {total_ionic_charge} mol")
    
    # Calculate unaccounted ion amount (simulating getUnaccountedIonAmount())
    init_charge = 8.494866535306801e-15  # Default init_charge in Coulombs
    FARADAY_CONSTANT = 96485.33212  # C/mol
    init_charge_in_moles = init_charge / FARADAY_CONSTANT
    
    # Sum of ion_charge * init_conc
    total_ionic_charge_concentration = sum(data["elementary_charge"] * data["init_vesicle_conc"] for data in species_data.values())
    
    # Calculate with and without 1000 factor (both ways C++ might implement it)
    init_volume = 9.202772079915702e-18  # Default vesicle volume in liters
    ionic_charge_in_moles = total_ionic_charge_concentration * init_volume
    ionic_charge_in_moles_with_1000 = total_ionic_charge_concentration * 1000 * init_volume
    
    # Calculate unaccounted ion amount
    unaccounted_no_factor = init_charge_in_moles - ionic_charge_in_moles
    unaccounted_with_factor = init_charge_in_moles - ionic_charge_in_moles_with_1000
    
    print(f"\nUnaccounted ion amount (without 1000 factor): {unaccounted_no_factor} mol")
    print(f"Unaccounted ion amount (with 1000 factor): {unaccounted_with_factor} mol")
    
    # Simulate finalization of total charge calculation
    total_charge_in_moles = total_ionic_charge + unaccounted_with_factor  # Using the 1000 factor version
    total_charge_in_coulombs = total_charge_in_moles * FARADAY_CONSTANT
    
    print(f"\nFinal charge calculation:")
    print(f"Total ionic charge: {total_ionic_charge} mol")
    print(f"Unaccounted ion amount: {unaccounted_with_factor} mol")
    print(f"Total charge in moles: {total_charge_in_moles} mol")
    print(f"Total charge in Coulombs: {total_charge_in_coulombs} C")
    
    # Compare with actual Python implementation charge
    sim.set_ion_amounts()
    sim.get_unaccounted_ion_amount()
    sim.update_charge()
    actual_charge = sim.vesicle.charge
    
    print(f"\nActual charge from Python implementation: {actual_charge} C")
    print(f"Difference: {total_charge_in_coulombs - actual_charge} C")

def check_species_iteration_order():
    """Check if the order of species iteration might affect results"""
    print("\n==== CHECKING SPECIES ITERATION ORDER ====")
    
    # Create a simulation and get ion species
    sim = Simulation()
    sim.set_ion_amounts()
    
    # Inspect the iteration order in Python dictionary vs. list
    print("\nIteration order in sim.species (dictionary):")
    for i, (name, species) in enumerate(sim.species.items()):
        contribution = species.elementary_charge * species.vesicle_amount
        print(f"{i+1}. {name}: contribution={contribution} mol")
    
    print("\nIteration order in sim.all_species (list):")
    for i, species in enumerate(sim.all_species):
        contribution = species.elementary_charge * species.vesicle_amount
        print(f"{i+1}. {species.display_name}: contribution={contribution} mol")
    
    # Check if ordering affects the total charge calculation
    total_from_dict = sum(species.elementary_charge * species.vesicle_amount for species in sim.species.values())
    total_from_list = sum(species.elementary_charge * species.vesicle_amount for species in sim.all_species)
    
    print(f"\nTotal ionic charge from dictionary: {total_from_dict} mol")
    print(f"Total ionic charge from list: {total_from_list} mol")
    print(f"Difference: {total_from_dict - total_from_list} mol")

def main():
    # Inspect simulation creation and how ion species are loaded
    inspect_simulation_creation()
    
    # Simulate how C++ would handle the same ion species
    simulate_cpp_species_map()
    
    # Check if iteration order might affect results
    check_species_iteration_order()

if __name__ == "__main__":
    main() 