#!/usr/bin/env python3
"""
Run legacy vs current simulations for two scenarios (default and 0.5× internal Cl)
and plot voltage, volume, pH, concentrations, and key fluxes over 1000 s.

Usage (from repo root):
  python compare_legacy_current_scenarios.py

Outputs:
  - comparison_default.png
  - comparison_low_cl.png
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# Make legacy and current code importable
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "legacy"))
sys.path.insert(0, str(ROOT / "src"))

from legacy.utilities import simulation_tools as legacy_sim
import legacy.config as legacy_cfg

from src.backend.simulation import Simulation
from src.backend.default_channels import default_channels
from src.backend.default_ion_species import default_ion_species
from src.backend.ion_and_channels_link import IonChannelsLink


def run_legacy(cl_internal_mM: float):
    """Run legacy simulation with specified internal Cl concentration (mM)."""
    # Recompute initial state using legacy helper
    X_amount, ext_conc, internal_amounts, internal_conc, sum_initial = \
        legacy_cfg.initialize_internal_concentrations(Cl_i_concentration=cl_internal_mM * 1e-3)

    params = {
        "dt": legacy_cfg.dt,
        "T": legacy_cfg.T,
        "G": {
            "ASOR": 8e-5,
            "TPC": 2e-6,
            "K": 0.0,
            "CLC": 1e-7,
            "NHE": 0.0,
            "vATPase": 8e-9,
            "H_leak": 1.6e-8,
        },
        "external_ions_concentrations": ext_conc,
        "A_from_V_const": legacy_cfg.A_from_V_const,
        "X_amount": X_amount,
        "buffer_capacity_t0": legacy_cfg.buffer_capacity_t0,
        "V_t0": legacy_cfg.V0,
        "c_spec": legacy_cfg.c_spec,
        "RT": legacy_cfg.RT,
        "F": legacy_cfg.F,
        "pH_i": legacy_cfg.pH_i,
        "U0": legacy_cfg.U0,
        "A0": legacy_cfg.A0,
        "C0": legacy_cfg.C0,
        "Sum_initial_amounts": sum_initial,
        "ASOR_pH_k2": 3.0,
        "ASOR_pH_half": 5.4,
        "ASOR_U_k2": 80.0,
        "ASOR_U_half": -40e-3,
        "CLC_pH_k2": 1.5,
        "CLC_pH_half": 5.5,
        "CLC_U_k2": 80.0,
        "CLC_U_half": -40e-3,
    }

    results = legacy_sim.run_simulation(np.array(internal_amounts), params)
    return results, params


def clone_species_with_cl(cl_internal_mM: float):
    """Clone default species but override internal Cl concentration."""
    import copy
    species = copy.deepcopy(default_ion_species)
    species["cl"].init_vesicle_conc = cl_internal_mM * 1e-3
    return species


def run_current(cl_internal_mM: float):
    """Run current simulation with specified internal Cl concentration (mM)."""
    # Reuse legacy initialization to get consistent totals and X_amount
    X_amount, ext_conc, internal_amounts, internal_conc, sum_initial = \
        legacy_cfg.initialize_internal_concentrations(Cl_i_concentration=cl_internal_mM * 1e-3)

    # Clone species and set hydrogen totals and external Cl to match legacy state
    species = clone_species_with_cl(cl_internal_mM)
    # CRITICAL: Must update BOTH init_vesicle_conc AND vesicle_conc!
    # vesicle_conc is what gets used in set_ion_amounts() during run()
    species["cl"].init_vesicle_conc = internal_conc[legacy_cfg.Cl_idx]
    species["cl"].vesicle_conc = internal_conc[legacy_cfg.Cl_idx]
    species["h"].init_vesicle_conc = internal_conc[legacy_cfg.H_idx]  # total H internal
    species["h"].vesicle_conc = internal_conc[legacy_cfg.H_idx]       # Set current conc too
    species["h"].exterior_conc = ext_conc[legacy_cfg.H_idx]           # total H external
    species["cl"].exterior_conc = ext_conc[legacy_cfg.Cl_idx]
    species["na"].init_vesicle_conc = internal_conc[legacy_cfg.Na_idx]
    species["na"].vesicle_conc = internal_conc[legacy_cfg.Na_idx]
    species["na"].exterior_conc = ext_conc[legacy_cfg.Na_idx]
    species["k"].init_vesicle_conc = internal_conc[legacy_cfg.K_idx]
    species["k"].vesicle_conc = internal_conc[legacy_cfg.K_idx]
    species["k"].exterior_conc = ext_conc[legacy_cfg.K_idx]

    # Compute temperature from legacy RT to match legacy Nernst constant
    legacy_temperature = legacy_cfg.RT / 8.31446261815324

    sim = Simulation(
        channels=default_channels,
        species=species,
        ion_channel_links=IonChannelsLink(use_defaults=True),
        vesicle_params={
            "init_radius": legacy_cfg.r,
            "init_voltage": legacy_cfg.U0,
            "init_pH": legacy_cfg.pH_i,
        },
        exterior_params={"pH": legacy_cfg.pH_o},
        time_step=legacy_cfg.dt,
        total_time=legacy_cfg.T,
        temperature=legacy_temperature,
        init_buffer_capacity=legacy_cfg.buffer_capacity_t0,
        buffer_capacity_beta_mM_per_pH=None,  # use inverse directly for parity
    )
    # Inject legacy-unaccounted charge to match initial voltage
    # This ensures charge balance is consistent with legacy's calculation
    sim.unaccounted_ion_amounts = X_amount
    
    # Recompute initial charge/voltage using legacy amounts before run
    from src.backend.constants import FARADAY_CONSTANT
    total_charge = (
        sum(ion.elementary_charge * ion.init_vesicle_conc for ion in sim.all_species)
        * sim.vesicle.init_volume * 1000
        + sim.unaccounted_ion_amounts
    ) * FARADAY_CONSTANT
    
    sim.vesicle.init_charge = total_charge  # Update init_charge
    sim.vesicle.charge = total_charge       # Update current charge
    sim.vesicle.voltage = sim.vesicle.charge / sim.vesicle.capacitance  # Recalculate voltage
    histories = sim.run()
    return sim, histories


def align_time_legacy(results, dt):
    """Legacy uses arrays length T/dt; current uses stored time array."""
    time = np.arange(0, len(results["other_variables"]["vesicle_parameters"]["V"]) * dt, dt)
    # shift by one step to align physical state (legacy uses previous step for voltage)
    if len(time) > 1:
        time = time[1:]
    return time


def align_series_legacy(arr):
    return arr[1:] if len(arr) > 1 else arr


def downsample(x, y, step=100):
    return x[::step], y[::step]


def plot_case(label, legacy_results, current_histories, dt):
    legacy_time = align_time_legacy(legacy_results, dt)
    current_time = np.array(current_histories.histories["simulation_time"])

    def interp_current(series):
        s = current_histories.histories[series]
        return np.interp(legacy_time, current_time, s)

    fig, axes = plt.subplots(3, 3, figsize=(18, 12))
    fig.suptitle(f"{label} – Legacy vs Current (aligned)", fontsize=16)

    # Concentrations (mM)
    ions = [("Cl", "cl"), ("Na", "na"), ("H", "h"), ("K", "k")]
    for idx, (lname, ckey) in enumerate(ions):
        ax = axes[idx // 3, idx % 3]
        legacy = align_series_legacy(legacy_results["internal_ions"][lname]["concentrations"]) * 1000
        current = interp_current(f"{ckey}_vesicle_conc") * 1000
        t_ds, legacy_ds = downsample(legacy_time, legacy)
        _, current_ds = downsample(legacy_time, current)
        ax.plot(t_ds, legacy_ds, "b-", label="Legacy")
        ax.plot(t_ds, current_ds, "r--", label="Current")
        ax.set_title(f"{lname} concentration (mM)")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("mM")
        ax.grid(True, alpha=0.3)
        ax.legend()

    # Volume (µm³)
    ax = axes[1, 1]
    legacy_vol = align_series_legacy(legacy_results["other_variables"]["vesicle_parameters"]["V"]) * 1e18
    current_vol = interp_current("Vesicle_volume") * 1e18
    t_ds, lv_ds = downsample(legacy_time, legacy_vol)
    _, cv_ds = downsample(legacy_time, current_vol)
    ax.plot(t_ds, lv_ds, "b-", label="Legacy")
    ax.plot(t_ds, cv_ds, "r--", label="Current")
    ax.set_title("Volume (µm³)")
    ax.set_xlabel("Time (s)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # pH
    ax = axes[1, 2]
    legacy_pH = align_series_legacy(legacy_results["other_variables"]["vesicle_parameters"]["pH"])
    current_pH = interp_current("Vesicle_pH")
    t_ds, lp_ds = downsample(legacy_time, legacy_pH)
    _, cp_ds = downsample(legacy_time, current_pH)
    ax.plot(t_ds, lp_ds, "b-", label="Legacy")
    ax.plot(t_ds, cp_ds, "r--", label="Current")
    ax.set_title("Vesicle pH")
    ax.set_xlabel("Time (s)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Voltage (mV)
    ax = axes[2, 0]
    legacy_v = align_series_legacy(legacy_results["other_variables"]["vesicle_parameters"]["U"]) * 1000
    current_v = interp_current("Vesicle_voltage") * 1000
    t_ds, lv_ds = downsample(legacy_time, legacy_v)
    _, cv_ds = downsample(legacy_time, current_v)
    ax.plot(t_ds, lv_ds, "b-", label="Legacy")
    ax.plot(t_ds, cv_ds, "r--", label="Current")
    ax.set_title("Voltage (mV)")
    ax.set_xlabel("Time (s)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Fluxes (first few main channels), mol/s
    ax = axes[2, 1]
    legacy_cl_asor = align_series_legacy(legacy_results["fluxes"]["Cl"]["ASOR"])
    legacy_cl_clc = align_series_legacy(legacy_results["fluxes"]["Cl"]["CLC"])
    current_asor = interp_current("ASOR_flux")
    current_clc = interp_current("CLC_flux")
    t_ds, l_asor_ds = downsample(legacy_time, legacy_cl_asor)
    _, c_asor_ds = downsample(legacy_time, current_asor)
    ax.plot(t_ds, l_asor_ds, "b-", label="ASOR (legacy)")
    ax.plot(t_ds, c_asor_ds, "b--", label="ASOR (current)")
    t_ds, l_clc_ds = downsample(legacy_time, legacy_cl_clc)
    _, c_clc_ds = downsample(legacy_time, current_clc)
    ax.plot(t_ds, l_clc_ds, "r-", label="CLC (legacy)")
    ax.plot(t_ds, c_clc_ds, "r--", label="CLC (current)")
    ax.set_title("Cl fluxes (mol/s)")
    ax.set_xlabel("Time (s)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)

    # Hide unused subplot
    axes[2, 2].set_visible(False)

    plt.tight_layout()
    outfile = f"comparison_{label.replace(' ', '_').lower()}.png"
    plt.savefig(outfile, dpi=200)
    print(f"Saved {outfile}")


def main():
    scenarios = [
        ("default", 159.0),
        ("low_cl", 159.0 / 2.0),
    ]
    for label, cl_mM in scenarios:
        print(f"\n=== Running scenario: {label} (Cl internal = {cl_mM} mM) ===")
        legacy_results, _ = run_legacy(cl_mM)
        current_sim, current_hist = run_current(cl_mM)
        plot_case(label, legacy_results, current_hist, legacy_cfg.dt)
        # Diagnostics for first 5 steps on low_cl
        if label == "low_cl":
            legacy_time = align_time_legacy(legacy_results, legacy_cfg.dt)
            current_time = np.array(current_hist.histories["simulation_time"])
            # helper
            def interp_current(series):
                s = current_hist.histories[series]
                return np.interp(legacy_time, current_time, s)
            def legacy_series(path):
                return align_series_legacy(path)
            print("\n--- DIAGNOSTICS: first 5 steps (aligned for legacy history duplication) ---")
            # Legacy duplicates the initial state at indices 0 and 1, so we skip index 0
            fields = [
                ("Voltage (mV)", legacy_series(legacy_results["other_variables"]["vesicle_parameters"]["U"]) * 1000,
                 interp_current("Vesicle_voltage") * 1000),
                ("pH", legacy_series(legacy_results["other_variables"]["vesicle_parameters"]["pH"]),
                 interp_current("Vesicle_pH")),
                ("Cl conc (mM)", legacy_series(legacy_results["internal_ions"]["Cl"]["concentrations"]) * 1000,
                 interp_current("cl_vesicle_conc") * 1000),
                ("H conc (mM)", legacy_series(legacy_results["internal_ions"]["H"]["concentrations"]) * 1000,
                 interp_current("h_vesicle_conc") * 1000),
                ("ASOR flux", legacy_series(legacy_results["fluxes"]["Cl"]["ASOR"]),
                 interp_current("ASOR_flux")),
                ("CLC flux", legacy_series(legacy_results["fluxes"]["Cl"]["CLC"]),
                 interp_current("CLC_flux")),
            ]
            for name, leg, cur in fields:
                print(f"\n{name}:")
                for i in range(min(5, len(leg), len(cur))):
                    print(f"  step {i}: legacy={leg[i]:.6e}, current={cur[i]:.6e}, diff={cur[i]-leg[i]:.6e}")


if __name__ == "__main__":
    main()

