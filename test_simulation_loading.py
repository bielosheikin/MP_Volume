from src.backend.simulation_suite import SimulationSuite
from src.app_settings import DEBUG_LOGGING
import sys

# Enable debug logging
print(f"Debug logging is {'enabled' if DEBUG_LOGGING else 'disabled'}")

# Create a suite
print("Creating simulation suite...")
suite = SimulationSuite('test_suite')

# List simulations
print("Listing simulations...")
simulations = suite.list_simulations(skip_problematic=False)
print(f"Found {len(simulations)} simulations")

# Try to load first simulation if any exists
if simulations:
    sim_hash = simulations[0]['hash']
    print(f"Attempting to load simulation with hash: {sim_hash}")
    
    try:
        sim = suite.load_simulation(sim_hash)
        if sim:
            print(f"Successfully loaded simulation: {sim.display_name}")
            print(f"Simulation has 'config' attribute: {hasattr(sim, 'config')}")
            if hasattr(sim, 'config'):
                print(f"Config has 'species' attribute: {hasattr(sim.config, 'species')}")
                print(f"Config has 'channels' attribute: {hasattr(sim.config, 'channels')}")
        else:
            print("Failed to load simulation - returned None")
    except Exception as e:
        import traceback
        print(f"Error loading simulation: {str(e)}")
        print(traceback.format_exc())
else:
    print("No simulations found to load")

print("Test complete") 