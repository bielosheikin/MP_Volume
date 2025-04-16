import numpy as np
from src.backend.simulation import Simulation
import json
import os
import sys

def format_scientific(number):
    """Format a number in scientific notation with consistent precision"""
    return f"{number:.6e}"

def compare_calculations():
    print("=== COMPARING PYTHON AND C++ CALCULATIONS ===")
    
    # Create a minimal simulation using the same parameters as in analyze_config.py
    sim = Simulation(
        time_step=0.001,
        total_time=0.001,
        temperature=310.13274319979337,
        init_buffer_capacity=0.0005,
        vesicle_init_radius=1.3e-6,
        vesicle_init_voltage=0.04,
        vesicle_init_pH=7.4,
        vesicle_specific_capacitance=0.01,
        exterior_pH=7.2,
        ion_species=[
            {
                "name": "cl",
                "init_vesicle_conc": 0.159,
                "exterior_conc": 0.02,
                "elementary_charge": -1
            },
            {
                "name": "h",
                "init_vesicle_conc": 7.962143411069939e-05,
                "exterior_conc": 0.0001261914688960386,
                "elementary_charge": 1
            },
            {
                "name": "na",
                "init_vesicle_conc": 0.15,
                "exterior_conc": 0.01,
                "elementary_charge": 1
            },
            {
                "name": "k",
                "init_vesicle_conc": 0.005,
                "exterior_conc": 0.14,
                "elementary_charge": 1
            }
        ]
    )
    
    # Calculate the unaccounted ion amount in Python
    FARADAY_CONSTANT = 96485  # C/mol
    
    # Python calculations
    init_charge = sim.vesicle.init_charge
    init_charge_in_moles = init_charge / FARADAY_CONSTANT
    
    # Calculate sum of ion_charge * concentration
    ionic_charge_conc = 0
    for ion in sim.all_species:
        ionic_charge_conc += ion.elementary_charge * ion.init_vesicle_conc
    
    # Calculate the ionic charge in moles
    init_volume = sim.vesicle.init_volume
    ionic_charge_in_moles = ionic_charge_conc * init_volume
    
    # Calculate unaccounted ion amount
    unaccounted_ion_amount = init_charge_in_moles - ionic_charge_in_moles
    
    # Print comparison
    print("\n=== PYTHON CALCULATION BREAKDOWN ===")
    print(f"FARADAY_CONSTANT: {format_scientific(FARADAY_CONSTANT)} C/mol")
    print(f"init_charge: {format_scientific(init_charge)} C")
    print(f"init_charge_in_moles: {format_scientific(init_charge_in_moles)} mol")
    
    print("\nIon contributions to charge concentration:")
    for ion in sim.all_species:
        contribution = ion.elementary_charge * ion.init_vesicle_conc
        print(f"  Ion with charge {ion.elementary_charge}: {ion.elementary_charge} * {ion.init_vesicle_conc} = {format_scientific(contribution)} mol/L")
    
    print(f"Sum of ion_charge * concentration: {format_scientific(ionic_charge_conc)} mol/L")
    print(f"init_volume: {format_scientific(init_volume)} L")
    print(f"ionic_charge_in_moles = ionic_charge_conc * init_volume = {format_scientific(ionic_charge_in_moles)} mol")
    print(f"unaccounted_ion_amount = init_charge_in_moles - ionic_charge_in_moles = {format_scientific(unaccounted_ion_amount)} mol")
    
    print("\n=== C++ VALUES (FROM OUTPUT) ===")
    print("init_charge: 8.49487e-15 C")
    print("init_charge_in_moles (calculated): 8.80434e-20 mol")
    print("Total ionic charge concentration: -0.0039204 mol/L")
    print("init_volume: 9.20277e-18 L")
    print("ionic_charge_in_moles (calculated): -3.60784e-20 mol")
    print("unaccounted_ion_amount (calculated): 1.24122e-19 mol")
    
    print("\n=== COMPARISON OF KEY VALUES ===")
    print(f"Python init_charge: {format_scientific(init_charge)} C vs C++ init_charge: 8.49487e-15 C")
    print(f"Python ionic_charge_conc: {format_scientific(ionic_charge_conc)} mol/L vs C++ ionic_charge_conc: -0.0039204 mol/L")
    print(f"Python init_volume: {format_scientific(init_volume)} L vs C++ init_volume: 9.20277e-18 L")
    print(f"Python ionic_charge_in_moles: {format_scientific(ionic_charge_in_moles)} mol")
    print("C++ ionic_charge_in_moles (calculated): -3.60784e-20 mol")
    print(f"Python unaccounted_ion_amount: {format_scientific(unaccounted_ion_amount)} mol")
    print("C++ unaccounted_ion_amount (reported): 1.24122e-19 mol")
    
    # Calculate ratio between Python and C++ unaccounted_ion_amount
    cpp_unaccounted = 1.24122e-19
    ratio = cpp_unaccounted / unaccounted_ion_amount
    print(f"\nRatio (C++ / Python): {format_scientific(ratio)}")
    
    # Missing factor analysis
    missing_factor = ratio
    print(f"Missing factor might be: {missing_factor:.2f}")
    
    # Try to identify common factor issues
    common_factors = {
        "1000 (L to mL)": 1000,
        "10^3 (SI prefix kilo)": 10**3,
        "10^6 (SI prefix mega)": 10**6,
        "10^-3 (SI prefix milli)": 10**-3,
        "10^-6 (SI prefix micro)": 10**-6,
        "Avogadro's constant (approx)": 6.022e23,
        "Faraday constant": FARADAY_CONSTANT,
    }
    
    print("\nPossible explanations for the difference:")
    for name, factor in common_factors.items():
        if 0.9 < abs(missing_factor / factor) < 1.1:
            print(f"- Differs roughly by {name}")
        if 0.9 < abs(factor / missing_factor) < 1.1:
            print(f"- Differs roughly by 1/{name}")
    
    # Check for sum of ion concentrations
    total_positive_conc = 0
    total_negative_conc = 0
    for ion in sim.all_species:
        if ion.elementary_charge > 0:
            total_positive_conc += ion.init_vesicle_conc
        else:
            total_negative_conc += abs(ion.init_vesicle_conc)
    
    print(f"\nTotal positive ion concentration: {format_scientific(total_positive_conc)} mol/L")
    print(f"Total negative ion concentration: {format_scientific(total_negative_conc)} mol/L")
    print(f"Net charge concentration: {format_scientific(total_positive_conc - total_negative_conc)} mol/L")
    
    # Special debugging for c++ formula
    # In C++, it might be calculated as: init_charge/F - (elementary_charge * init_conc * 1000 * init_volume)
    # So let's try with the 1000 factor
    ionic_charge_in_moles_with_factor = ionic_charge_conc * 1000 * init_volume
    unaccounted_with_factor = init_charge_in_moles - ionic_charge_in_moles_with_factor
    
    print("\n=== TESTING WITH FACTOR OF 1000 (COMMON C++ MISTAKE) ===")
    print(f"ionic_charge_in_moles_with_factor = ionic_charge_conc * 1000 * init_volume = {format_scientific(ionic_charge_in_moles_with_factor)} mol")
    print(f"unaccounted_with_factor = init_charge_in_moles - ionic_charge_in_moles_with_factor = {format_scientific(unaccounted_with_factor)} mol")
    
    ratio_with_factor = 1.24122e-19 / unaccounted_with_factor
    print(f"Ratio (C++ / Python with factor): {format_scientific(ratio_with_factor)}")
    
    # Check if Na+ and K+ are missing from C++ calculation
    cl_charge_conc = -0.159  # Cl- has -1 charge and 0.159 M concentration
    h_charge_conc = 7.962143411069939e-05  # H+ has +1 charge and 7.96e-5 M concentration
    cpp_reported_charge_conc = -0.0039204
    
    print("\n=== CHECKING FOR MISSING IONS IN C++ CALCULATION ===")
    print(f"Cl- charge contribution: {format_scientific(cl_charge_conc)} mol/L")
    print(f"H+ charge contribution: {format_scientific(h_charge_conc)} mol/L")
    print(f"Sum of Cl- and H+ contributions: {format_scientific(cl_charge_conc + h_charge_conc)} mol/L")
    print(f"C++ reported total: {format_scientific(cpp_reported_charge_conc)} mol/L")
    
    if abs((cl_charge_conc + h_charge_conc) - cpp_reported_charge_conc) < 0.001:
        print("POSSIBLE ISSUE: C++ might only be considering Cl- and H+ ions, ignoring Na+ and K+")
    
    # Test using only Cl- and H+ in the calculation
    limited_ionic_charge_conc = cl_charge_conc + h_charge_conc
    limited_ionic_charge_in_moles = limited_ionic_charge_conc * init_volume
    limited_unaccounted = init_charge_in_moles - limited_ionic_charge_in_moles
    
    print(f"\nlimited_ionic_charge_in_moles (only Cl- and H+): {format_scientific(limited_ionic_charge_in_moles)} mol")
    print(f"limited_unaccounted (only Cl- and H+): {format_scientific(limited_unaccounted)} mol")
    
    ratio_limited = 1.24122e-19 / limited_unaccounted
    print(f"Ratio (C++ / Python with only Cl- and H+): {format_scientific(ratio_limited)}")

if __name__ == "__main__":
    compare_calculations() 