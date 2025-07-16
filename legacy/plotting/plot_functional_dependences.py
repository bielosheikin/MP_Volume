import matplotlib 
import matplotlib.pyplot as plt
import numpy as np
from utilities import dep_functions as dep_funct

def plot_dependency ():
    pH_step=0.1
    pH_start=1
    pH_end=12
    voltage_step=5*1e-3
    voltage_start=-100*1e-3
    voltage_end=100*1e-3

    pH_axis = np.arange(pH_start, pH_end, pH_step)
    voltage_axis = np.arange(voltage_start, voltage_end, voltage_step)

    pH_values_ASOR_wt=np.zeros(len(pH_axis))
    pH_values_ASOR_mutant=np.zeros(len(pH_axis))
    U_values_ASOR=np.zeros(len(voltage_axis))
    pH_values_ClC=np.zeros(len(pH_axis))
    U_values_ClC=np.zeros(len(voltage_axis))

    pH = pH_start
    for i in range(len(pH_axis)):
        pH = pH + pH_step
        pH_values_ASOR_wt[i] = dep_funct.pH_dependence_ASOR(pH)
        pH_values_ClC[i] = dep_funct.pH_dependence_ClC(pH)
        pH_values_ASOR_mutant[i]=dep_funct.pH_dependence_ASOR(pH, pH_k2=1.0, pH_half=7.4)

    for i in range(len(voltage_axis)):
        U_values_ASOR[i]=dep_funct.v_dependence_ASOR(voltage_axis[i])
        U_values_ClC[i]=dep_funct.v_dependence_ClC(voltage_axis[i])

    fig,axes = plt.subplots(2,2, figsize = (10,10))
    matplotlib.rcParams['font.sans-serif'] = "Arial"
    matplotlib.rcParams['font.family'] = "sans-serif"


    axes[0,0].plot(pH_axis,pH_values_ClC, color=u'#348ABD', linewidth=1)
    axes[0,0].set_title('ClC', fontsize=20, pad=25, fontname="Arial")
    axes[0,0].spines['right'].set_visible(False)
    axes[0,0].spines['top'].set_visible(False)
    axes[0,0].spines['bottom'].set_linewidth(0.4)
    axes[0,0].spines['left'].set_linewidth(0.4)
    axes[0,0].spines['left'].set_position(('outward', 5))
    axes[0,0].tick_params(axis='both', which='major', labelsize=16, width=0.2)
    axes[0,0].set_ylabel('pH-dependency function', fontname="Arial", fontsize =24, labelpad=25)
    axes[0,0].set_xlabel('pH', fontname="Arial", fontsize =18)
    axes[0,0].set_xticks(np.arange(2, 13, 2.0))

    line,=axes[0,1].plot(pH_axis,pH_values_ASOR_wt, color=u'#348ABD', linewidth=1, label='ASOR wild-type')
    line,=axes[0,1].plot(pH_axis,pH_values_ASOR_mutant, color=u'#E24A33', linewidth=1, label='pH-shifted ASOR mutant')
    axes[0,1].set_title('ASOR', fontsize=20, pad=25, fontname="Arial")
    axes[0,1].spines['right'].set_visible(False)
    axes[0,1].spines['top'].set_visible(False)
    axes[0,1].spines['bottom'].set_linewidth(0.4)
    axes[0,1].spines['left'].set_linewidth(0.4)
    axes[0,1].spines['left'].set_position(('outward', 5))
    axes[0,1].tick_params(axis='both', which='major', labelsize=16, width=0.2)
    # axes[0,0].set_ylabel('pH', fontname="Arial", fontsize =24)
    axes[0,1].set_xlabel('pH', fontname="Arial", fontsize =18)
    axes[0,1].set_xticks(np.arange(2, 13, 2.0))
    axes[0,1].legend(loc=1, bbox_to_anchor=(0.8, 0.5, 0.5, 0.5), fontsize=14, frameon=False)

    axes[1,0].plot(voltage_axis*1000,U_values_ClC, color=u'#348ABD', linewidth=1)
    # axes[1,0].set_title('ClC voltage-dependence', fontsize=20)
    axes[1,0].spines['right'].set_visible(False)
    axes[1,0].spines['top'].set_visible(False)
    axes[1,0].spines['bottom'].set_linewidth(0.4)
    axes[1,0].spines['left'].set_linewidth(0.4)
    axes[1,0].spines['left'].set_position(('outward', 5))
    axes[1,0].tick_params(axis='both', which='major', labelsize=16, width=0.2)
    axes[1,0].set_ylabel('U-dependency function', fontname="Arial", fontsize =24, labelpad=25)
    axes[1,0].set_xlabel('U, mV', fontname="Arial", fontsize =18)

    axes[1,1].plot(voltage_axis*1000,U_values_ASOR, color=u'#348ABD', linewidth=1)
    # axes[1,1].set_title('ASOR', fontsize=20)
    axes[1,1].spines['right'].set_visible(False)
    axes[1,1].spines['top'].set_visible(False)
    axes[1,1].spines['bottom'].set_linewidth(0.4)
    axes[1,1].spines['left'].set_linewidth(0.4)
    axes[1,1].spines['left'].set_position(('outward', 5))
    axes[1,1].tick_params(axis='both', which='major', labelsize=16, width=0.2)
    # axes[0,0].set_ylabel('pH', fontname="Arial", fontsize =24)
    axes[1,1].set_xlabel('U, mV', fontname="Arial", fontsize =18)

    plt.subplots_adjust(wspace=None, hspace=0.35)

    plt.show()
