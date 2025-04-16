#!/usr/bin/env python
import re
import sys

def scan_ion_names(file_path):
    """Scan a C++ debug output file for all unique ion names mentioned"""
    try:
        with open(file_path, 'r') as f:
            cpp_output = f.read()
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None

    # Find all mentions of "Ion: X" in the log
    ion_matches = re.findall(r'Ion: (\w+)', cpp_output)
    unique_ions = set(ion_matches)
    
    # Count occurrences of each ion
    ion_counts = {}
    for ion in ion_matches:
        if ion in ion_counts:
            ion_counts[ion] += 1
        else:
            ion_counts[ion] = 1
    
    # Check for specific ions we expect to see
    expected_ions = ['cl', 'h', 'na', 'k']
    missing_ions = [ion for ion in expected_ions if ion not in unique_ions]
    
    # Look for vesicle amount for each ion
    ion_amounts = {}
    for ion in unique_ions:
        # Look for vesicle amount pattern
        amount_match = re.search(rf'Ion: {ion}.*?Vesicle amount: ([-+]?\d*\.\d+[eE][-+]?\d+|\d+\.\d+) mol', 
                               cpp_output, re.DOTALL)
        if amount_match:
            ion_amounts[ion] = float(amount_match.group(1))
    
    # Look for updateCharge debug output to check which ions are included
    update_charge_section = re.search(r'updateCharge calculation:.*?(?=Final charge:)', cpp_output, re.DOTALL)
    ions_in_charge_calc = []
    if update_charge_section:
        charge_calc_text = update_charge_section.group(0)
        # Find ions mentioned in the charge calculation
        ions_in_calc = re.findall(r'(\w+): .* = (\S+) mol', charge_calc_text)
        ions_in_charge_calc = [ion[0] for ion in ions_in_calc]
    
    # Print results
    print("\n==== C++ ION IMPLEMENTATION CHECK ====")
    print(f"Found {len(unique_ions)} unique ions in the debug output:")
    for ion, count in ion_counts.items():
        print(f"  {ion}: mentioned {count} times")
    
    print("\nExpected ions:")
    for ion in expected_ions:
        if ion in unique_ions:
            print(f"  {ion}: FOUND")
        else:
            print(f"  {ion}: MISSING")
    
    if missing_ions:
        print(f"\nWARNING: The following ions are missing from the C++ debug output: {', '.join(missing_ions)}")
        print("This likely explains any charge calculation discrepancies between Python and C++.")
    else:
        print("\nAll expected ions appear in the C++ debug output.")
    
    print("\nIon amounts found in C++ output:")
    for ion, amount in ion_amounts.items():
        print(f"  {ion}: {amount}")
    
    if ions_in_charge_calc:
        print("\nIons included in the charge calculation:")
        for ion in ions_in_charge_calc:
            print(f"  {ion}")
        
        missing_in_calc = [ion for ion in unique_ions if ion not in ions_in_charge_calc]
        if missing_in_calc:
            print(f"\nWARNING: The following ions appear in the debug output but not in the charge calculation: {', '.join(missing_in_calc)}")
    else:
        print("\nNo charge calculation details found in the debug output.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python check_cpp_ion_completeness.py <cpp_debug_output_file>")
        return
    
    scan_ion_names(sys.argv[1])

if __name__ == "__main__":
    main() 