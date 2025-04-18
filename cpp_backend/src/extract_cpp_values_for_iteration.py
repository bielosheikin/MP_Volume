#!/usr/bin/env python
import re
import sys

def extract_cpp_values_for_iteration(cpp_output, iteration):
    """Extract values for a specific iteration from C++ debug output"""
    values = {}
    lines = cpp_output.split('\n')
    
    # Find the section for the current iteration
    iter_start = None
    iter_end = None
    for i, line in enumerate(lines):
        if f"=== ITERATION {iteration} " in line:
            iter_start = i
        elif iter_start is not None and (f"=== ITERATION {iteration+1} " in line or "=== SIMULATION COMPLETE ===" in line):
            iter_end = i
            break
    
    if iter_start is None:
        print(f"Warning: Iteration {iteration} not found in C++ output")
        return values
    
    if iter_end is None:
        iter_end = len(lines)
    
    # Extract values from this iteration section
    iter_section = lines[iter_start:iter_end]
    
    # Extract volume, capacitance, charge, voltage, and pH
    for i, line in enumerate(iter_section):
        if "Final volume:" in line:
            try:
                values["volume"] = float(line.split(":")[-1].strip().split()[0])
            except (ValueError, IndexError):
                pass
        
        elif "Final capacitance:" in line:
            try:
                values["capacitance"] = float(line.split(":")[-1].strip().split()[0])
            except (ValueError, IndexError):
                pass
        
        elif "Final charge:" in line:
            try:
                values["charge"] = float(line.split(":")[-1].strip().split()[0])
            except (ValueError, IndexError):
                pass
        
        elif "Final voltage:" in line:
            try:
                values["voltage"] = float(line.split(":")[-1].strip().split()[0])
            except (ValueError, IndexError):
                pass
        
        elif "Final pH:" in line:
            try:
                values["pH"] = float(line.split(":")[-1].strip().split()[0])
            except (ValueError, IndexError):
                pass
    
    # Extract ion concentrations and amounts from updateIonAmounts
    ion_amount_pattern = re.compile(r'(\w+): ([\d.e+-]+) \+ \([\d.e+-]+ \* [\d.e+-]+\) = ([\d.e+-]+) mol')
    for line in iter_section:
        match = ion_amount_pattern.search(line)
        if match:
            ion_name = match.group(1)
            final_amount = float(match.group(3))
            values[f"{ion_name}_amount"] = final_amount
    
    # Extract channel flux values
    channel_flux_pattern = re.compile(r'(\w+): ([\d.e+-]+) mol/s')
    for i, line in enumerate(iter_section):
        if "Computing channel fluxes:" in line:
            # Process subsequent lines containing channel flux values
            j = i + 1
            while j < len(iter_section) and ":" in iter_section[j] and "mol/s" in iter_section[j]:
                match = channel_flux_pattern.search(iter_section[j])
                if match:
                    channel_name = match.group(1)
                    flux_value = float(match.group(2))
                    values[f"flux_{channel_name}"] = flux_value
                j += 1
    
    # Extract ion concentrations
    conc_pattern = re.compile(r'Vesicle concentration: ([\d.e+-]+) M')
    for i, line in enumerate(iter_section):
        if conc_pattern.search(line):
            # Look backward for the ion name
            for prev_i in range(max(0, i-5), i):
                if "Ion:" in iter_section[prev_i]:
                    ion_name = iter_section[prev_i].split(":")[-1].strip()
                    conc_value = float(conc_pattern.search(line).group(1))
                    values[f"{ion_name}_conc"] = conc_value
                    break
    
    return values

def main():
    if len(sys.argv) != 3:
        print("Usage: python extract_cpp_values_for_iteration.py <cpp_debug_output_file> <iteration>")
        return
    
    cpp_output_file = sys.argv[1]
    iteration = int(sys.argv[2])
    
    with open(cpp_output_file, 'r') as f:
        cpp_output = f.read()
    
    values = extract_cpp_values_for_iteration(cpp_output, iteration)
    
    print("\nExtracted values for iteration", iteration)
    for key, value in sorted(values.items()):
        print(f"{key}: {value}")

if __name__ == "__main__":
    main() 