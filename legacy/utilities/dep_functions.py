import numpy as np

"""Voltage and acidity dependence functions (nonlinear) and turn-on of proton pump"""

'''def pH_dependence(h_prime, k1 = 7.63*1e4, hprime_half = 3.2 * 1e-5):
   return 1.0 / (1.0 + np.exp(-k1*(h_prime - hprime_half)))

   Equations for pH- and V- dependency functions:
   f(pH) = 1 / (1 + e(k1*(pH-pH1/2)) 
   f(U) = 1 / (1 + e(k2*(U-U1/2))
'''   

# ASOR pH dependency function 

def pH_dependence_ASOR(pH, pH_k2=3.0, pH_half=5.4):
    """
    When simulating wild-type ASOR pH dependency function, pH_k2 = 3.0, pH_half = 5.4
    When simulating ASOR alkaline shifted mutant pH dependency function channel, pH_k2 = 1.0, pH_half = 7.4
    When simulating ASOR without pH-dependency, pH_k2 = 0, pH_half = 0
    """
    return 1.0 / (1.0 + np.exp(pH_k2*(pH-pH_half)))

# ASOR voltage dependency function
def v_dependence_ASOR(U, U_k2=80.0, U_half = -40*1e-3):
    """
    When simulating wild-type ASOR voltage dependency function, U_k2 = 80.0, U_half = -40*1e-3
    When simulating ASOR without voltage-dependency, U_k2 = 0, U_half = 0
    """
    return 1.0 / (1.0 + np.exp(U_k2*(U - U_half)))

# ClC pH dependency function
def pH_dependence_ClC(pH, pH_k2=1.5, pH_half=5.5):
    """
    When simulating wild-type CLC pH dependency function, pH_k2 = 1.5, pH_half = 5.5
    When simulating CLC without pH-dependency, pH_k2 = 0, pH_half = 0
    """
    return 1.0 / (1.0 + np.exp(pH_k2*(pH_half-pH)))

# ClC voltage dependency function
def v_dependence_ClC(U, U_k2=80, U_half = -40*1e-3):
    """
    When simulating wild-type CLC voltage dependency function, U_k2 = 80.0, U_half = -40*1e-3
    When simulating CLC without voltage-dependency, U_k2 = 0, U_half = 0
    """
    return 1.0 / (1.0 + np.exp(U_k2*(U - U_half)))

# V-ATPase insertion function
def g_VATP_dependence(t, k=0, t_half=0):
    return 1.0 / (1.0 + np.exp(k*(t_half - t)))