#!/usr/bin/env python3
"""
Comparison script between legacy and current simulation systems.

This script helps verify that the legacy and current simulation systems
produce identical results when run with the same parameters.
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from pathlib import Path

# Add both systems to path
legacy_path = Path(__file__).parent / "legacy"
current_path = Path(__file__).parent / "src"
sys.path.insert(0, str(legacy_path))
sys.path.insert(0, str(current_path))

# Import legacy system
from legacy.utilities import simulation_tools as legacy_sim
from legacy.config import *

# Import current system
from src.backend.simulation import Simulation
from src.backend.ion_channels import IonChannel
from src.backend.ion_species import IonSpecies
from src.backend.ion_and_channels_link import IonChannelsLink

class SimulationComparator:
    """Compare legacy and current simulation systems."""
    
    def __init__(self):
        """Initialize the comparator with default parameters."""
        self.setup_common_parameters()
    
    def setup_common_parameters(self):
        """Set up identical parameters for both systems."""
        # Time parameters
        self.dt = 0.001  # time step
        self.T = 1000.0  # total time (faster testing but long enough to see differences)
        self.debug_steps = 5  # Number of steps to debug in detail
        
        # Physical constants
        self.RT = 2578.5871
        self.F = 96485.0
        self.c_spec = 0.01
        self.buffer_capacity_t0 = 5.0e-4
        
        # Vesicle properties
        self.r = 1.3e-6
        self.V0 = (4.0/3.0) * np.pi * (self.r**3)
        self.A0 = 4.0 * np.pi * (self.r**2)
        self.A_from_V_const = (36.0*np.pi)**(1/3)
        self.U0 = 40e-3
        
        # Ion concentrations (M)
        self.external_concentrations = {
            'cl': 20e-3,
            'na': 10e-3, 
            'k': 140e-3,
            'pH_o': 7.2
        }
        
        self.internal_concentrations = {
            'cl': 159e-3,  # "high" chloride condition
            'na': 150e-3,
            'k': 5e-3,
            'pH_i': 7.4
        }
        
        # Calculate hydrogen concentrations
        self.hfree_o = 10**(-self.external_concentrations['pH_o'])
        self.hfree_i = 10**(-self.internal_concentrations['pH_i'])
        self.htotal_o = self.hfree_o / self.buffer_capacity_t0
        self.htotal_i = self.hfree_i / self.buffer_capacity_t0
        
        # Channel conductances (S/m²)
        self.conductances = {
            'asor': 8e-5,
            'tpc': 2e-6,
            'k': 0.0,
            'clc': 1e-7,
            'nhe': 0.0,
            'vatpase': 8e-9,
            'hleak': 1.6e-8
        }
        
        # Dependency parameters - Wild type ASOR and CLC
        self.asor_params = {
            'pH_k2': 3.0,
            'pH_half': 5.4,
            'U_k2': 80.0,
            'U_half': -40e-3
        }
        
        self.clc_params = {
            'pH_k2': 1.5,  # Note: positive for CLC in legacy (uses pH_half - pH formula)
            'pH_half': 5.5,
            'U_k2': 80.0,
            'U_half': -40e-3
        }
    
    def run_legacy_simulation(self):
        """Run the legacy simulation system."""
        print("Running legacy simulation...")
        
        # Prepare legacy parameters
        external_ions_concentrations = [
            self.external_concentrations['cl'],
            self.external_concentrations['na'],
            self.htotal_o,
            self.external_concentrations['k']
        ]
        
        # Calculate X_amount
        Q0 = self.U0 * self.A0 * self.c_spec
        X_amount = (Q0/self.F) - ((self.internal_concentrations['na'] + 
                                   self.internal_concentrations['k'] + 
                                   self.htotal_i - 
                                   self.internal_concentrations['cl']) * self.V0 * 1000)
        
        # Initial ion amounts (moles)
        initial_ions_amounts = np.array([
            self.internal_concentrations['cl'] * self.V0 * 1000,    # Cl
            self.internal_concentrations['na'] * self.V0 * 1000,    # Na  
            self.htotal_i * self.V0 * 1000,                         # H
            self.internal_concentrations['k'] * self.V0 * 1000      # K
        ])
        
        Sum_initial_amounts = (initial_ions_amounts[0] + initial_ions_amounts[1] + 
                              abs(X_amount) + initial_ions_amounts[3])
        
        # Legacy conductances dictionary
        G = {
            'ASOR': self.conductances['asor'],
            'TPC': self.conductances['tpc'],
            'K': self.conductances['k'],
            'CLC': self.conductances['clc'],
            'NHE': self.conductances['nhe'],
            'vATPase': self.conductances['vatpase'],
            'H_leak': self.conductances['hleak']
        }
        
        # Legacy parameters
        parameters = {
            'dt': self.dt,
            'T': self.T,
            'G': G,
            'external_ions_concentrations': external_ions_concentrations,
            'A_from_V_const': self.A_from_V_const,
            'X_amount': X_amount,
            'buffer_capacity_t0': self.buffer_capacity_t0,
            'V_t0': self.V0,
            'c_spec': self.c_spec,
            'RT': self.RT,
            'F': self.F,
            'pH_i': self.internal_concentrations['pH_i'],
            'U0': self.U0,
            'A0': self.A0,
            'C0': self.A0 * self.c_spec,
            'Sum_initial_amounts': Sum_initial_amounts,
            'ASOR_pH_k2': self.asor_params['pH_k2'],
            'ASOR_pH_half': self.asor_params['pH_half'],
            'ASOR_U_k2': self.asor_params['U_k2'],
            'ASOR_U_half': self.asor_params['U_half'],
            'CLC_pH_k2': self.clc_params['pH_k2'],
            'CLC_pH_half': self.clc_params['pH_half'],
            'CLC_U_k2': self.clc_params['U_k2'],
            'CLC_U_half': self.clc_params['U_half']
        }
        
        # Run legacy simulation
        results = legacy_sim.run_simulation(initial_ions_amounts, parameters)
        
        # DEBUG: Check actual time array length and parameters
        print(f"DEBUG Legacy simulation:")
        print(f"  - T parameter passed: {parameters['T']}")
        print(f"  - dt parameter passed: {parameters['dt']}")
        print(f"  - Expected time points: {int(parameters['T']/parameters['dt'])+1}")
        if 'internal_ions' in results and 'Cl' in results['internal_ions']:
            actual_points = len(results['internal_ions']['Cl']['concentrations'])
            print(f"  - Actual time points returned: {actual_points}")
            if actual_points > 0:
                print(f"  - Actual time span: 0 to {(actual_points-1) * parameters['dt']:.1f} seconds")
        
        # DEBUG: Show actual initial values used in legacy simulation
        print(f"\nDEBUG Legacy ACTUAL initial values:")
        print(f"  - Initial ion amounts (moles): {initial_ions_amounts}")
        print(f"  - Initial volume (m³): {self.V0}")
        print(f"  - Initial concentrations calculated from amounts:")
        for i, ion in enumerate(['Cl', 'Na', 'H', 'K']):
            conc = initial_ions_amounts[i] / (self.V0 * 1000)
            print(f"    - {ion}: {conc:.6e} M")
        print(f"  - X_amount (unaccounted): {X_amount:.6e} moles")
        print(f"  - Sum_initial_amounts: {Sum_initial_amounts:.6e} moles")
        
        # Check first few time points of concentrations
        if 'internal_ions' in results:
            print(f"  - LEGACY t=0 concentrations:")
            for ion in ['Cl', 'Na', 'H', 'K']:
                if ion in results['internal_ions']:
                    conc_t0 = results['internal_ions'][ion]['concentrations'][0]
                    print(f"    - {ion}: {conc_t0:.6e} M")
        
        return results, parameters
    
    def run_current_simulation(self):
        """Run the current simulation system using defaults."""
        print("Running current simulation...")
        
        # Import default configurations
        from src.backend.default_channels import default_channels
        from src.backend.default_ion_species import default_ion_species
        from src.backend.ion_and_channels_link import IonChannelsLink
        
        # Use default components with matched parameters
        vesicle_params = {
            "init_radius": self.r,
            "init_voltage": self.U0,
            "init_pH": self.internal_concentrations['pH_i'],
        }
        
        exterior_params = {
            "pH": self.external_concentrations['pH_o'],
        }
        
        # Create simulation with defaults but our matched time parameters
        simulation = Simulation(
            channels=default_channels,
            species=default_ion_species,
            ion_channel_links=IonChannelsLink(use_defaults=True),
            vesicle_params=vesicle_params,
            exterior_params=exterior_params,
            time_step=self.dt,
            total_time=self.T,
            temperature=310.13274319979337,  # Use precise temperature that gives legacy RT = 2578.5871
            init_buffer_capacity=self.buffer_capacity_t0
        )
        
        # Both systems should use the same RT value consistently
        print(f"Using consistent RT value (2578.5871) for all channels in both systems")
        print(f"Standard nernst_constant: {simulation.nernst_constant:.8f}")
        
        print(f"Channels: {list(simulation.channels.keys())}")
        print(f"Ion-channel links: {simulation.ion_channel_links.links}")
        
        # Run simulation
        histories = simulation.run()
        
        # DEBUG: Check actual time array length and parameters  
        print(f"DEBUG Current simulation:")
        print(f"  - T parameter set: {simulation.total_time}")
        print(f"  - dt parameter set: {simulation.time_step}")
        print(f"  - Expected time points: {int(simulation.total_time/simulation.time_step)+1}")
        if 'simulation_time' in histories.histories:
            actual_points = len(histories.histories['simulation_time'])
            print(f"  - Actual time points returned: {actual_points}")
            if actual_points > 0:
                time_array = histories.histories['simulation_time']
                print(f"  - Actual time span: {time_array[0]:.1f} to {time_array[-1]:.1f} seconds")
        
        # DEBUG: Show actual initial values used in current simulation
        print(f"\nDEBUG Current ACTUAL initial values:")
        print(f"  - Initial vesicle volume (m³): {simulation.vesicle.init_volume}")
        print(f"  - Initial vesicle voltage (V): {simulation.vesicle.init_charge / simulation.vesicle.init_capacitance}")
        print(f"  - Unaccounted ion amounts (moles): {simulation.unaccounted_ion_amounts}")
        print(f"  - Species initial values:")
        for species_name, species in simulation.species.items():
            print(f"    - {species_name}:")
            print(f"      - init_vesicle_conc: {species.init_vesicle_conc:.6e} M")
            print(f"      - exterior_conc: {species.exterior_conc:.6e} M")
            print(f"      - vesicle_amount: {species.vesicle_amount:.6e} moles")
            print(f"      - vesicle_conc: {species.vesicle_conc:.6e} M")
        
        # Check first few time points of concentrations 
        print(f"  - CURRENT t=0 concentrations from histories:")
        for ion in ['cl', 'na', 'h', 'k']:
            if f'{ion}_vesicle_conc' in histories.histories:
                conc_t0 = histories.histories[f'{ion}_vesicle_conc'][0]
                print(f"    - {ion}: {conc_t0:.6e} M")
        
        return simulation, histories
    
    def compare_results(self, legacy_results, current_simulation, current_histories):
        """Compare the results from both simulation systems."""
        print("\nComparing results...")
        
        # Create time arrays
        legacy_time = np.arange(0, self.T, self.dt)
        current_time = np.array(current_histories.histories['simulation_time'])
        
        # TIMING ALIGNMENT FIX: Shift legacy data to align with current timing
        # Legacy voltage[N] uses ion amounts from step N-1, while Current voltage[N] uses step N
        # To compare equivalent physical states, we shift legacy data backward by 1 step
        print("🔧 APPLYING TIMING ALIGNMENT:")
        print("   Legacy data shifted backward by 1 step to align physical states")
        print("   This eliminates the algorithmic timing difference for visual comparison")
        
        def align_legacy_data(legacy_data):
            """Shift legacy data backward by 1 step to align with current timing"""
            if len(legacy_data) > 1:
                return legacy_data[1:]  # Skip first point, use [1:] to align with current [0:]
            return legacy_data
        
        def align_legacy_time():
            """Adjust legacy time array to match aligned data"""
            if len(legacy_time) > 1:
                return legacy_time[1:]  # Corresponding time points for shifted data
            return legacy_time
        
        # Aligned legacy time for interpolation
        aligned_legacy_time = align_legacy_time()
        
        # Interpolate current results to match aligned legacy time points
        def interpolate_to_legacy_time(current_data):
            if len(current_time) != len(current_data):
                print(f"Warning: Time length mismatch. Time: {len(current_time)}, Data: {len(current_data)}")
                min_len = min(len(current_time), len(current_data))
                return np.interp(aligned_legacy_time, current_time[:min_len], current_data[:min_len])
            return np.interp(aligned_legacy_time, current_time, current_data)
        
        # Compare ion concentrations
        print("\nIon Concentration Comparison:")
        print("-" * 50)
        
        ion_names = ['Cl', 'Na', 'H', 'K']
        ion_keys = ['cl', 'na', 'h', 'k']
        
        max_differences = {}
        
        for i, (legacy_name, current_key) in enumerate(zip(ion_names, ion_keys)):
            legacy_conc_raw = legacy_results['internal_ions'][legacy_name]['concentrations']
            legacy_conc = align_legacy_data(legacy_conc_raw)  # Apply timing alignment
            
            # Get current concentrations
            current_conc_raw = current_histories.histories[f'{current_key}_vesicle_conc']
            current_conc = interpolate_to_legacy_time(current_conc_raw)
            
            # Calculate differences
            abs_diff = np.abs(legacy_conc - current_conc)
            rel_diff = abs_diff / (np.abs(legacy_conc) + 1e-12) * 100  # Relative difference in %
            
            max_abs_diff = np.max(abs_diff)
            max_rel_diff = np.max(rel_diff)
            
            max_differences[legacy_name] = {
                'abs': max_abs_diff,
                'rel': max_rel_diff
            }
            
            print(f"{legacy_name:2s}: Max abs diff = {max_abs_diff:.2e} M, Max rel diff = {max_rel_diff:.2f}%")
        
        # Compare other variables
        print("\nOther Variables Comparison:")
        print("-" * 50)
        
        # Volume
        legacy_volume_raw = legacy_results['other_variables']['vesicle_parameters']['V']
        legacy_volume = align_legacy_data(legacy_volume_raw)  # Apply timing alignment
        # Current system tracking
        current_volume = interpolate_to_legacy_time(current_histories.histories['Vesicle_volume'])
        volume_diff = np.max(np.abs(legacy_volume - current_volume))
        print(f"Volume: Max abs diff = {volume_diff:.2e} m³")
        
        # pH
        legacy_pH_raw = legacy_results['other_variables']['vesicle_parameters']['pH']
        legacy_pH = align_legacy_data(legacy_pH_raw)  # Apply timing alignment
        # Current system tracking
        current_pH = interpolate_to_legacy_time(current_histories.histories['Vesicle_pH'])
        pH_diff = np.max(np.abs(legacy_pH - current_pH))
        print(f"pH: Max abs diff = {pH_diff:.4f}")
        
        # Voltage - Apply timing alignment for visual comparison
        legacy_voltage_raw = legacy_results['other_variables']['vesicle_parameters']['U']
        legacy_voltage = align_legacy_data(legacy_voltage_raw)  # Apply timing alignment
        current_voltage = interpolate_to_legacy_time(current_histories.histories['Vesicle_voltage'])
        voltage_diff = np.max(np.abs(legacy_voltage - current_voltage))
        print(f"Voltage: Max abs diff = {voltage_diff:.2e} V")
        
        # Create summary
        print("\nSUMMARY:")
        print("=" * 50)
        
        tolerance_abs = 1e-6  # Absolute tolerance
        tolerance_rel = 1.0   # Relative tolerance (%)
        
        all_good = True
        for ion, diffs in max_differences.items():
            if diffs['abs'] > tolerance_abs or diffs['rel'] > tolerance_rel:
                all_good = False
                print(f"❌ {ion} concentrations differ significantly!")
            else:
                print(f"✓ {ion} concentrations match within tolerance")
        
        if volume_diff > tolerance_abs:
            all_good = False
            print("❌ Volume differs significantly!")
        else:
            print("✓ Volume matches within tolerance")
            
        if pH_diff > 0.01:  # pH tolerance
            all_good = False
            print("❌ pH differs significantly!")
        else:
            print("✓ pH matches within tolerance")
            
        if voltage_diff > 1e-4:  # Voltage tolerance
            all_good = False
            print("❌ Voltage differs significantly!")
        else:
            print("✓ Voltage matches within tolerance")
        
        if all_good:
            print("\n🎉 SUCCESS: Both systems produce nearly identical results!")
        else:
            print("\n⚠️  WARNING: Significant differences detected!")
        
        return {
            'ion_differences': max_differences,
            'volume_diff': volume_diff,
            'pH_diff': pH_diff,
            'voltage_diff': voltage_diff,
            'all_match': all_good
        }
    
    def plot_comparison(self, legacy_results, current_simulation, current_histories):
        """Create comparison plots."""
        print("\nCreating comparison plots...")
        
        # Create time arrays
        legacy_time = np.arange(0, self.T, self.dt)
        current_time = np.array(current_histories.histories['simulation_time'])
        
        # TIMING ALIGNMENT FIX: Apply same alignment as in compare_results
        def align_legacy_data(legacy_data):
            """Shift legacy data backward by 1 step to align with current timing"""
            if len(legacy_data) > 1:
                return legacy_data[1:]  # Skip first point, use [1:] to align with current [0:]
            return legacy_data
        
        def align_legacy_time():
            """Adjust legacy time array to match aligned data"""
            if len(legacy_time) > 1:
                return legacy_time[1:]  # Corresponding time points for shifted data
            return legacy_time
        
        # Aligned legacy time for interpolation
        aligned_legacy_time = align_legacy_time()
        
        # Interpolate current results to match aligned legacy time points
        def interpolate_to_legacy_time(current_data):
            if len(current_time) != len(current_data):
                min_len = min(len(current_time), len(current_data))
                return np.interp(aligned_legacy_time, current_time[:min_len], current_data[:min_len])
            return np.interp(aligned_legacy_time, current_time, current_data)
        
        # Create figure with 3x3 grid to include voltage
        fig, axes = plt.subplots(3, 3, figsize=(18, 12))
        fig.suptitle('Legacy vs Current Simulation Comparison (Timing Aligned)', fontsize=16)
        
        # Ion concentrations
        ion_names = ['Cl', 'Na', 'H', 'K']
        ion_keys = ['cl', 'na', 'h', 'k']
        
        for i, (legacy_name, current_key) in enumerate(zip(ion_names[:4], ion_keys[:4])):
            if i < 4:
                ax = axes[i//3, i%3]  # Arrange in 3x3 grid
                legacy_conc_raw = legacy_results['internal_ions'][legacy_name]['concentrations']
                legacy_conc = align_legacy_data(legacy_conc_raw)  # Apply timing alignment
                current_conc = interpolate_to_legacy_time(current_histories.histories[f'{current_key}_vesicle_conc'])
                
                ax.plot(aligned_legacy_time, legacy_conc * 1000, 'b-', label='Legacy', linewidth=2)
                ax.plot(aligned_legacy_time, current_conc * 1000, 'r--', label='Current', linewidth=2)
                ax.set_title(f'{legacy_name}⁻ Concentration' if legacy_name == 'Cl' else f'{legacy_name}⁺ Concentration')
                ax.set_xlabel('Time (s)')
                ax.set_ylabel('Concentration (mM)')
                ax.legend()
                ax.grid(True, alpha=0.3)
        
        # Volume
        legacy_volume_raw = legacy_results['other_variables']['vesicle_parameters']['V']
        legacy_volume = align_legacy_data(legacy_volume_raw)  # Apply timing alignment
        current_volume = interpolate_to_legacy_time(current_histories.histories['Vesicle_volume'])
        
        axes[1, 1].plot(aligned_legacy_time, legacy_volume * 1e18, 'b-', label='Legacy', linewidth=2)
        axes[1, 1].plot(aligned_legacy_time, current_volume * 1e18, 'r--', label='Current', linewidth=2)
        axes[1, 1].set_title('Volume')
        axes[1, 1].set_xlabel('Time (s)')
        axes[1, 1].set_ylabel('Volume (μm³)')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        # pH
        legacy_pH_raw = legacy_results['other_variables']['vesicle_parameters']['pH']
        legacy_pH = align_legacy_data(legacy_pH_raw)  # Apply timing alignment
        current_pH = interpolate_to_legacy_time(current_histories.histories['Vesicle_pH'])
        
        axes[1, 2].plot(aligned_legacy_time, legacy_pH, 'b-', label='Legacy', linewidth=2)
        axes[1, 2].plot(aligned_legacy_time, current_pH, 'r--', label='Current', linewidth=2)
        axes[1, 2].set_title('pH')
        axes[1, 2].set_xlabel('Time (s)')
        axes[1, 2].set_ylabel('pH')
        axes[1, 2].legend()
        axes[1, 2].grid(True, alpha=0.3)
        
        # Voltage - No timing adjustment needed after fixing order of operations
        legacy_voltage_raw = legacy_results['other_variables']['vesicle_parameters']['U']
        legacy_voltage = align_legacy_data(legacy_voltage_raw)  # Apply timing alignment
        current_voltage = interpolate_to_legacy_time(current_histories.histories['Vesicle_voltage'])
        
        axes[2, 0].plot(aligned_legacy_time, legacy_voltage * 1000, 'b-', label='Legacy', linewidth=2)
        axes[2, 0].plot(aligned_legacy_time, current_voltage * 1000, 'r--', label='Current', linewidth=2)
        axes[2, 0].set_title('Voltage')
        axes[2, 0].set_xlabel('Time (s)')
        axes[2, 0].set_ylabel('Voltage (mV)')
        axes[2, 0].legend()
        axes[2, 0].grid(True, alpha=0.3)
        
        # Hide unused subplots
        for i in [1, 2]:
            axes[2, i].set_visible(False)
        
        plt.tight_layout()
        plt.savefig('legacy_vs_current_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("Comparison plot saved as 'legacy_vs_current_comparison.png'")
    
    def run_full_comparison(self):
        """Run the complete comparison between legacy and current systems."""
        print("=" * 60)
        print("LEGACY vs CURRENT SIMULATION COMPARISON")
        print("=" * 60)
        
        try:
            # Run legacy simulation
            legacy_results, legacy_params = self.run_legacy_simulation()
            
            # Run current simulation
            current_simulation, current_histories = self.run_current_simulation()
            
            # First, compare all parameters to identify differences
            self.compare_parameters(current_simulation)
            
            # Then compare results
            comparison_stats = self.compare_results(legacy_results, current_simulation, current_histories)
            
            # Create plots
            self.plot_comparison(legacy_results, current_simulation, current_histories)
            
            # Add detailed voltage debugging for first few steps
            print("\n" + "="*80)
            print("DETAILED VOLTAGE DEBUGGING - FIRST 5 STEPS")
            print("="*80)
            
            # Get voltage histories
            legacy_voltages = legacy_results['other_variables']['vesicle_parameters']['U']
            
            # Debug: Print available keys in current histories
            print("DEBUG: Available keys in current_histories:")
            for key in sorted(current_histories.histories.keys()):
                print(f"  {key}")
            
            # Find the voltage key (it's probably 'Vesicle_voltage' with capital V)
            voltage_keys = [k for k in current_histories.histories.keys() if 'voltage' in k.lower()]
            if voltage_keys:
                voltage_key = voltage_keys[0]
                print(f"DEBUG: Using voltage key: {voltage_key}")
                current_voltages = current_histories.histories[voltage_key]
            else:
                print("ERROR: No voltage key found in histories!")
                return comparison_stats
            
            print(f"{'Step':<6} {'Legacy V':<12} {'Current V':<12} {'Diff (mV)':<12} {'Rel Diff %':<12}")
            print("-" * 70)
            
            for i in range(min(5, len(legacy_voltages), len(current_voltages))):
                legacy_v = legacy_voltages[i]
                current_v = current_voltages[i]
                diff_mv = (current_v - legacy_v) * 1000  # Convert to mV
                rel_diff = abs(diff_mv / (legacy_v * 1000)) * 100 if legacy_v != 0 else 0
                
                print(f"{i:<6} {legacy_v:<12.6f} {current_v:<12.6f} {diff_mv:<12.3f} {rel_diff:<12.3f}")
                
            print(f"\nFirst voltage difference appears at step 0: {(current_voltages[0] - legacy_voltages[0])*1000:.3f} mV")
            
            # Check if the difference is already present at initialization
            if abs(current_voltages[0] - legacy_voltages[0]) > 1e-10:
                print("⚠️  WARNING: Voltage difference exists at initialization!")
                print(f"   Legacy initial voltage: {legacy_voltages[0]:.10f} V")
                print(f"   Current initial voltage: {current_voltages[0]:.10f} V")
                print(f"   This suggests a difference in initial conditions or voltage calculation.")
            
            # Add detailed charge calculation debugging
            print("\n" + "="*80)
            print("DETAILED CHARGE CALCULATION DEBUGGING")
            print("="*80)
            
            # Get first iteration data for detailed analysis
            print("\n🔍 INITIAL CHARGE CALCULATION COMPARISON:")
            print("-" * 60)
            
            # Legacy charge calculation (step 1)
            legacy_results_step1 = legacy_results['other_variables']['vesicle_parameters']
            legacy_voltage_step1 = legacy_results_step1['U'][1] if len(legacy_results_step1['U']) > 1 else legacy_results_step1['U'][0]
            legacy_capacitance_step1 = legacy_results_step1['C'][1] if len(legacy_results_step1['C']) > 1 else legacy_results_step1['C'][0]
            legacy_charge_step1 = legacy_voltage_step1 * legacy_capacitance_step1
            
            # Current charge calculation (step 1)
            current_voltage_step1 = current_voltages[1] if len(current_voltages) > 1 else current_voltages[0]
            current_capacitance_step1 = current_histories.histories['Vesicle_capacitance'][1] if len(current_histories.histories['Vesicle_capacitance']) > 1 else current_histories.histories['Vesicle_capacitance'][0]
            current_charge_step1 = current_histories.histories['Vesicle_charge'][1] if len(current_histories.histories['Vesicle_charge']) > 1 else current_histories.histories['Vesicle_charge'][0]
            
            print(f"📊 Step 1 Calculations:")
            print(f"  Legacy:")
            print(f"    Voltage: {legacy_voltage_step1:.10f} V")
            print(f"    Capacitance: {legacy_capacitance_step1:.10e} F")
            print(f"    Charge (V×C): {legacy_charge_step1:.10e} C")
            print(f"  Current:")
            print(f"    Voltage: {current_voltage_step1:.10f} V")
            print(f"    Capacitance: {current_capacitance_step1:.10e} F")
            print(f"    Charge (stored): {current_charge_step1:.10e} C")
            
            print(f"\n📊 Differences:")
            voltage_diff_step1 = current_voltage_step1 - legacy_voltage_step1
            capacitance_diff_step1 = current_capacitance_step1 - legacy_capacitance_step1
            charge_diff_step1 = current_charge_step1 - legacy_charge_step1
            
            print(f"  Voltage diff: {voltage_diff_step1:.10f} V ({voltage_diff_step1*1000:.3f} mV)")
            print(f"  Capacitance diff: {capacitance_diff_step1:.2e} F")
            print(f"  Charge diff: {charge_diff_step1:.2e} C")
            
            # Check if charge difference explains voltage difference
            if abs(capacitance_diff_step1) < 1e-15:  # Capacitance essentially same
                expected_voltage_from_charge = current_charge_step1 / current_capacitance_step1
                print(f"\n🔍 Voltage from charge calculation check:")
                print(f"  Expected voltage (Q/C): {expected_voltage_from_charge:.10f} V")
                print(f"  Stored voltage: {current_voltage_step1:.10f} V")
                print(f"  Match: {abs(expected_voltage_from_charge - current_voltage_step1) < 1e-12}")
            
            # Try to identify if it's a charge calculation or capacitance issue
            if abs(charge_diff_step1) > 1e-15:
                print(f"\n⚠️  CHARGE CALCULATION DIFFERENCE DETECTED!")
                print(f"   This suggests the issue is in how charges are calculated from ion amounts.")
            elif abs(capacitance_diff_step1) > 1e-15:
                print(f"\n⚠️  CAPACITANCE CALCULATION DIFFERENCE DETECTED!")
                print(f"   This suggests the issue is in area or capacitance calculation.")
            else:
                print(f"\n🤔 MYSTERIOUS: Charge and capacitance match but voltage differs!")
                print(f"   This suggests a numerical precision or order-of-operations issue.")
            
            # Add detailed flux comparison after the charge calculation section

            print("\n" + "="*80)
            print("DETAILED FLUX COMPARISON - FIRST 3 STEPS")
            print("="*80)

            # Extract flux data for comparison
            legacy_cl_asor = legacy_results['fluxes']['Cl']['ASOR'][:3]
            legacy_cl_clc = legacy_results['fluxes']['Cl']['CLC'][:3]
            legacy_na_tpc = legacy_results['fluxes']['Na']['TPC'][:3]
            legacy_h_vatp = legacy_results['fluxes']['H']['vATPase'][:3]

            # Current system fluxes
            current_asor_flux = current_histories.histories['ASOR_flux'][:3]
            current_clc_flux = current_histories.histories['CLC_flux'][:3] 
            current_tpc_flux = current_histories.histories['TPC_flux'][:3]
            current_vatp_flux = current_histories.histories['VATPase_flux'][:3]

            print(f"\n🔍 ASOR Cl⁻ FLUX COMPARISON:")
            print(f"{'Step':<4} {'Legacy':<15} {'Current':<15} {'Diff':<15} {'Rel Diff %':<10}")
            print("-" * 70)
            for i in range(3):
                diff = current_asor_flux[i] - legacy_cl_asor[i]
                rel_diff = (diff / legacy_cl_asor[i] * 100) if legacy_cl_asor[i] != 0 else 0
                print(f"{i:<4} {legacy_cl_asor[i]:<15.6e} {current_asor_flux[i]:<15.6e} {diff:<15.6e} {rel_diff:<10.3f}")

            print(f"\n🔍 CLC Cl⁻ FLUX COMPARISON:")
            print(f"{'Step':<4} {'Legacy':<15} {'Current':<15} {'Diff':<15} {'Rel Diff %':<10}")
            print("-" * 70)
            for i in range(3):
                diff = current_clc_flux[i] - legacy_cl_clc[i]
                rel_diff = (diff / legacy_cl_clc[i] * 100) if legacy_cl_clc[i] != 0 else 0
                print(f"{i:<4} {legacy_cl_clc[i]:<15.6e} {current_clc_flux[i]:<15.6e} {diff:<15.6e} {rel_diff:<10.3f}")

            print(f"\n🔍 TPC Na⁺ FLUX COMPARISON:")
            print(f"{'Step':<4} {'Legacy':<15} {'Current':<15} {'Diff':<15} {'Rel Diff %':<10}")
            print("-" * 70)
            for i in range(3):
                diff = current_tpc_flux[i] - legacy_na_tpc[i]
                rel_diff = (diff / legacy_na_tpc[i] * 100) if legacy_na_tpc[i] != 0 else 0
                print(f"{i:<4} {legacy_na_tpc[i]:<15.6e} {current_tpc_flux[i]:<15.6e} {diff:<15.6e} {rel_diff:<10.3f}")

            print(f"\n🔍 VATPase H⁺ FLUX COMPARISON:")
            print(f"{'Step':<4} {'Legacy':<15} {'Current':<15} {'Diff':<15} {'Rel Diff %':<10}")
            print("-" * 70)
            for i in range(3):
                diff = current_vatp_flux[i] - legacy_h_vatp[i]
                rel_diff = (diff / legacy_h_vatp[i] * 100) if legacy_h_vatp[i] != 0 else 0
                print(f"{i:<4} {legacy_h_vatp[i]:<15.6e} {current_vatp_flux[i]:<15.6e} {diff:<15.6e} {rel_diff:<10.3f}")

            # Add Nernst potential comparison 
            print(f"\n🔍 NERNST POTENTIAL COMPARISON:")
            print(f"{'Channel':<10} {'Step':<4} {'Legacy':<15} {'Current':<15} {'Diff':<15}")
            print("-" * 70)

            # We need to calculate legacy Nernst potentials - let's add this
            # For now, let's compare available current system Nernst potentials
            current_asor_nernst = current_histories.histories['ASOR_nernst_potential'][:3]
            current_clc_nernst = current_histories.histories['CLC_nernst_potential'][:3]
            current_tpc_nernst = current_histories.histories['TPC_nernst_potential'][:3]

            print("Note: Legacy Nernst potentials need to be extracted from legacy system")
            print(f"Current ASOR: {current_asor_nernst}")
            print(f"Current CLC:  {current_clc_nernst}") 
            print(f"Current TPC:  {current_tpc_nernst}")
            
            return comparison_stats
            
        except Exception as e:
            print(f"Error during comparison: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def compare_parameters(self, current_simulation):
        """
        Compare all parameters between legacy and current systems to identify differences.
        """
        print("\n" + "=" * 60)
        print("COMPREHENSIVE PARAMETER COMPARISON")
        print("=" * 60)
        
        # Legacy parameters (from config.py)
        print("\n🔍 INITIAL CONCENTRATIONS COMPARISON:")
        print("-" * 40)
        print(f"{'Parameter':<25} {'Legacy':<15} {'Current':<15} {'Match':<8}")
        print("-" * 40)
        
        # Ion concentrations
        concentrations = [
            ('Cl⁻ (internal)', self.internal_concentrations['cl'], current_simulation.species['cl'].init_vesicle_conc),
            ('Cl⁻ (external)', self.external_concentrations['cl'], current_simulation.species['cl'].exterior_conc),
            ('Na⁺ (internal)', self.internal_concentrations['na'], current_simulation.species['na'].init_vesicle_conc),
            ('Na⁺ (external)', self.external_concentrations['na'], current_simulation.species['na'].exterior_conc),
            ('H⁺ (internal)', self.htotal_i, current_simulation.species['h'].init_vesicle_conc),
            ('H⁺ (external)', self.htotal_o, current_simulation.species['h'].exterior_conc),
            ('K⁺ (internal)', self.internal_concentrations['k'], current_simulation.species['k'].init_vesicle_conc),
            ('K⁺ (external)', self.external_concentrations['k'], current_simulation.species['k'].exterior_conc),
        ]
        
        for name, legacy_val, current_val in concentrations:
            match = "✓" if abs(legacy_val - current_val) < 1e-9 else "❌"
            print(f"{name:<25} {legacy_val:<15.6e} {current_val:<15.6e} {match:<8}")
        
        # pH and buffer parameters
        print(f"\n🔍 pH AND BUFFER PARAMETERS:")
        print("-" * 40)
        print(f"{'Parameter':<25} {'Legacy':<15} {'Current':<15} {'Match':<8}")
        print("-" * 40)
        
        ph_buffer_params = [
            ('pH internal', self.internal_concentrations['pH_i'], current_simulation.vesicle_params['init_pH']),
            ('pH external', self.external_concentrations['pH_o'], current_simulation.exterior_params['pH']),
            ('Buffer capacity', self.buffer_capacity_t0, current_simulation.init_buffer_capacity),  
        ]
        
        for name, legacy_val, current_val in ph_buffer_params:
            if isinstance(legacy_val, (int, float)) and isinstance(current_val, (int, float)):
                match = "✓" if abs(legacy_val - current_val) < 1e-9 else "❌"
                print(f"{name:<25} {legacy_val:<15.6f} {current_val:<15.6f} {match:<8}")
            else:
                match = "✓" if legacy_val == current_val else "❌"
                print(f"{name:<25} {str(legacy_val):<15} {str(current_val):<15} {match:<8}")
        
        # Vesicle parameters
        print(f"\n🔍 VESICLE PARAMETERS:")
        print("-" * 40)
        print(f"{'Parameter':<25} {'Legacy':<15} {'Current':<15} {'Match':<8}")
        print("-" * 40)
        
        vesicle_params = [
            ('Initial radius (m)', self.r, current_simulation.vesicle_params['init_radius']),
            ('Initial voltage (V)', self.U0, current_simulation.vesicle_params['init_voltage']),
        ]
        
        for name, legacy_val, current_val in vesicle_params:
            match = "✓" if abs(legacy_val - current_val) < 1e-9 else "❌"
            print(f"{name:<25} {legacy_val:<15.6e} {current_val:<15.6e} {match:<8}")
        
        # Simulation parameters
        print(f"\n🔍 SIMULATION PARAMETERS:")
        print("-" * 40)
        print(f"{'Parameter':<25} {'Legacy':<15} {'Current':<15} {'Match':<8}")
        print("-" * 40)
        
        sim_params = [
            ('Time step (s)', self.dt, current_simulation.time_step),
            ('Total time (s)', self.T, current_simulation.total_time),
            ('Temperature (K)', self.RT / 8.31446261815324, current_simulation.temperature), # Convert RT to temperature using precise gas constant
        ]
        
        # Debug temperature values
        print(f"DEBUG: Legacy RT = {self.RT}")
        print(f"DEBUG: Legacy temperature = {self.RT / 8.31446261815324}")
        print(f"DEBUG: Current temperature = {current_simulation.temperature}")
        print(f"DEBUG: Current nernst_constant = {current_simulation.nernst_constant}")
        
        for name, legacy_val, current_val in sim_params:
            match = "✓" if abs(legacy_val - current_val) < 1e-9 else "❌"
            print(f"{name:<25} {legacy_val:<15.6f} {current_val:<15.6f} {match:<8}")
        
        # Channel parameters comparison
        print(f"\n🔍 CHANNEL PARAMETERS COMPARISON:")
        print("-" * 80)
        
        # Define legacy channel parameters (extracted from legacy equations)
        legacy_channels = {
            'ASOR': {
                'type': 'voltage_and_pH',
                'conductance': 8e-5,  # This needs to be extracted from legacy
                'pH_dependence': 2.5,
                'voltage_dependence': 25,
                'substrate_km': 30,
                'flux_direction': 1,  # positive
            },
            'CLC': {
                'type': 'voltage_and_pH', 
                'conductance': 1e-7,  # This needs to be extracted from legacy
                'voltage_dependence': 25,
                'substrate_km': 30,
                'flux_direction': 2,  # 2.0 multiplier in legacy J_Cl_CLC function  
                'coupling_ratio': 2,  # 2 Cl- : 1 H+
            },
            'TPC': {
                'type': 'simple',
                'conductance': 2e-6,  # This needs to be extracted from legacy
                'flux_direction': 1,  # positive
            },
            'NHE': {
                'type': 'antiporter',
                'conductance': 0.0,  # Electroneutral in legacy
                'flux_direction': 1,  # positive
                'coupling_ratio': 1,  # 1 Na+ : 1 H+
            },
            'VATPase': {
                'type': 'time_dependent',
                'conductance': 8e-9,  # This needs to be extracted from legacy
                'time_dependence': 't_dep_func',
                'flux_direction': -1,  # negative (pumps H+ in)
            },
            'H_leak': {
                'type': 'simple',
                'conductance': 1.6e-8,  # This needs to be extracted from legacy
                'flux_direction': 1,  # positive
            }
        }
        
        current_channels = {
            'ASOR': current_simulation.channels['asor'],
            'CLC': current_simulation.channels['clc'],
            'TPC': current_simulation.channels['tpc'],
            'NHE': current_simulation.channels['nhe'],
            'VATPase': current_simulation.channels['vatpase'],
            'H_leak': current_simulation.channels['hleak'],
        }
        
        for channel_name in legacy_channels:
            print(f"\n--- {channel_name} Channel ---")
            legacy_ch = legacy_channels[channel_name]
            current_ch = current_channels[channel_name]
            
            print(f"{'Parameter':<25} {'Legacy':<15} {'Current':<15} {'Match':<8}")
            print("-" * 65)
            
            # Compare conductance
            if 'conductance' in legacy_ch:
                legacy_cond = legacy_ch['conductance']
                current_cond = current_ch.conductance if current_ch.conductance is not None else 0.0
                match = "✓" if abs(legacy_cond - current_cond) < 1e-12 else "❌"
                print(f"{'Conductance':<25} {legacy_cond:<15.2e} {current_cond:<15.2e} {match:<8}")
            
            # Compare voltage multiplier
            current_vmult = current_ch.voltage_multiplier if current_ch.voltage_multiplier is not None else 0.0
            print(f"{'Voltage multiplier':<25} {'N/A':<15} {current_vmult:<15.1f} {'?':<8}")
            
            # Compare nernst multiplier
            current_nmult = current_ch.nernst_multiplier if current_ch.nernst_multiplier is not None else 1.0
            print(f"{'Nernst multiplier':<25} {'N/A':<15} {current_nmult:<15.3f} {'?':<8}")
            
            # Compare flux multiplier
            legacy_flux_dir = legacy_ch.get('flux_direction', 1)
            current_flux_mult = current_ch.flux_multiplier if current_ch.flux_multiplier is not None else 1.0
            flux_match = "✓" if legacy_flux_dir == current_flux_mult else "❌"
            print(f"{'Flux direction/mult':<25} {legacy_flux_dir:<15.1f} {current_flux_mult:<15.1f} {flux_match:<8}")
            
            # Compare primary and secondary exponents
            current_prim_exp = current_ch.primary_exponent
            current_sec_exp = current_ch.secondary_exponent
            print(f"{'Primary exponent':<25} {'N/A':<15} {current_prim_exp:<15} {'?':<8}")
            print(f"{'Secondary exponent':<25} {'N/A':<15} {current_sec_exp:<15} {'?':<8}")
            
            # Compare dependence type
            legacy_type = legacy_ch['type']
            current_type = current_ch.dependence_type if current_ch.dependence_type else 'None'
            dep_match = "?" # We'll need to check this manually
            print(f"{'Dependence type':<25} {legacy_type:<15} {current_type:<15} {dep_match:<8}")
        
        print(f"\n🔍 SUMMARY:")
        print("-" * 40)
        print("✓ = Match    ❌ = Mismatch    ? = Needs manual verification")
        print("Legend: Legacy values are from the original equations")
        print("        Current values are from the new system configuration")

def main():
    """Main function to run the comparison."""
    comparator = SimulationComparator()
    stats = comparator.run_full_comparison()
    
    if stats and stats['all_match']:
        print("\n🎉 Congratulations! Your legacy and current systems are mathematically equivalent!")
    else:
        print("\n🔍 There are differences between the systems that need investigation.")
        print("Check the detailed output above and the comparison plots.")

if __name__ == "__main__":
    main() 