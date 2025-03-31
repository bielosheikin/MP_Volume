#!/usr/bin/env python3
import sys
import os
import shutil
import json

# Add the current directory to the path to enable imports
sys.path.insert(0, os.path.abspath('.'))

from src.backend.simulation import Simulation
from src.backend.simulation_suite import SimulationSuite

def clear_test_directory(test_dir="test_simulation_suites"):
    """Clear the test directory to ensure a clean test environment."""
    if os.path.exists(test_dir):
        print(f"Clearing test directory: {test_dir}")
        shutil.rmtree(test_dir)
    os.makedirs(test_dir, exist_ok=True)

def create_test_simulation(name="Test Simulation", temperature=300.0, time_step=0.01, total_time=10.0):
    """Create a test simulation for use in the suite."""
    sim = Simulation(
        display_name=name,
        time_step=time_step,
        total_time=total_time,
        temperature=temperature
    )
    
    # Initialize the simulation
    sim.set_ion_amounts()
    sim.get_unaccounted_ion_amount()
    
    return sim

def test_create_suite(suite_name="TestSuite1", root_dir="test_simulation_suites"):
    """Test creating a simulation suite."""
    print(f"\n=== Testing Suite Creation: {suite_name} ===")
    
    suite = SimulationSuite(suite_name, simulation_suites_root=root_dir)
    print(f"Created suite: {suite.suite_name} at {suite.suite_path}")
    
    # Verify the directory was created
    assert os.path.exists(suite.suite_path), "Suite directory was not created"
    
    print(f"Suite creation test passed for {suite_name}.")
    return suite

def test_add_simulation(suite, name="Simulation1", temperature=300.0):
    """Test adding a simulation to the suite."""
    print(f"\n=== Testing Add Simulation: {name} to {suite.suite_name} ===")
    
    # Create and add a simulation
    sim = create_test_simulation(name, temperature=temperature)
    suite.add_simulation(sim)
    
    # Verify it was added to the in-memory list
    assert any(s.display_name == name for s in suite.simulations), f"{name} not added to list"
    
    # Verify the suite config was saved
    config_path = os.path.join(suite.suite_path, "config.json")
    assert os.path.exists(config_path), "Suite config not saved"
    
    # Print the suite config
    with open(config_path, 'r') as f:
        config = json.load(f)
    print(f"Suite config: {json.dumps(config, indent=2)}")
    
    print(f"Add simulation test passed for {name} in {suite.suite_name}.")
    return sim

def test_save_simulation(suite, sim):
    """Test saving a simulation to the suite."""
    print(f"\n=== Testing Save Simulation: {sim.display_name} in {suite.suite_name} ===")
    
    # Save the simulation
    path = suite.save_simulation(sim)
    print(f"Simulation saved to: {path}")
    
    # Verify the simulation directory was created
    assert os.path.exists(path), "Simulation directory was not created"
    
    # Verify the pickle file was created
    pickle_path = os.path.join(path, "simulation.pickle")
    assert os.path.exists(pickle_path), "Simulation pickle not created"
    
    print(f"Save simulation test passed for {sim.display_name}.")
    return path

def test_list_simulations(suite):
    """Test listing simulations in the suite."""
    print(f"\n=== Testing List Simulations in {suite.suite_name} ===")
    
    # List the simulations
    sims = suite.list_simulations()
    print(f"Found {len(sims)} simulations in {suite.suite_name}:")
    for i, sim in enumerate(sims, 1):
        print(f"{i}. {sim['display_name']} (Index: {sim['index']}, Hash: {sim['hash']})")
    
    # Verify we found at least one simulation
    assert len(sims) > 0, f"No simulations found in {suite.suite_name}"
    
    print(f"List simulations test passed for {suite.suite_name}.")
    return sims

def test_get_simulation(suite, sim_hash, expected_name):
    """Test retrieving a simulation by hash."""
    print(f"\n=== Testing Get Simulation from {suite.suite_name} ===")
    
    # Get the simulation
    sim = suite.get_simulation(sim_hash)
    print(f"Retrieved simulation: {sim.display_name} with hash {sim_hash}")
    
    # Verify we got a simulation
    assert sim is not None, "Failed to retrieve simulation"
    assert sim.display_name == expected_name, f"Retrieved wrong simulation. Expected {expected_name}, got {sim.display_name}"
    
    print(f"Get simulation test passed for {sim.display_name} in {suite.suite_name}.")
    return sim

def test_remove_simulation(suite, sim_hash):
    """Test removing a simulation from the suite."""
    print(f"\n=== Testing Remove Simulation from {suite.suite_name} ===")
    
    # Verify the simulation exists
    sim = suite.get_simulation(sim_hash)
    assert sim is not None, "Simulation not found before removal"
    sim_name = sim.display_name
    
    # Remove the simulation
    result = suite.remove_simulation(sim_hash)
    print(f"Removal result: {result}")
    
    # Verify it was removed
    assert result is True, "Removal returned False"
    assert suite.get_simulation(sim_hash) is None, "Simulation still exists after removal"
    
    print(f"Remove simulation test passed for {sim_name} in {suite.suite_name}.")
    return result

def test_multiple_suites():
    """Test creating and managing multiple simulation suites."""
    root_dir = "test_simulation_suites"
    clear_test_directory(root_dir)
    
    # Create Suite 1 with 3 simulations
    suite1 = test_create_suite("TestSuite1", root_dir)
    sim1_1 = test_add_simulation(suite1, "Simulation1-1", temperature=300.0)
    sim1_2 = test_add_simulation(suite1, "Simulation1-2", temperature=305.0)
    sim1_3 = test_add_simulation(suite1, "Simulation1-3", temperature=310.0)
    
    # Save all simulations
    test_save_simulation(suite1, sim1_1)
    test_save_simulation(suite1, sim1_2)
    test_save_simulation(suite1, sim1_3)
    
    # Verify we can list all simulations
    sims1 = test_list_simulations(suite1)
    assert len(sims1) == 3, f"Expected 3 simulations in Suite1, found {len(sims1)}"
    
    # Create Suite 2 with 2 simulations
    suite2 = test_create_suite("TestSuite2", root_dir)
    sim2_1 = test_add_simulation(suite2, "Simulation2-1", temperature=290.0)
    sim2_2 = test_add_simulation(suite2, "Simulation2-2", temperature=295.0)
    
    # Save all simulations
    test_save_simulation(suite2, sim2_1)
    test_save_simulation(suite2, sim2_2)
    
    # Verify we can list all simulations
    sims2 = test_list_simulations(suite2)
    assert len(sims2) == 2, f"Expected 2 simulations in Suite2, found {len(sims2)}"
    
    # Test retrieving simulations from each suite
    sim1_hash = sims1[0]["hash"]
    sim2_hash = sims2[0]["hash"]
    
    retrieved_sim1 = test_get_simulation(suite1, sim1_hash, sims1[0]["display_name"])
    retrieved_sim2 = test_get_simulation(suite2, sim2_hash, sims2[0]["display_name"])
    
    # Test removing a simulation from each suite
    test_remove_simulation(suite1, sim1_hash)
    test_remove_simulation(suite2, sim2_hash)
    
    # Verify the correct number of simulations after removal
    sims1_after = test_list_simulations(suite1)
    sims2_after = test_list_simulations(suite2)
    
    assert len(sims1_after) == 2, f"Expected 2 simulations in Suite1 after removal, found {len(sims1_after)}"
    assert len(sims2_after) == 1, f"Expected 1 simulation in Suite2 after removal, found {len(sims2_after)}"
    
    print("\n=== Multiple suites test passed! ===")
    return suite1, suite2

def test_suite_reloading():
    """Test that we can reload a suite from disk with all its simulations."""
    print("\n=== Testing Suite Reloading ===")
    
    # Create a fresh suite with simulations
    root_dir = "test_simulation_suites"
    suite_name = "ReloadSuite"
    
    # First create a suite and add simulations
    suite = test_create_suite(suite_name, root_dir)
    sim1 = test_add_simulation(suite, "ReloadSim1", temperature=300.0)
    sim2 = test_add_simulation(suite, "ReloadSim2", temperature=305.0)
    sim3 = test_add_simulation(suite, "ReloadSim3", temperature=310.0)
    
    # Save all simulations
    test_save_simulation(suite, sim1)
    test_save_simulation(suite, sim2)
    test_save_simulation(suite, sim3)
    
    # List original simulations
    orig_sims = test_list_simulations(suite)
    
    # Create a brand new suite instance with the same name and root
    print("\nRecreating suite to test loading from disk...")
    new_suite = SimulationSuite(suite_name, simulation_suites_root=root_dir)
    
    # List reloaded simulations
    reloaded_sims = test_list_simulations(new_suite)
    
    # Verify we have the same number of simulations
    assert len(orig_sims) == len(reloaded_sims), f"Expected {len(orig_sims)} simulations, found {len(reloaded_sims)}"
    
    # Compare simulation names
    orig_names = sorted([s["display_name"] for s in orig_sims])
    reloaded_names = sorted([s["display_name"] for s in reloaded_sims])
    
    assert orig_names == reloaded_names, f"Simulation names don't match. Original: {orig_names}, Reloaded: {reloaded_names}"
    
    print("Suite reloading test passed!")
    return new_suite

def test_run_all_unrun():
    """Test running all unrun simulations in a suite."""
    print("\n=== Testing Run All Unrun ===")
    
    # Create a fresh suite with simulations
    root_dir = "test_simulation_suites"
    suite_name = "RunAllSuite"
    
    # First create a suite and add simulations
    suite = test_create_suite(suite_name, root_dir)
    
    # Add simulations but don't run them
    sim1 = test_add_simulation(suite, "RunAllSim1", temperature=300.0)
    sim2 = test_add_simulation(suite, "RunAllSim2", temperature=305.0)
    sim3 = test_add_simulation(suite, "RunAllSim3", temperature=310.0)
    
    # Save all simulations (without running)
    test_save_simulation(suite, sim1)
    test_save_simulation(suite, sim2)
    test_save_simulation(suite, sim3)
    
    # Verify none of them are marked as run
    sims = suite.list_simulations()
    for sim in sims:
        assert not sim["has_run"], f"Simulation {sim['display_name']} should not be marked as run yet"
    
    # Run them all using run_all_unrun
    print("\nRunning all unrun simulations...")
    results = suite.run_all_unrun()
    
    # Verify all simulations ran successfully
    assert len(results) == 3, f"Expected 3 simulation results, got {len(results)}"
    for sim_hash, result in results.items():
        assert result is True, f"Simulation {sim_hash} failed to run: {result}"
    
    # Verify they're now all marked as run
    sims_after = suite.list_simulations()
    for sim in sims_after:
        assert sim["has_run"], f"Simulation {sim['display_name']} should be marked as run now"
    
    # Run again and verify no simulations are run
    print("\nRunning again (should find no unrun simulations)...")
    results_again = suite.run_all_unrun()
    assert len(results_again) == 0, f"Expected 0 simulation results on second run, got {len(results_again)}"
    
    # Create a brand new suite instance with the same name and root to test persistence
    print("\nRecreating suite to test persistence of has_run status...")
    new_suite = SimulationSuite(suite_name, simulation_suites_root=root_dir)
    
    # Verify all simulations still show as run
    reloaded_sims = new_suite.list_simulations()
    for sim in reloaded_sims:
        assert sim["has_run"], f"Reloaded simulation {sim['display_name']} lost its has_run status"
    
    print("Run all unrun test passed!")
    return new_suite

def run_all_tests():
    """Run all tests for the SimulationSuite class."""
    print("=== Starting SimulationSuite Tests ===")
    
    # Test basic suite operations
    print("\n--- Testing Basic Suite Operations ---")
    basic_tests_suite = test_create_suite("BasicTestSuite", "test_simulation_suites")
    sim = test_add_simulation(basic_tests_suite)
    path = test_save_simulation(basic_tests_suite, sim)
    sims = test_list_simulations(basic_tests_suite)
    sim_hash = sims[0]["hash"]
    retrieved_sim = test_get_simulation(basic_tests_suite, sim_hash, sims[0]["display_name"])
    
    # Test multiple suites
    print("\n--- Testing Multiple Suites ---")
    suite1, suite2 = test_multiple_suites()
    
    # Test suite reloading
    print("\n--- Testing Suite Reloading ---")
    reloaded_suite = test_suite_reloading()
    
    # Test running all unrun simulations
    print("\n--- Testing Run All Unrun ---")
    new_suite = test_run_all_unrun()
    
    print("\n=== All SimulationSuite tests passed! ===")

if __name__ == "__main__":
    run_all_tests() 