# Mathematical model of macropinosome shrinkage repo

Companion repository for "Proton-gated anion transport governs macropinosome shrinkage" by Mariia Zeziulia, Sandy Blin, Franziska W. Schmitt, Martin Lehmann, Thomas J. Jentsch

# Installation 

To run the Python code in this repo, we recommend building a virtual environment using `venv` and the provided `requirements.txt` file, which 
will install all of the required dependencies for you:

```
python3 -m venv my_env
source my_env/bin/activate (for Mac OS)
my_env\Scripts\activate (for Windows)
pip install -r requirements.txt
```

# Usage

## How to run the code

To run the code using an IPython kernel (e.g. in VSCode or Spyder or Pycharm), open up the file `ipython_run.py` in your IDE of choice and then run the code using the parameters provided in figure legends 

If you want to run this from the command line you can also specify particular parameters as additional keyword arguments using 

`python3 run.py [-KEYWORD] [VALUE]`

## Choice of parameters

Parameters that are requested and could be defined from a keyboard:

* g_ASOR
* g_TPC
* g_K (in all simulations is set to 0)
* g_CLC
* g_NHE (in all simulations is set to 0)
* g_vATPase
* g_H-leak
* ASOR pH-dependency could be chosen between wild-type (wt), pH-shifted mutant (mt) or without pH-dependency (none)
* Choice if ASOR has voltage-dependency: yes/no
* Choice if CLC has pH- or voltage-dependency: yes/no
* Initial internal Cl concentration: 'high' = 159mM, 'low' = 9mM, 'zero' = 1mM


If you are running the code from the command line, if no input was provided from a keyboard, default parameters will be used:

- g_asor [--gasor] [-as] = 8 * 10<sup>-5
- g_tpc [--gtpc] [-tpc]  = 2 * 10<sup>-6
- g_k [--gk] [-k] = 0.0
- g_CLC [--gclc] [-clc] = 10 * 10<sup>-8
- g_NHE [--gnhe] [-nhe] = 0.0
- g_VATPase [--gvatpase] [-atp] = 8 * 10<sup>-9
- g_H_leak [--ghleak] [-hlk] = 16 * 10<sup>-9
- ASOR pH-dependency [--ASOR_wt_vs_mutant_vs_none] [-wtmt]: wt
- ASOR voltage-dependency [--ASOR_U_dep] [-audep]: yes
- CLC pH- and voltage-dependency [--CLC_dep] [-cdep]: yes
- Initial internal Cl concentration [--Cli_concentration] [-cli]: 'high'


If you are running the code from IPython kernel, you have to set all parameters from the keyboard. In case of g values, if the indicated value in the manuscript states 2 * 10<sup>-6</sup>, and the window states '10**-6', please input 2; but is the window states '10**-7', please input 20. 

## List of parameters used to generate figures

### Supplementary figure 14

a) g_CLC = 4 * 10<sup>-6</sup>

b) g_ASOR = 4 * 10<sup>-6</sup>, g_CLC = 4 * 10<sup>-6</sup>

c) g_TPC = 1 * 10<sup>-6</sup>, g_CLC = 4 * 10<sup>-6</sup>

d) g_ASOR = 4 * 10<sup>-6</sup>, g_TPC = 1 * 10<sup>-6</sup>, g_CLC = 4 * 10<sup>-6</sup>

e) g_ASOR = 4 * 10<sup>-6</sup>, g_TPC = 1 * 10<sup>-6</sup>

no pH- and voltage-dependency for ASOR and CLC

Initial ClC concentration is set to either 'high' or to 'zero'

### Supplementary figure 15

f(pH) = 1 / (1 + e<sup>(k<sub>1</sub> * (pH - pH<sub>1/2</sub>))</sup>)

f(U) = 1 / (1 + e<sup>(k<sub>2</sub> * (U - U<sub>1/2</sub>))</sup>)

WT ASOR pH-dependency: k<sub>1</sub> = 3, pH<sub>1/2</sub> = 5.4

pH-shifted mutant ASOR pH-dependency: k<sub>1</sub> = 1, pH<sub>1/2</sub> = 7.4

CLC pH-dependency: k<sub>1</sub> = -1.5, pH<sub>1/2</sub> = 5.5

ASOR and CLC voltage dependency: k<sub>2</sub> = 80, U<sub>1/2</sub> = -40

### Supplementary figure 16

a) g_ASOR = 8 * 10<sup>-5</sup>, g_TPC = 2 * 10<sup>-6</sup>, g_CLC = 1 * 10<sup>-7</sup>, g_vATPase = 8 * 10<sup>-9</sup>, g_Hleak = 1.6 * 10<sup>-8</sup>

b) g_TPC = 2 * 10<sup>-6</sup>, g_CLC = 1 * 10<sup>-7</sup>, g_vATPase = 8 * 10<sup>-9</sup>, g_Hleak = 1.6 * 10<sup>-8</sup>

c) g_TPC = 2 * 10<sup>-6</sup>, g_CLC = 1 * 10<sup>-7</sup>, g_Hleak = 1.6 * 10<sup>-8</sup>

d) g_TPC = 2 * 10<sup>-6</sup>, g_CLC = 1 * 10<sup>-7</sup>

e) g_ASOR = 8 * 10<sup>-5</sup>, g_TPC = 2 * 10<sup>-6</sup>, g_vATPase = 8 * 10<sup>-9</sup>, g_Hleak = 1.6 * 10<sup>-8</sup>

f) g_ASOR = 8 * 10<sup>-5</sup>, g_TPC = 2 * 10<sup>-6</sup>, g_CLC = 1 * 10<sup>-7</sup>, g_Hleak = 1.6 * 10<sup>-8</sup>

g) g_ASOR = 8 * 10<sup>-5</sup>, g_TPC = 2 * 10<sup>-6</sup>, g_CLC = 1 * 10<sup>-7</sup>, g_vATPase = 8 * 10<sup>-9</sup>

h) g_ASOR = 8 * 10<sup>-5</sup>, g_TPC = 2 * 10<sup>-6</sup>, g_CLC = 1 * 10<sup>-7</sup>

i) g_ASOR = 8 * 10<sup>-5</sup>, g_TPC = 2 * 10<sup>-6</sup>, g_vATPase = 8 * 10<sup>-9</sup>

j) g_ASOR = 8 * 10<sup>-5</sup>, g_TPC = 2 * 10<sup>-6</sup>, g_Hleak = 1.6 * 10<sup>-8</sup>

k) g_ASOR = 8 * 10<sup>-5</sup>, g_TPC = 2 * 10<sup>-6</sup>

Wild-type pH- and voltage-dependency for ASOR and CLC

Initial ClC concentration is set to either 'high' or to 'low'

### Supplementary figure 17

a) g_ASOR = 4 * 10<sup>-5</sup>, g_ASOR(5x) = 2 * 10<sup>-4</sup>, g_TPC = 1 * 10<sup>-6</sup>, g_CLC = 5 * 10<sup>-8</sup>, g_vATPase = 4 * 10<sup>-9</sup>

Wild-type pH- and voltage-dependency for ASOR and CLC

Initial ClC concentration is set to 'high'
 
