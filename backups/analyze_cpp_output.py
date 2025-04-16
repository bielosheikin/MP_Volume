#!/usr/bin/env python
import re
import sys

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
    
    # Look for this pattern
    # Ion: cl
    #   Vesicle amount: 1.4632e-18 mol
    ion_blocks = re.findall(r'Ion: (\w+).*?Vesicle amount: ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+) mol.*?Elementary charge: ([-+]?\d+)', 
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
            # Update only if newer data
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

def format_cpp_values(cpp_data):
    """Format the parsed C++ values for comparison with Python"""
    if not cpp_data:
        return
    
    print("\n==== EXTRACTED C++ ION CHARGE DATA ====")
    
    # Print each ion's amount and contribution to charge
    print("\nION AMOUNTS:")
    print(f"{'Ion':<5} {'Elem.Charge':<12} {'Amount (mol)':<25} {'Charge Contrib (mol)':<25}")
    print("-" * 70)
    
    total_ionic_charge_amount = 0.0
    for ion_name, ion_info in cpp_data.get('ion_species', {}).items():
        charge = ion_info.get('elementary_charge', 0)
        amount = ion_info.get('amount', 0)
        charge_amount = charge * amount
        total_ionic_charge_amount += charge_amount
        print(f"{ion_name:<5} {charge:<12} {amount:.20e} {charge_amount:.20e}")
    
    print(f"\nTotal sum(charge * amount): {total_ionic_charge_amount:.20e} mol")
    
    if 'unaccounted_ion_amount' in cpp_data:
        unaccounted = cpp_data['unaccounted_ion_amount']
        print(f"Unaccounted ion amount: {unaccounted:.20e} mol")
        
        # Calculate total charge in moles
        total_charge_in_moles = total_ionic_charge_amount + unaccounted
        print(f"Total charge in moles: {total_charge_in_moles:.20e} mol")
    
    if 'charge_in_coulombs' in cpp_data:
        print(f"Total charge in Coulombs: {cpp_data['charge_in_coulombs']:.20e} C")
    
    # Summary for comparison with Python
    print("\nSUMMARY FOR COMPARISON WITH PYTHON:")
    print(f"Total sum(ion_charge * amount): {total_ionic_charge_amount:.20e} mol")
    if 'unaccounted_ion_amount' in cpp_data:
        print(f"Unaccounted ion amount: {cpp_data['unaccounted_ion_amount']:.20e} mol")
    if 'charge_in_coulombs' in cpp_data:
        print(f"Total charge in Coulombs: {cpp_data['charge_in_coulombs']:.20e} C")
    
    # Missing ions compared to Python
    print("\nCheck if any expected ions are missing from C++ output:")
    expected_ions = ['cl', 'h', 'na', 'k']
    for ion in expected_ions:
        if ion not in cpp_data.get('ion_species', {}):
            print(f"  WARNING: Ion '{ion}' is missing from C++ output!")

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_cpp_output.py <cpp_debug_output_file>")
        return
    
    cpp_data = parse_cpp_output(sys.argv[1])
    if cpp_data:
        format_cpp_values(cpp_data)

if __name__ == "__main__":
    main() 