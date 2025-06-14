class EquationGenerator:
    """
    Generates rich text formatted equations for channel parameters.
    This class provides method to create pseudo-LaTeX formatted equations in HTML/rich text format.
    """
    
    @staticmethod
    def format_fraction(numerator, denominator):
        """
        Format a fraction with proper layout using HTML table approach
        which is more reliable than DIVs or SPANs for consistent display
        """
        return (
            f'<table style="display:inline-table; border-collapse:collapse; vertical-align:middle; margin:0 2px; line-height:1.2;">'
            f'<tr><td style="border-bottom:1px solid black; text-align:center; padding:1px 3px;">{numerator}</td></tr>'
            f'<tr><td style="text-align:center; padding:1px 3px;">{denominator}</td></tr>'
            f'</table>'
        )
    
    @staticmethod
    def format_special_value(value):
        """Format special values like 0.333333 to 1/3"""
        if isinstance(value, (int, float)):
            # Special case for 1/3
            if abs(value - 1/3) < 0.001:
                return EquationGenerator.format_fraction("1", "3")
            # Special case for 2/3
            elif abs(value - 2/3) < 0.001:
                return EquationGenerator.format_fraction("2", "3")
            # Special case for 1/2
            elif abs(value - 1/2) < 0.001:
                return EquationGenerator.format_fraction("1", "2")
            # Value is 1, just return "1"
            elif abs(value - 1.0) < 0.001:
                return "1"
        # For other values, return as string
        return str(value)
    
    @staticmethod
    def nernst_potential_equation(parameters, primary_ion, secondary_ion=None):
        """
        Generate the Nernst potential equation in rich text format using a table layout.
        """
        # Get relevant parameters with robust conversion
        try:
            voltage_multiplier = float(parameters.get('voltage_multiplier', 1.0))
        except (ValueError, TypeError):
            voltage_multiplier = 1.0
            
        try:
            nernst_multiplier = float(parameters.get('nernst_multiplier', 1.0))
        except (ValueError, TypeError):
            nernst_multiplier = 1.0
            
        try:
            voltage_shift = float(parameters.get('voltage_shift', 0.0))
        except (ValueError, TypeError):
            voltage_shift = 0.0
            
        try:
            primary_exp = int(parameters.get('primary_exponent', 1))
        except (ValueError, TypeError):
            primary_exp = 1
            
        try:
            secondary_exp = int(parameters.get('secondary_exponent', 0 if not secondary_ion else 1))
        except (ValueError, TypeError):
            secondary_exp = 0 if not secondary_ion else 1
            
        # Check for custom Nernst constant
        try:
            custom_nernst = parameters.get('custom_nernst_constant')
            if custom_nernst and custom_nernst.strip():
                custom_nernst = float(custom_nernst)
                has_custom_nernst = True
            else:
                has_custom_nernst = False
        except (ValueError, TypeError, AttributeError):
            has_custom_nernst = False
            custom_nernst = None
        
        # Check if hydrogen is involved and if using free hydrogen
        use_free_hydrogen = parameters.get('use_free_hydrogen', False)
        primary_involves_hydrogen = primary_ion and primary_ion.lower() == 'h'
        secondary_involves_hydrogen = secondary_ion and secondary_ion.lower() == 'h'
        
        # Format the primary ion concentrations
        if primary_involves_hydrogen:
            h_prefix = "free" if use_free_hydrogen else "total"
            primary_out = f"[{primary_ion}<sub>{h_prefix}, out</sub>]"
            primary_in = f"[{primary_ion}<sub>{h_prefix}, in</sub>]"
        else:
            primary_out = f"[{primary_ion}<sub>out</sub>]"
            primary_in = f"[{primary_ion}<sub>in</sub>]"
        
        # Add exponents if not 1
        if primary_exp != 1:
            primary_out = f"{primary_out}<sup>{primary_exp}</sup>"
            primary_in = f"{primary_in}<sup>{primary_exp}</sup>"
        
        # Build the equation using a table layout
        html = '<table style="border-collapse:collapse; margin:0; border:none; display:inline-table;">'
        html += '<tr style="vertical-align:middle;">'
        
        # First cell - Vnernst = 
        html += '<td style="padding:2px; text-align:left; white-space:nowrap; vertical-align:middle;">V<sub>nernst</sub> = </td>'
        
        # Add voltage_multiplier * V term
        if voltage_multiplier != 0:
            # Format voltage_multiplier
            if voltage_multiplier != 1:
                formatted_voltage_mult = EquationGenerator.format_special_value(abs(voltage_multiplier))
                # Sign handling
                if voltage_multiplier < 0:
                    html += f'<td style="padding:2px; text-align:center; vertical-align:middle;">-{formatted_voltage_mult}</td>'
                else:
                    html += f'<td style="padding:2px; text-align:center; vertical-align:middle;">{formatted_voltage_mult}</td>'
                html += '<td style="padding:2px; text-align:center; vertical-align:middle;">×</td>'
            
            # Add V term
            html += '<td style="padding:2px; text-align:center; vertical-align:middle;">V</td>'
        else:
            # If voltage_multiplier is 0, just show 0
            html += '<td style="padding:2px; text-align:center; vertical-align:middle;">0</td>'
        
        # Nernst Multiplier
        if nernst_multiplier != 0:
            # Sign
            sign = "+" if nernst_multiplier > 0 else "-"
            html += f'<td style="padding:2px; text-align:center; vertical-align:middle;">{sign}</td>'
            
            # Multiplier value if not 1
            if abs(nernst_multiplier) != 1:
                formatted_multiplier = EquationGenerator.format_special_value(abs(nernst_multiplier))
                html += f'<td style="padding:2px; text-align:center; vertical-align:middle;">{formatted_multiplier}</td>'
                html += '<td style="padding:2px; text-align:center; vertical-align:middle;">×</td>'
            
            # Nernst Term - either RT/F or custom value
            if has_custom_nernst:
                # Use the custom Nernst constant
                nernst_constant = str(custom_nernst)
                html += f'<td style="padding:2px; text-align:center; vertical-align:middle;">{nernst_constant}</td>'
            else:
                # Use the standard RT/F term
                rt_f = EquationGenerator.format_fraction("RT", "F")
                html += f'<td style="padding:2px; text-align:center; vertical-align:middle;">{rt_f}</td>'
            
            # Multiplication
            html += '<td style="padding:2px; text-align:center; vertical-align:middle;">×</td>'
            
            # ln term
            html += '<td style="padding:2px; text-align:center; vertical-align:middle;">ln(</td>'
            
            # Ion ratio
            if not secondary_ion or secondary_exp == 0:
                # Simple ratio for single ion - use standard format (exterior/vesicle)
                ion_ratio = EquationGenerator.format_fraction(primary_out, primary_in)
                html += f'<td style="padding:2px; text-align:center; vertical-align:middle;">{ion_ratio}</td>'
            else:
                # Two-ion channel
                if secondary_involves_hydrogen:
                    h_prefix = "free" if use_free_hydrogen else "total"
                    secondary_out = f"[{secondary_ion}<sub>{h_prefix}, out</sub>]"
                    secondary_in = f"[{secondary_ion}<sub>{h_prefix}, in</sub>]"
                else:
                    secondary_out = f"[{secondary_ion}<sub>out</sub>]"
                    secondary_in = f"[{secondary_ion}<sub>in</sub>]"
                
                # Add exponents if not 1
                if secondary_exp != 1:
                    secondary_out = f"{secondary_out}<sup>{secondary_exp}</sup>"
                    secondary_in = f"{secondary_in}<sup>{secondary_exp}</sup>"
                
                # Format the complex ratio using standard thermodynamic format
                # Standard format: (primary_out^n1 × secondary_in^n2) / (primary_in^n1 × secondary_out^n2)
                primary_term = primary_out
                primary_term_inv = primary_in
                secondary_term = secondary_in
                secondary_term_inv = secondary_out
                
                numerator = f"{primary_term} × {secondary_term}"
                denominator = f"{primary_term_inv} × {secondary_term_inv}"
                complex_ratio = EquationGenerator.format_fraction(numerator, denominator)
                html += f'<td style="padding:2px; text-align:center; vertical-align:middle;">{complex_ratio}</td>'
            
            # Closing parenthesis
            html += '<td style="padding:2px; text-align:center; vertical-align:middle;">)</td>'
        
        # Add voltage shift if not zero
        if voltage_shift != 0:
            sign = "-" if voltage_shift > 0 else "+"
            shift_value = abs(voltage_shift)
            html += f'<td style="padding:2px; text-align:center; vertical-align:middle;">{sign}</td>'
            html += f'<td style="padding:2px; text-align:center; vertical-align:middle;">{shift_value}</td>'
        
        # Close the table
        html += '</tr></table>'
        
        return html
    
    @staticmethod
    def flux_equation(parameters, primary_ion, secondary_ion=None):
        """
        Generate the flux equation in rich text format using a table layout.
        """
        dependence_type = parameters.get('dependence_type')
        
        # Normalize dependence_type for case-insensitive comparison
        normalized_dependence = dependence_type.lower() if isinstance(dependence_type, str) else None
        
        # Get flux multiplier with robust conversion
        try:
            flux_multiplier = float(parameters.get('flux_multiplier', 1.0))
        except (ValueError, TypeError):
            flux_multiplier = 1.0
        
        # Start building the table for the equation
        html = '<table style="border-collapse:collapse; margin:0; border:none; display:inline-table;">'
        html += '<tr style="vertical-align:middle;">'
        
        # J = 
        html += '<td style="padding:2px; text-align:left; white-space:nowrap; vertical-align:middle;">J = </td>'
        
        # Flux multiplier
        if flux_multiplier != 1:
            formatted_multiplier = EquationGenerator.format_special_value(flux_multiplier)
            html += f'<td style="padding:2px; text-align:center; vertical-align:middle;">{formatted_multiplier}</td>'
            html += '<td style="padding:2px; text-align:center; vertical-align:middle;">×</td>'
        
        # V_nernst and other base terms
        html += '<td style="padding:2px; text-align:center; vertical-align:middle;">V<sub>nernst</sub></td>'
        html += '<td style="padding:2px; text-align:center; vertical-align:middle;">×</td>'
        html += '<td style="padding:2px; text-align:center; vertical-align:middle;">conductance</td>'
        html += '<td style="padding:2px; text-align:center; vertical-align:middle;">×</td>'
        html += '<td style="padding:2px; text-align:center; vertical-align:middle;">area</td>'
        
        # Add dependencies if applicable
        if normalized_dependence in ["voltage", "voltage_and_ph"]:
            try:
                v_exp = float(parameters.get('voltage_exponent', 80.0))
            except (ValueError, TypeError):
                v_exp = 80.0
                
            try:
                v_half = float(parameters.get('half_act_voltage', -0.04))
            except (ValueError, TypeError):
                v_half = -0.04
            
            # Format voltage dependency term
            if v_half < 0:
                # For negative half activation voltage, use (V + |v_half|) to avoid double negative
                voltage_dependency = EquationGenerator.format_fraction("1", f"1 + exp({v_exp} × (V + {abs(v_half)}))")
            else:
                voltage_dependency = EquationGenerator.format_fraction("1", f"1 + exp({v_exp} × (V - {v_half}))")
            html += '<td style="padding:2px; text-align:center; vertical-align:middle;">×</td>'
            html += f'<td style="padding:2px; text-align:center; vertical-align:middle;">{voltage_dependency}</td>'
        
        if normalized_dependence in ["ph", "voltage_and_ph"]:
            try:
                ph_exp = float(parameters.get('pH_exponent', 3.0))
            except (ValueError, TypeError):
                ph_exp = 3.0
                
            try:
                ph_half = float(parameters.get('half_act_pH', 5.4))
            except (ValueError, TypeError):
                ph_half = 5.4
            
            # pH is always pH, regardless of free hydrogen setting
            ph_term = "pH"
            
            # Format pH dependency term
            if ph_exp < 0:
                # For negative pH exponent, swap the order to avoid negation confusion
                ph_dependency = EquationGenerator.format_fraction("1", f"1 + exp({abs(ph_exp)} × (pH - {ph_half}))")
            else:
                ph_dependency = EquationGenerator.format_fraction("1", f"1 + exp({ph_exp} × ({ph_half} - {ph_term}))")
            html += '<td style="padding:2px; text-align:center; vertical-align:middle;">×</td>'
            html += f'<td style="padding:2px; text-align:center; vertical-align:middle;">{ph_dependency}</td>'
        
        if normalized_dependence == "time":
            try:
                t_exp = float(parameters.get('time_exponent', 0.0))
            except (ValueError, TypeError):
                t_exp = 0.0
                
            try:
                t_half = float(parameters.get('half_act_time', 0.0))
            except (ValueError, TypeError):
                t_half = 0.0
            
            # Format time dependency term
            if t_exp < 0:
                # For negative time exponent, swap the order to avoid negation confusion
                time_dependency = EquationGenerator.format_fraction("1", f"1 + exp({abs(t_exp)} × (t - {t_half}))")
            else:
                time_dependency = EquationGenerator.format_fraction("1", f"1 + exp({t_exp} × ({t_half} - t))")
            html += '<td style="padding:2px; text-align:center; vertical-align:middle;">×</td>'
            html += f'<td style="padding:2px; text-align:center; vertical-align:middle;">{time_dependency}</td>'
        
        # Close the table
        html += '</tr></table>'
        
        return html
    
    @staticmethod
    def parameter_descriptions():
        """
        Return a dictionary mapping parameter names to descriptions.
        """
        return {
            'conductance': 'Base conductance of the channel (S/m²)',
            'voltage_multiplier': 'Multiplier for the voltage term in the Nernst equation',
            'nernst_multiplier': 'Multiplier for the concentration-dependent term in the Nernst equation',
            'voltage_shift': 'Constant offset added to the Nernst potential (V)',
            'flux_multiplier': 'Multiplier for the final flux calculation',
            'primary_exponent': 'Exponent for the primary ion concentration in the Nernst equation',
            'secondary_exponent': 'Exponent for the secondary ion concentration in the Nernst equation',
            'custom_nernst_constant': 'Custom value to use instead of RT/F in the Nernst equation',
            'voltage_exponent': 'Slope factor for voltage-dependent activation',
            'half_act_voltage': 'Voltage at which the channel is half-activated (V)',
            'pH_exponent': 'Slope factor for pH-dependent activation',
            'half_act_pH': 'pH at which the channel is half-activated',
            'time_exponent': 'Slope factor for time-dependent activation',
            'half_act_time': 'Time at which the channel is half-activated (s)',
            'invert_primary_log_term': 'Invert the primary ion concentration ratio in the log term (vesicle/exterior instead of exterior/vesicle)',
            'invert_secondary_log_term': 'Invert the secondary ion concentration ratio in the log term (exterior/vesicle instead of vesicle/exterior)'
        } 