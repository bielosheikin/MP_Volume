from config import dt, T, A_from_V_const, buffer_capacity_t0, V0, c_spec, pH_i, U0, A0, C0, initialize_internal_concentrations
import matplotlib.pyplot as plt
import numpy as np
from plotting import display_simulation_results as plot
from plotting import plot_functional_dependences as plot_dep

from utilities import simulation_tools as simtools

# G = {}
# G['ASOR'] = float(input('G_ASOR'))
# G['TPC'] = float(input('G_TPC'))
# G['K'] = float(input('G_K'))
# G['CLC'] = float(input('G_CLC'))
# G['NHE'] = float(input('G_NHE'))
# G['vATPase'] = float(input('G_vATPase'))
# G['H_leak'] = float(input('G_H_leak'))

G = {}
G['ASOR'] = float(input('G_ASOR 10**(-5)'))*1e-5
G['TPC'] = float(input('G_TPC 10**(-6)'))*1e-6
G['K'] = float(input('G_K'))
G['CLC'] = float(input('G_CLC 10**(-8)'))*1e-8
G['NHE'] = float(input('G_NHE'))
G['vATPase'] = float(input('G_vATPase 10**(-9)'))*1e-9
G['H_leak'] = float(input('G_H_leak 10**(-9)'))*1e-9


ASOR_pH_args = {}
choice_dep_fuct = input ('ASOR pH-dependency: WT (wt), pH-shifted mutant (mt) or none')
if choice_dep_fuct == 'wt':
    ASOR_pH_args['pH_k2'] = 3.0
    ASOR_pH_args['pH_half'] = 5.4
elif choice_dep_fuct == 'mt':
    ASOR_pH_args['pH_k2'] = 1.0
    ASOR_pH_args['pH_half'] = 7.4
elif choice_dep_fuct == 'none':
    ASOR_pH_args['pH_k2'] = 0.0
    ASOR_pH_args['pH_half'] = 0.0

ASOR_U_args = {}
choice_dep_fuct = input ('ASOR V-dependency: yes or no')
if choice_dep_fuct == 'yes':
    ASOR_U_args['U_k2'] = 80 
    ASOR_U_args['U_half'] = -40*1e-3
elif choice_dep_fuct == 'no':
    ASOR_U_args['U_k2'] = 0 
    ASOR_U_args['U_half'] = 0

CLC_args = {}
choice_dep_fuct = input ('CLC pH- and V-dependency: yes or no')
if choice_dep_fuct == 'yes':
    CLC_args['U_k2'] = 80 
    CLC_args['U_half'] = -40*1e-3
    CLC_args['pH_k2'] = 1.5 
    CLC_args['pH_half'] = 5.5
elif choice_dep_fuct == 'no':
    CLC_args['U_k2'] = 0 
    CLC_args['U_half'] = 0
    CLC_args['pH_k2'] = 0 
    CLC_args['pH_half'] = 0

choice_Cl_conc = input ('Initial internal Cl concentration: high, low or zero')
if choice_Cl_conc == 'high':
    Cl_i_concentration = 159*1e-3
elif choice_Cl_conc == 'low':
    Cl_i_concentration = 9*1e-3
elif choice_Cl_conc == 'zero':
    Cl_i_concentration = 1*1e-3


X_amount, external_ions_concentrations, internal_ions_amounts, internal_ions_concentrations, Sum_initial_amounts = initialize_internal_concentrations(Cl_i_concentration)

parameters = {
    'dt': dt,
    'T': T,
    'G': G,
    'external_ions_concentrations': external_ions_concentrations,
    'A_from_V_const': A_from_V_const,
    'X_amount': X_amount,
    'buffer_capacity_t0': buffer_capacity_t0, 
    'V_t0': V0, 
    'c_spec': c_spec, 
    'RT': 2578.5871, 
    'F': 96485.0,
    'pH_i': pH_i,
    'U0': U0,
    'A0': A0,
    'C0': C0,
    'Sum_initial_amounts': Sum_initial_amounts,
    'ASOR_pH_k2': ASOR_pH_args['pH_k2'],
    'ASOR_pH_half': ASOR_pH_args['pH_half'],
    'ASOR_U_k2': ASOR_U_args['U_k2'],
    'ASOR_U_half': ASOR_U_args['U_half'],
    'CLC_pH_k2': CLC_args['pH_k2'],
    'CLC_pH_half': CLC_args['pH_half'],
    'CLC_U_k2': CLC_args['U_k2'],
    'CLC_U_half': CLC_args['U_half']
   }


results = simtools.run_simulation(internal_ions_amounts, parameters)

figure = plot.figure_plottting(results)
figure_dependency = plot_dep.plot_dependency()
