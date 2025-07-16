import numpy as np
from utilities import nernst_potentials as P
from utilities import ionic_fluxes as i_flux
from utilities import dep_functions as dep_funct
from config import *


def compute_flows(time_step, 
    internal_ions, 
    V,
    G,
    external_ions_concentrations,
    A_from_V_const,
    X_amount,
    buffer_capacity_T0,
    V_t0, 
    c_spec, 
    ASOR_pH_k2, 
    ASOR_pH_half,
    ASOR_U_k2,
    ASOR_U_half,
    CLC_pH_k2,
    CLC_pH_half,
    CLC_U_k2,
    CLC_U_half,
    RT = 2578.5871, 
    F = 96485.0,
): 
    '''
    Arguments
    =============
    `time_step` [float]:
        - which timestep (in seconds)
    `internal_ions` [1D np.ndarray]:
        -vector of internal ion amounts (in moles)
    `external_ions_concentrations` [1D np.ndarray]:
        -vector of external ion concentrations (in moles/l)
    `V_t` [float]:
        - current volume (in m3)
    "G" [dict]:
        - dictionary containing conductances (in UNITS HERE) for the following channel types:
            - ASOR, ClC, TPC, NHE, vATPase, H leak, K channel
    `X_amount` [float]:
        - amount of unaccounted for ions (in moles)
    `A_from_V_const` [float]
        - area calculated from the volume
    `buffer_capacity_T0` [float]:
        - buffer capacity at initial time
    `V_t0` [float]:
        - initial volume (in m3)
    `c_spec` [float]:
        - membrane capacitance (in F/(m**2))
    `RTdivF` [float]:
        - RT / F
    `ASOR_pH_k2` [float]:
        - exponential scaling parameter of the ASOR pH dependence 
    `ASOR_pH_half` [float]:
        - pH1/2 of ASOR activation
    `ASOR_U_k2` [float]:
        - exponential scaling parameter of the ASOR voltage dependence 
    `ASOR_U_half` [float]:
        - U1/2 of ASOR activation
    `CLC_pH_k2` [float]:
        - exponential scaling parameter of the CLC pH dependence 
    `CLC_pH_half` [float]:
        - pH1/2 of CLC activation
    `CLC_U_k2` [float]:
        - exponential scaling parameter of the CLC voltage dependence 
    `CLC_U_half` [float]:
        - U1/2 of CLC activation
    `RT` [float]:
        - Gas constant x Temperature 
    `F` [float]:
        - Faraday's constant

    Returns
    ===========
    `dIons_dt` [1D np.ndarray]:
        - vector of fluxes for Cl, Na, H and K ions
    `fluxes` [dict]:
        - dictionary containing fluxes of each ion through each ion chanel
    `deps` [dict]:
        - dictionary containing pH-, time- and V- dependency functions for ASOR, ClC and vATPase
    `local_vars` [dict]:
        - dictionary containing other macropinosme parameters: pH, membrane area, capacitance  and buffer capacity

    '''

    dIons_dt = np.empty(internal_ions.shape[0])

    Buffer_T=buffer_capacity_T0*(V/V_t0) # Buffer capacity at the current time step
    htotal_i = internal_ions[H_idx]/(V*1000) # Concentration (mol/l) of H (total) in MP from the amount (mol) 

    hfree_o =  external_ions_concentrations[H_idx] * buffer_capacity_T0 # Free external H concentration (mol/l)
    hfree_i = htotal_i * Buffer_T # Free internal H concentration (mol/l)

    A=A_from_V_const*(V**(2/3)) #Membrane area of the macropinosome at the current time step
    C=A*c_spec # Membrane capacitance 
    Q = (internal_ions[Na_idx] + internal_ions[K_idx] + internal_ions[H_idx] -  internal_ions[Cl_idx] + X_amount) * F # Total charge
    U = Q / C # Membrane potential
    
    cl_i = internal_ions[Cl_idx]/(V*1000) # Internal Cl concentration in mol/l
    na_i = internal_ions[Na_idx]/(V*1000) # Internal Na concentration in mol/l
    k_i = internal_ions[K_idx]/(V*1000) # Internal K concentration in mol/l

    pH_local=-np.log10(hfree_i) #pH inside of the macropinosome

    RTdivF = RT / F

    # Nernst potentials computed for different channels
    potential_asor = P.nernst_potential_Cl_asor(U, external_ions_concentrations[Cl_idx], cl_i, RTdivF)
    potential_CLC = P.nernst_potential_CLC(U, cl_i, external_ions_concentrations[Cl_idx], hfree_i, hfree_o, RT, F)
    n_potential_Na_TPC = P.nernst_potential_Na_K(U, external_ions_concentrations[Na_idx], na_i, RTdivF)
    potential_nhe = P.potential_NHE(external_ions_concentrations[Na_idx], na_i, hfree_i, hfree_o)
    potential_k= P.nernst_potential_Na_K(U, external_ions_concentrations[K_idx], k_i, RTdivF)
    potential_VATPase= P.nernst_potential_VATPase(U, hfree_o, hfree_i, RTdivF)
    potential_H_leak = P.nernst_potential_H_leak(U, hfree_o, hfree_i, RTdivF)

    # Flow of chloride (d[Cl]/dt)
    Cl_flux_asor = i_flux.J_cl_asor(potential_asor, G['ASOR'], U, pH_local, A, ASOR_pH_k2, ASOR_pH_half, ASOR_U_k2, ASOR_U_half)
    Cl_flux_CLC = i_flux.J_Cl_CLC(potential_CLC, G['CLC'], U, pH_local, A, CLC_pH_k2, CLC_pH_half, CLC_U_k2, CLC_U_half)

    dIons_dt[Cl_idx] = Cl_flux_asor + Cl_flux_CLC

    # Flow of sodium (d[Na]/dt)
    na_flux_tpc = i_flux.J_na_tpc(n_potential_Na_TPC, G['TPC'], A)
    na_flux_nhe = i_flux.J_Na_NHE(potential_nhe, G['NHE'], A)

    dIons_dt[Na_idx] = na_flux_tpc + na_flux_nhe

    # Flow of protons (d[H]/dt)
    H_flux_CLC = i_flux.J_H_CLC(potential_CLC, G['CLC'], U, pH_local, A, CLC_pH_k2, CLC_pH_half, CLC_U_k2, CLC_U_half)
    H_flux_NHE = i_flux.J_H_NHE(potential_nhe,G['NHE'],A)
    H_flux_VATPase = i_flux.J_VATPase(potential_VATPase, G['vATPase'], time_step, A)
    H_flux_leak    = i_flux.J_H_leak(potential_H_leak, G['H_leak'], A)

    dIons_dt[H_idx] = H_flux_CLC + H_flux_NHE + H_flux_VATPase + H_flux_leak

    # calculate flow of K (d[K]/dt)
    K_flux = i_flux.J_k(potential_k, G['K'], A)

    dIons_dt[K_idx] = K_flux
    
    pH_dep_ASOR= dep_funct.pH_dependence_ASOR(pH_local, pH_k2 = ASOR_pH_k2, pH_half = ASOR_pH_half)
    v_dep_ASOR= dep_funct.v_dependence_ASOR(U, U_k2 = ASOR_U_k2, U_half = ASOR_U_half)
    
    pH_dep_ClC = dep_funct.pH_dependence_ClC(pH_local, pH_k2 = CLC_pH_k2, pH_half = CLC_pH_half)
    v_dep_ClC  = dep_funct.v_dependence_ClC(U, U_k2 = CLC_U_k2, U_half = CLC_U_half)

    t_dep_VATPase = dep_funct.g_VATP_dependence(time_step)

    fluxes = {'Cl_asor': Cl_flux_asor,
            'Cl_CLC': Cl_flux_CLC,
            'Na_tpc': na_flux_tpc,
            'Na_nhe': na_flux_nhe,
            'H_CLC': H_flux_CLC,
            'H_NHE': H_flux_NHE,
            'H_VATPase': H_flux_VATPase,
            'H_leak': H_flux_leak,
            'K': K_flux
            }
    
    deps = {'pH_ASOR': pH_dep_ASOR,
            'v_ASOR': v_dep_ASOR,
            'pH_ClC': pH_dep_ClC,
            'v_ClC': v_dep_ClC,
             't_VATPase': t_dep_VATPase
             }
    
    local_vars = {'pH_local': pH_local,
                    'A': A,
                    'C': C,
                    'Buffer_T': Buffer_T,
                    'U': U
                    }

    return dIons_dt, fluxes, deps, local_vars

def update_euler(past_state, int_step, derivative):
    """ Integrate ODE with simple Euler integration """
    return past_state + (int_step * derivative) # Euler integration i.e. x(t) = x(t-1) + (dt * dx(t)/dt)

def run_simulation(initial_state_ions_amounts, parameters):
    """
    Arguments
    ==========
    `initial state_ions_amounts` [1D np.ndarray]:
        - vector of initial internal ionic amounts (in moles)
    `parameters` [dict]:
        - dictionary of simulation parameters, including the following key/value pairs:
            `dt` [float]:
                - time step, seconds
            `T` [float]:
                - simulations length, seconds
            `G` [dict]:
                - dictionary containing conductances for the following channel types:
                    - ASOR, ClC, TPC, NHE, vATPase, H leak, K channel
            `external_ions_concentrations` [1D np.ndarray]:
                - external_ions_concentrations in M,
            `A_from_V_const` [float]
                - area calculated from the volume
            `buffer_capacity_T0` [float]:
                - buffer capacity at initial time
             `V_t0` [float]:
                - initial volume (in m3)
            `c_spec` [float]:
                - membrane capacitance (in F/(m**2))
            `RT` [float]:
                - Gas constant x Temperature 
            `F` [float]:
                - Faraday's constant 
            `ASOR_pH_k2` [float]:
                - exponential scaling parameter of the ASOR pH dependence 
            `ASOR_pH_half` [float]:
                - pH1/2 of ASOR activation
            `ASOR_U_k2` [float]:
                - exponential scaling parameter of the ASOR voltage dependence 
            `ASOR_U_half` [float]:
                - U1/2 of ASOR activation
            `CLC_pH_k2` [float]:
                - exponential scaling parameter of the CLC pH dependence 
            `CLC_pH_half` [float]:
                - pH1/2 of CLC activation
            `CLC_U_k2` [float]:
                - exponential scaling parameter of the CLC voltage dependence 
            `CLC_U_half` [float]:
                - U1/2 of CLC activation


    Returns
    =======
    `results` [dict]:
        - dictionary of simulation outome
            `internal_ions` [dict]:
                - dictionary containing internal concentrations and amounts of Na, Cl, H and K ions throught simulation
            `fluxes` [dict]:
                - dictionary containing fluxes of Cl, Na, H and K ions through ASOR, CLC, NHE, vATPase, H_leak and K channels throught simulation
            `other_variables` [dict]:
                - dictionary containing information about dependency functions outcomes and variables regarding vesicle properties (pH, volume, membrane area, membrane capacitance and buffer capacity) throught simulation

    """

    ''' Initialize variables for the simulation '''
    dt, T = parameters['dt'], parameters['T']
    time_axis = np.arange(0, T, dt)
    
    ''' Initialize arrays / dictionaries to store the histories of each variable-of-interest over time '''
    ions_t = np.empty((4, len(time_axis)))
    ions_t[:,0] = initial_state_ions_amounts

    V_t = np.empty(len(time_axis))
    V_t[0] = parameters['V_t0']

    flux_history_dictionary = {'ClC_ASOR': np.zeros(len(time_axis)-1),
                                'ClC_CLC': np.zeros(len(time_axis)-1), 
                                'Na_TPC': np.zeros(len(time_axis)-1), 
                                'Na_NHE': np.zeros(len(time_axis)-1),
                                'H_Cl': np.zeros(len(time_axis)-1),
                                'H_NHE': np.zeros(len(time_axis)-1),
                                'H_vATPase': np.zeros(len(time_axis)-1),
                                'H_leak': np.zeros(len(time_axis)-1),
                                'K': np.zeros(len(time_axis)-1)
                                }

    dependency_histories = {'pH_ASOR': np.zeros(len(time_axis)),
                            'v_ASOR': np.zeros(len(time_axis)),
                            'pH_CLC': np.zeros(len(time_axis)),
                            'v_CLC': np.zeros(len(time_axis)),
                            't_vATPase': np.zeros(len(time_axis)),
                            'pH_t': np.zeros(len(time_axis)),
                            'A_t': np.zeros(len(time_axis)),
                            'C_t': np.zeros(len(time_axis)),
                            'buffer_capacity_t': np.zeros(len(time_axis)),
                            'U': np.zeros(len(time_axis))
                            }

    dependency_histories['pH_ASOR'][0] = dep_funct.pH_dependence_ASOR(parameters['pH_i'], pH_k2 = parameters['ASOR_pH_k2'], pH_half = parameters['ASOR_pH_half'])
    dependency_histories['v_ASOR'][0] = dep_funct.v_dependence_ASOR(parameters['U0'], U_k2 = parameters['ASOR_U_k2'], U_half = parameters['ASOR_U_half'])
    dependency_histories['pH_CLC'][0] = dep_funct.pH_dependence_ClC(parameters['pH_i'], pH_k2 = parameters['CLC_pH_k2'], pH_half = parameters['CLC_pH_half'])
    dependency_histories['v_CLC'][0] = dep_funct.v_dependence_ClC(parameters['U0'], U_k2 = parameters['CLC_U_k2'], U_half = parameters['CLC_U_half'])
    dependency_histories['t_vATPase'][0] = dep_funct.g_VATP_dependence(time_axis[0])
    dependency_histories['pH_t'][0] = parameters['pH_i']
    dependency_histories['A_t'][0] = parameters['A0']
    dependency_histories['C_t'][0] = parameters['C0']
    dependency_histories['buffer_capacity_t'][0] = parameters['buffer_capacity_t0']
    dependency_histories['U'][0] = parameters['U0']

    G = parameters['G']
    ext_ion = parameters['external_ions_concentrations']
    A_from_V_const = parameters['A_from_V_const']
    X_amount = parameters['X_amount']
    buffer_capacity_t0 = parameters['buffer_capacity_t0']
    V_t0 = parameters['V_t0']
    c_spec = parameters['c_spec']
    RT = parameters['RT']
    F = parameters['F']

    for t in range(1,len(time_axis)):

        ''' Compute the flows and local variables to store at this timestep''' 
        dIons_dt, fluxes, deps, local_vars = compute_flows(time_axis[t], ions_t[:, t-1], V_t[t-1], G, ext_ion, A_from_V_const, X_amount, buffer_capacity_t0, V_t0, c_spec, parameters['ASOR_pH_k2'], parameters['ASOR_pH_half'], parameters['ASOR_U_k2'], parameters['ASOR_U_half'], parameters['CLC_pH_k2'], parameters['CLC_pH_half'], parameters['CLC_U_k2'], parameters['CLC_U_half'])

        ''' update the ion amounts using the flows and store '''
        ions_t[:,t] = update_euler(ions_t[:,t-1], dt, dIons_dt)

        ''' store other relevant variables in history array '''
        flux_history_dictionary['ClC_ASOR'][t-1] = fluxes['Cl_asor']
        flux_history_dictionary['ClC_CLC'][t-1] = fluxes['Cl_CLC']
        flux_history_dictionary['Na_TPC'][t-1] = fluxes['Na_tpc']
        flux_history_dictionary['Na_NHE'][t-1] = fluxes['Na_nhe']
        flux_history_dictionary['H_Cl'][t-1] = fluxes['H_CLC']
        flux_history_dictionary['H_NHE'][t-1] = fluxes['H_NHE']
        flux_history_dictionary['H_vATPase'][t-1] = fluxes['H_VATPase']
        flux_history_dictionary['H_leak'][t-1] = fluxes['H_leak']
        flux_history_dictionary['K'][t-1] = fluxes['K']

        dependency_histories['pH_ASOR'][t] = deps['pH_ASOR']
        dependency_histories['v_ASOR'][t] = deps['v_ASOR']
        dependency_histories['pH_CLC'][t] = deps['pH_ClC']
        dependency_histories['v_CLC'][t] = deps['v_ClC']
        dependency_histories['t_vATPase'][t] = deps['t_VATPase']
        dependency_histories['pH_t'][t] = local_vars['pH_local']
        dependency_histories['A_t'][t] = local_vars['A']
        dependency_histories['C_t'][t] = local_vars['C']
        dependency_histories['buffer_capacity_t'][t] = local_vars['Buffer_T']
        dependency_histories['U'][t] = local_vars['U']

        ''' update volume using the ion amounts and the initial amounts and store '''
        V_t[t] = (V_t0*(ions_t[Cl_idx, t]+ions_t[Na_idx,t]+ions_t[K_idx,t] + abs(parameters['X_amount'])))/parameters['Sum_initial_amounts']
    
    ions_t_concen = ions_t/ (V_t[t] *1000)

    ''' Package output of simulation into results dictionary / some understandable datastructure that is useful for downstream plotting/processing/etc.'''

    results = {}
    results['internal_ions'] = {'Na': {'amounts': ions_t[Na_idx,:], 'concentrations': ions_t_concen[Na_idx,:]}, 
                                "H": {'amounts': ions_t[H_idx,:], 'concentrations': ions_t_concen[H_idx,:]}, 
                                "Cl": {'amounts': ions_t[Cl_idx,:], 'concentrations': ions_t_concen[Cl_idx,:]}, 
                                "K": {'amounts': ions_t[K_idx,:], 'concentrations': ions_t_concen[K_idx,:]}
                                }
    results['fluxes'] = {'Cl': {'ASOR': flux_history_dictionary['ClC_ASOR'], 'CLC': flux_history_dictionary['ClC_CLC']},
                        'Na': {'TPC': flux_history_dictionary['Na_TPC'], 'NHE':  flux_history_dictionary['Na_NHE']},
                        'H': {'CLC': flux_history_dictionary['H_Cl'], 'NHE': flux_history_dictionary['H_NHE'], 'vATPase':  flux_history_dictionary['H_vATPase'], 'H_leak': flux_history_dictionary['H_leak']},
                        'K': {'K': flux_history_dictionary['K']}
                        }
    results['other_variables'] = {'dependencies': {'pH_ASOR': dependency_histories['pH_ASOR'], 'v_ASOR': dependency_histories['v_ASOR'], 'pH_CLC': dependency_histories['pH_CLC'], 'v_CLC': dependency_histories['v_CLC'], 't_vATPase': dependency_histories['t_vATPase']},
                                  'vesicle_parameters': {'pH': dependency_histories['pH_t'], 'V': V_t, 'A':  dependency_histories['A_t'], 'C': dependency_histories['C_t'], 'buffer_capacity': dependency_histories['buffer_capacity_t'], 'U': dependency_histories['U']}  
                                }

    return results


