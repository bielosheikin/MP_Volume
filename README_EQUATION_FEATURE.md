# Channel Parameters Equation Display

## Overview
This feature adds an interactive equation display to the channel parameter editor. When editing channel parameters, you'll now see the mathematical equations that use these parameters, updating in real-time as you modify the values.

## How It Works
When you click "Edit" on a channel in the Channels tab, the parameter editor dialog will open with a split view:
- Left side: Parameter editing fields
- Right side: Mathematical equations and parameter descriptions

The displayed equations will update automatically as you change parameters, showing you exactly how your changes affect the underlying calculations.

## Equations Displayed

### Nernst Potential Equation
This equation shows how the Nernst potential is calculated for the ion channel:

For a single-ion channel:
```
V_nernst = voltage_multiplier * V + nernst_multiplier * RT/F * ln([ion_out] / [ion_in]) - voltage_shift
```

For a two-ion channel:
```
V_nernst = voltage_multiplier * V + nernst_multiplier * RT/F * ln([ion1_out]^p * [ion2_in]^s / ([ion1_in]^p * [ion2_out]^s)) - voltage_shift
```

### Flux Equation
This equation shows how the ion flux is calculated:

Basic formula:
```
J = flux_multiplier * V_nernst * conductance * area
```

With additional terms for dependencies:

For voltage dependency:
```
J = J * (1 / (1 + exp(V_exp * (V - V_half))))
```

For pH dependency:
```
J = J * (1 / (1 + exp(pH_exp * (pH_half - pH))))
```

For time dependency:
```
J = J * (1 / (1 + exp(t_exp * (t_half - t))))
```

## Parameter Descriptions
Each parameter has a description explaining its role in the equations:

- **conductance**: Base conductance of the channel (S/m²)
- **voltage_multiplier**: Multiplier for the voltage term in the Nernst equation
- **nernst_multiplier**: Multiplier for the concentration-dependent term in the Nernst equation
- **voltage_shift**: Constant offset added to the Nernst potential (V)
- **flux_multiplier**: Multiplier for the final flux calculation
- **primary_exponent**: Exponent for the primary ion concentration in the Nernst equation
- **secondary_exponent**: Exponent for the secondary ion concentration in the Nernst equation
- **voltage_exponent**: Slope factor for voltage-dependent activation
- **half_act_voltage**: Voltage at which the channel is half-activated (V)
- **pH_exponent**: Slope factor for pH-dependent activation
- **half_act_pH**: pH at which the channel is half-activated
- **time_exponent**: Slope factor for time-dependent activation
- **half_act_time**: Time at which the channel is half-activated (s)

## Best Practices
1. When setting up a new channel, refer to the equations to understand how your parameters affect the flux calculation
2. Use the real-time equation updates to fine-tune channel behavior
3. Refer to the parameter descriptions to understand what each value represents 