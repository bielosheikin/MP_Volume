from src.backend.simulation import Simulation
from src.backend.ion_species import IonSpecies
from src.backend.ion_channels import IonChannel
from src.backend.simulation_suite import SimulationSuite
from src.app_settings import DEBUG_LOGGING
import os

# Ensure simulation_suites directory exists
if not os.path.exists("simulation_suites"):
    os.makedirs("simulation_suites")

# Create a suite
print("Creating simulation suite...")
suite = SimulationSuite('test_suite')

# Create a basic simulation
print("Creating test simulation...")
sim = Simulation(
    display_name="Test Simulation",
    time_step=0.001,
    total_time=100.0,
    temperature=310.0,
    simulations_path=os.path.join("simulation_suites", "test_suite")
)

# Add some species
h = IonSpecies(display_name="h", init_vesicle_conc=1e-7, exterior_conc=1e-7, elementary_charge=1)
na = IonSpecies(display_name="na", init_vesicle_conc=0.001, exterior_conc=0.145, elementary_charge=1)
k = IonSpecies(display_name="k", init_vesicle_conc=0.14, exterior_conc=0.003, elementary_charge=1)

# Add species to simulation
sim.config.species = {
    "h": h,
    "na": na,
    "k": k
}

# Create a simple channel
leak = IonChannel(display_name="leak", conductance=1e-9, channel_type="leak")

# Add channel to simulation
sim.config.channels = {
    "leak": leak
}

# Set up vesicle parameters
sim.config.vesicle_params = {
    "init_volume": 5.23e-19,
    "surface_area": 5.02e-13,
    "relative_buffer_capacity": 20
}

# Set up exterior parameters
sim.config.exterior_params = {
    "volume": 1e-12
}

# Save the simulation to the suite
print("Adding simulation to suite...")
suite.add_simulation(sim)

# Run the simulation briefly
print("Running simulation...")
sim.run()

# Save again after running
print("Saving simulation after running...")
suite.save_simulation(sim)

print(f"Test simulation created with hash: {sim.config.to_sha256_str()}")
print("Done!") 