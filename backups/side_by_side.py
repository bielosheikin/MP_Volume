#!/usr/bin/env python
import sys
from pathlib import Path
import re

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))
from src.backend.simulation import Simulation, FARADAY_CONSTANT

def parse_cpp_output(file_path):
    """Parse the C++ debug output file to extract ion amounts and charge information"""
    try:
        with open(file_path, 'r') as f:
            cpp_output = f.read()
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    
    result = {}
    
    # Extract ion species data from the output
    ion_data = {}
    
    # Look for ion block patterns
    ion_blocks = re.findall(r'Ion: (\w+)\s+.*?Vesicle amount: ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+) mol.*?Elementary charge: ([-+]?\d+)', 
                           cpp_output, re.DOTALL)
    
    for match in ion_blocks:
        ion_name = match[0]
        amount = float(match[1])
        charge = int(match[2])
        
        if ion_name not in ion_data:
            ion_data[ion_name] = {
                'elementary_charge': charge,
                'amount': amount
            }
        else:
            # Update only if newer data (assuming later entries are more up-to-date)
            ion_data[ion_name].update({
                'elementary_charge': charge,
                'amount': amount
            })
    
    result['ion_species'] = ion_data
    
    # Extract unaccounted ion amount
    unaccounted_match = re.search(r'Unaccounted ion amount: ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+)', cpp_output)
    if unaccounted_match:
        result['unaccounted_ion_amount'] = float(unaccounted_match.group(1))
    
    # Extract charge information
    charge_match = re.search(r'Charge in Coulombs: ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+)', cpp_output)
    if charge_match:
        result['charge_in_coulombs'] = float(charge_match.group(1))
    
    return result

def get_python_data():
    """Get the ion charge data from the Python implementation"""
    sim = Simulation()
    
    # Calculate Python values
    ion_data = {}
    
    # Set ion amounts
    sim.set_ion_amounts()
    
    # Calculate unaccounted ion amount
    sim.get_unaccounted_ion_amount()
    
    # Get ion amounts and charges
    for ion in sim.all_species:
        ion_data[ion.display_name] = {
            'elementary_charge': ion.elementary_charge,
            'amount': ion.vesicle_amount
        }
    
    # Calculate total charge
    total_ionic_charge_amount = sum(ion.elementary_charge * ion.vesicle_amount for ion in sim.all_species)
    total_charge_in_moles = total_ionic_charge_amount + sim.unaccounted_ion_amounts
    total_charge_in_coulombs = total_charge_in_moles * FARADAY_CONSTANT
    
    result = {
        'ion_species': ion_data,
        'unaccounted_ion_amount': sim.unaccounted_ion_amounts,
        'total_ionic_charge_amount': total_ionic_charge_amount,
        'total_charge_in_moles': total_charge_in_moles,
        'charge_in_coulombs': total_charge_in_coulombs
    }
    
    return result

def compare_side_by_side(py_data, cpp_data):
    """Compare the Python and C++ data side by side"""
    print("\n===== SIDE-BY-SIDE COMPARISON =====")
    
    # List all ion species
    all_ions = set(list(py_data['ion_species'].keys()) + list(cpp_data.get('ion_species', {}).keys()))
    
    # Compare ion amounts and charges
    print("\nION AMOUNTS AND CHARGES:")
    print("--------------------------------------------------------------------------------------------------------------------------")
    print(f"{'Ion':<6} {'Elem Charge':<15} {'Python Amount':<25} {'C++ Amount':<25} {'Difference':<25}")
    print("--------------------------------------------------------------------------------------------------------------------------")
    
    py_total_charge_amount = 0.0
    cpp_total_charge_amount = 0.0
    
    for ion in sorted(all_ions):
        py_ion = py_data['ion_species'].get(ion, {})
        cpp_ion = cpp_data.get('ion_species', {}).get(ion, {})
        
        py_charge = py_ion.get('elementary_charge')
        cpp_charge = cpp_ion.get('elementary_charge')
        
        py_amount = py_ion.get('amount')
        cpp_amount = cpp_ion.get('amount')
        
        if py_charge is not None and py_amount is not None:
            py_contrib = py_charge * py_amount
            py_total_charge_amount += py_contrib
        else:
            py_contrib = None
        
        if cpp_charge is not None and cpp_amount is not None:
            cpp_contrib = cpp_charge * cpp_amount
            cpp_total_charge_amount += cpp_contrib
        else:
            cpp_contrib = None
        
        # Calculate difference if both values exist
        diff = ""
        if py_amount is not None and cpp_amount is not None:
            diff = py_amount - cpp_amount
        
        print(f"{ion:<6} {py_charge if py_charge is not None else 'N/A':<15} "
              f"{py_amount:.20e if py_amount is not None else 'N/A':<25} "
              f"{cpp_amount:.20e if cpp_amount is not None else 'N/A':<25} "
              f"{diff:.20e if diff != '' else 'N/A':<25}")
    
    print("--------------------------------------------------------------------------------------------------------------------------")
    
    # Compare total ion charge contribution
    print("\nTOTAL CHARGE CALCULATION:")
    print(f"{'Component':<25} {'Python Value':<25} {'C++ Value':<25} {'Difference':<25}")
    print("--------------------------------------------------------------------------------------------------------------------------")
    
    # Sum of ion charge * amount
    diff = py_total_charge_amount - cpp_total_charge_amount
    print(f"{'Sum(ion_charge * amount)':<25} {py_total_charge_amount:.20e} {cpp_total_charge_amount:.20e} {diff:.20e}")
    
    # Unaccounted ion amount
    py_unaccounted = py_data['unaccounted_ion_amount']
    cpp_unaccounted = cpp_data.get('unaccounted_ion_amount')
    if cpp_unaccounted is not None:
        diff = py_unaccounted - cpp_unaccounted
        print(f"{'Unaccounted ion amount':<25} {py_unaccounted:.20e} {cpp_unaccounted:.20e} {diff:.20e}")
    else:
        print(f"{'Unaccounted ion amount':<25} {py_unaccounted:.20e} {'N/A':<25} {'N/A':<25}")
    
    # Total charge in moles
    py_total_moles = py_data['total_charge_in_moles']
    cpp_total_moles = None
    if cpp_total_charge_amount is not None and cpp_unaccounted is not None:
        cpp_total_moles = cpp_total_charge_amount + cpp_unaccounted
    
    if cpp_total_moles is not None:
        diff = py_total_moles - cpp_total_moles
        print(f"{'Total charge in moles':<25} {py_total_moles:.20e} {cpp_total_moles:.20e} {diff:.20e}")
    else:
        print(f"{'Total charge in moles':<25} {py_total_moles:.20e} {'N/A':<25} {'N/A':<25}")
    
    # Total charge in Coulombs
    py_coulombs = py_data['charge_in_coulombs']
    cpp_coulombs = cpp_data.get('charge_in_coulombs')
    
    if cpp_coulombs is not None:
        diff = py_coulombs - cpp_coulombs
        print(f"{'Total charge in Coulombs':<25} {py_coulombs:.20e} {cpp_coulombs:.20e} {diff:.20e}")
    else:
        print(f"{'Total charge in Coulombs':<25} {py_coulombs:.20e} {'N/A':<25} {'N/A':<25}")
    
    # Check for missing ions
    print("\nMISSING IONS:")
    missing_in_cpp = [ion for ion in py_data['ion_species'] if ion not in cpp_data.get('ion_species', {})]
    missing_in_py = [ion for ion in cpp_data.get('ion_species', {}) if ion not in py_data['ion_species']]
    
    if missing_in_cpp:
        print(f"Ions missing in C++ implementation: {', '.join(missing_in_cpp)}")
    else:
        print("No ions missing in C++ implementation")
    
    if missing_in_py:
        print(f"Ions missing in Python implementation: {', '.join(missing_in_py)}")
    else:
        print("No ions missing in Python implementation")
    
    # Summary of findings
    print("\nANALYSIS SUMMARY:")
    if missing_in_cpp:
        print(f"WARNING: The C++ implementation is missing these ions: {', '.join(missing_in_cpp)}")
        print(f"This likely explains the charge calculation discrepancy.")
        total_missing_contribution = sum(py_data['ion_species'][ion]['elementary_charge'] * 
                                         py_data['ion_species'][ion]['amount'] 
                                         for ion in missing_in_cpp)
        print(f"Total charge contribution from missing ions: {total_missing_contribution:.20e} mol")
        print(f"This would account for {total_missing_contribution/py_total_charge_amount*100:.2f}% of the total ion charge in Python")
    elif abs(py_total_charge_amount - cpp_total_charge_amount) > 1e-20:
        print("WARNING: There's a significant difference in the ion charge calculation, but no missing ions.")
        print("Check for differences in ion amounts or calculation methods.")
    else:
        print("The ion charge calculations appear to match closely between Python and C++.")
    
    if cpp_unaccounted is not None and abs(py_unaccounted - cpp_unaccounted) > 1e-20:
        print(f"WARNING: There's a significant difference in the unaccounted ion amount calculation.")
        print(f"Python: {py_unaccounted:.20e} mol, C++: {cpp_unaccounted:.20e} mol")
    
    if cpp_coulombs is not None and abs(py_coulombs - cpp_coulombs) > 1e-15:
        print(f"WARNING: There's a significant difference in the final charge in Coulombs.")
        print(f"Python: {py_coulombs:.20e} C, C++: {cpp_coulombs:.20e} C")
        print(f"Difference: {py_coulombs - cpp_coulombs:.20e} C")

def main():
    if len(sys.argv) < 2:
        print("Usage: python side_by_side.py <cpp_debug_output_file>")
        return
    
    cpp_data = parse_cpp_output(sys.argv[1])
    py_data = get_python_data()
    
    if cpp_data and py_data:
        compare_side_by_side(py_data, cpp_data)

if __name__ == "__main__":
    main() 