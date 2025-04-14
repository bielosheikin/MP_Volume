import os
import json
import tempfile
import subprocess
from pathlib import Path

# Constants for C++ backend
CPP_EXECUTABLE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                             "cpp_backend", "build", "simulation_engine.exe")

class CppSimulationRunner:
    """
    Handles running simulations using the C++ backend.
    This class serves as a bridge between the Python GUI and the C++ simulation engine.
    """
    
    def __init__(self, simulation):
        """
        Initialize with a Python simulation object.
        
        Args:
            simulation: The Python Simulation object with the configuration
        """
        self.simulation = simulation
        
    def prepare_config(self):
        """
        Convert the Python simulation object to a JSON configuration for the C++ backend.
        
        Returns:
            str: The JSON configuration string
        """
        # Extract simulation parameters
        config = {
            "time_step": self.simulation.config.time_step,
            "total_time": self.simulation.config.total_time,
            "display_name": self.simulation.config.display_name,
            "temperature": self.simulation.config.temperature,
            "init_buffer_capacity": self.simulation.config.init_buffer_capacity,
            
            # Extract vesicle parameters
            "vesicle_params": {
                "init_radius": self.simulation.vesicle.config.init_radius,
                "init_voltage": self.simulation.vesicle.config.init_voltage,
                "init_pH": self.simulation.vesicle.config.init_pH,
                "specific_capacitance": self.simulation.vesicle.config.specific_capacitance,
                "display_name": self.simulation.vesicle.display_name
            },
            
            # Extract exterior parameters
            "exterior_params": {
                "pH": self.simulation.exterior.config.pH,
                "display_name": self.simulation.exterior.display_name
            },
            
            # Extract ion species parameters
            "species": {},
            
            # Extract channel parameters
            "channels": {},
            
            # Extract ion channel links
            "ion_channel_links": {}
        }
        
        # Process ion species
        for species_name, species in self.simulation.species.items():
            config["species"][species_name] = {
                "init_vesicle_conc": species.config.init_vesicle_conc,
                "exterior_conc": species.config.exterior_conc,
                "elementary_charge": species.config.elementary_charge,
                "display_name": species.display_name
            }
        
        # Process channels
        for channel_name, channel in self.simulation.channels.items():
            channel_config = {attr: getattr(channel.config, attr) 
                              for attr in dir(channel.config) 
                              if not attr.startswith('_') and not callable(getattr(channel.config, attr))}
            channel_config["display_name"] = channel.display_name
            config["channels"][channel_name] = channel_config
        
        # Process ion channel links
        for species_name, links in self.simulation.ion_channel_links.config.links.items():
            config["ion_channel_links"][species_name] = links
        
        return json.dumps(config, indent=2)
    
    def run(self, progress_callback=None):
        """
        Run the simulation using the C++ backend.
        
        Args:
            progress_callback: Callback function to report progress (0-100)
            
        Returns:
            dict: The simulation results (histories)
        """
        # Check if the C++ executable exists
        if not os.path.exists(CPP_EXECUTABLE):
            raise FileNotFoundError(f"C++ simulation engine not found at: {CPP_EXECUTABLE}")
        
        # Create temporary files for config and results
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as config_file, \
             tempfile.NamedTemporaryFile(suffix='.json', delete=False) as results_file:
            
            # Write config to file
            config_json = self.prepare_config()
            config_file.write(config_json)
            config_file.flush()
            
            # Close results file so the C++ program can write to it
            results_path = results_file.name
            results_file.close()
            
            # Run C++ executable
            try:
                process = subprocess.Popen(
                    [CPP_EXECUTABLE, config_file.name, results_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1  # Line buffered
                )
                
                # Monitor progress
                for line in iter(process.stdout.readline, ''):
                    if line.startswith("PROGRESS:"):
                        progress = int(line.split(":")[1])
                        if progress_callback:
                            progress_callback(progress)
                    elif line.startswith("ERROR:"):
                        error_msg = line[6:].strip()
                        raise RuntimeError(f"C++ simulation error: {error_msg}")
                
                # Wait for process to complete
                returncode = process.wait()
                
                # Check for errors
                if returncode != 0:
                    stderr = process.stderr.read()
                    raise RuntimeError(f"C++ simulation failed with code {returncode}: {stderr}")
                
                # Read results
                with open(results_path, 'r') as f:
                    results = json.load(f)
                
                # Update the Python simulation object's histories
                self.simulation.histories.histories = results
                self.simulation.has_run = True
                
                return results
                
            finally:
                # Clean up temporary files
                os.unlink(config_file.name)
                if os.path.exists(results_path):
                    os.unlink(results_path) 