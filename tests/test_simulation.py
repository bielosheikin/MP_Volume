import unittest
from src.backend.simulation import Simulation
from src.backend.ion_channels import IonChannel
from src.backend.ion_species import IonSpecies
from src.backend.ion_and_channels_link import IonChannelsLink
from src.backend.vesicle import Vesicle
from src.backend.exterior import Exterior

class TestSimulation(unittest.TestCase):
    def setUp(self):
        # Set up default parameters for the tests
        self.vesicle_params = {
            "init_radius": 1.3e-6,
            "init_voltage": 0.04,
            "init_pH": 7.4,
        }
        self.exterior_params = {
            "pH": 7.2,
        }
        self.simulation_params = {
            "time_step": 0.001,
            "total_time": 100.0,
        }

    def test_simulation_initialization(self):
        # Test initialization of the Simulation class
        simulation = Simulation(
            vesicle_params=self.vesicle_params,
            exterior_params=self.exterior_params
        )
        
        # Check that the simulation is initialized with the correct parameters
        self.assertEqual(simulation.vesicle_params, self.vesicle_params)
        self.assertEqual(simulation.exterior_params, self.exterior_params)
        self.assertEqual(simulation.time_step, self.simulation_params["time_step"])
        self.assertEqual(simulation.total_time, self.simulation_params["total_time"])

    def test_simulation_run(self):
        # Test running the simulation
        simulation = Simulation(
            vesicle_params=self.vesicle_params,
            exterior_params=self.exterior_params
        )
        
        # Run the simulation
        histories = simulation.run()
        
        # Check that histories are returned
        self.assertIsNotNone(histories)

    def test_zero_time_step(self):
        # Test with zero time_step
        with self.assertRaises(ValueError):
            Simulation(
                vesicle_params=self.vesicle_params,
                exterior_params=self.exterior_params,
                time_step=0
            )

    def test_negative_total_time(self):
        # Test with negative total_time
        with self.assertRaises(ValueError):
            Simulation(
                vesicle_params=self.vesicle_params,
                exterior_params=self.exterior_params,
                total_time=-100.0
            )

    def test_extreme_vesicle_params(self):
        # Test with extreme vesicle parameters
        extreme_vesicle_params = {
            "init_radius": 1e-12,  # Extremely small radius
            "init_voltage": 1e6,  # Extremely high voltage
            "init_pH": 14.0,     # Extremely high pH
        }
        simulation = Simulation(
            vesicle_params=extreme_vesicle_params,
            exterior_params=self.exterior_params
        )
        self.assertEqual(simulation.vesicle_params, extreme_vesicle_params)

    def test_missing_vesicle_params(self):
        # Test with missing vesicle parameters
        simulation = Simulation(
            exterior_params=None
        )
        
        # Check that default vesicle parameters are used
        default_vesicle = Vesicle()
        self.assertEqual(simulation.vesicle_params["init_radius"], default_vesicle.init_radius)
        self.assertEqual(simulation.vesicle_params["init_voltage"], default_vesicle.init_voltage)
        self.assertEqual(simulation.vesicle_params["init_pH"], default_vesicle.init_pH)

        # Check that default exterior parameters are used
        default_exterior = Exterior()
        self.assertEqual(simulation.exterior_params["pH"], default_exterior.pH)

    def test_invalid_type_for_params(self):
        # Test with invalid type for parameters
        with self.assertRaises(TypeError):
            Simulation(
                vesicle_params="invalid_type",
                exterior_params=self.exterior_params
            )

    def test_missing_exterior_params(self):
        # Test with missing exterior parameters
        simulation = Simulation(
            vesicle_params=None
        )
        
        # Check that default vesicle parameters are used
        default_vesicle = Vesicle()
        self.assertEqual(simulation.vesicle_params["init_radius"], default_vesicle.init_radius)
        self.assertEqual(simulation.vesicle_params["init_voltage"], default_vesicle.init_voltage)
        self.assertEqual(simulation.vesicle_params["init_pH"], default_vesicle.init_pH)

        # Check that default exterior parameters are used
        default_exterior = Exterior()
        self.assertEqual(simulation.exterior_params["pH"], default_exterior.pH)

if __name__ == '__main__':
    unittest.main() 