import numpy as np

"""Potential functions"""

def nernst_potential_Cl_asor(U, ion_outside, ion_inside, RTdivF):
    return U + (RTdivF * np.log(ion_outside/ion_inside))

def nernst_potential_Na_K(U, ion_outside, ion_inside, RTdivF):
    return -U + (RTdivF * np.log(ion_outside/ion_inside))

def nernst_potential_CLC(U, Cl_i, Cl_o, hprime_i, hprime_o, RT = 2477.572, F = 96485.0):
    return U + ((RT/(3*F)) * np.log( ((Cl_o**2) / (Cl_i**2)) * (hprime_i/hprime_o) ))

def potential_NHE(Na_o, Na_i, hprime_i, hprime_o):
    return  np.log( (Na_o/Na_i) * (hprime_i/hprime_o))

def nernst_potential_VATPase(U, ion_outside, ion_inside, RTdivF, U_ATP=0.27):
    return U - (RTdivF * np.log(ion_outside/ion_inside)) - U_ATP

def nernst_potential_H_leak(U, hprime_o, h_prime_i, RTdivF):
    return -U + (RTdivF * np.log(hprime_o/h_prime_i))