from src.backend.simulation_suite import SimulationSuite

def check_simulations():
    try:
        print("Creating simulation suite object...")
        suite = SimulationSuite('TestSuite')
        
        print("Listing simulations (including problematic ones)...")
        simulations = suite.list_simulations(skip_problematic=False)
        print(f'Number of simulations: {len(simulations)}')
        
        # Display information about each simulation
        for i, sim in enumerate(simulations):
            problematic = sim.get('is_problematic', False)
            status = "⚠️ PROBLEMATIC" if problematic else "✓ OK"
            print(f"{i+1}. {sim['display_name']} - Hash: {sim['hash']} - {status}")
            
        # Try to get a simulation if there are any
        if simulations:
            print("\nTrying to load the first simulation...")
            first_sim = suite.get_simulation(simulations[0]['hash'])
            if first_sim:
                print(f"Successfully loaded: {first_sim.display_name}")
                print(f"Has config: {hasattr(first_sim, 'config')}")
                if hasattr(first_sim, 'config'):
                    print(f"Config attributes: {dir(first_sim.config)}")
            else:
                print("Failed to load the simulation.")
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    check_simulations() 