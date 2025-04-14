#include <iostream>
#include <fstream>
#include <string>
#include <nlohmann/json.hpp>
#include <stdexcept>

#include "Simulation.h"

using json = nlohmann::json;

int main(int argc, char* argv[]) {
    try {
        // Check command line arguments
        if (argc != 3) {
            std::cerr << "Usage: " << argv[0] << " <config_file.json> <output_file.json>" << std::endl;
            return 1;
        }
        
        std::string configFile = argv[1];
        std::string outputFile = argv[2];
        
        // Load the config JSON from the file
        std::ifstream configInput(configFile);
        if (!configInput.is_open()) {
            std::cerr << "ERROR: Could not open config file: " << configFile << std::endl;
            return 1;
        }
        
        std::string configJson((std::istreambuf_iterator<char>(configInput)),
                              std::istreambuf_iterator<char>());
        configInput.close();
        
        // Create and configure the simulation
        Simulation simulation;
        simulation.loadFromJson(configJson);
        
        // Run the simulation with progress reporting
        simulation.run([](int progress) {
            std::cout << "PROGRESS:" << progress << std::endl;
        });
        
        // Get the results as JSON
        json results = simulation.getHistoriesJson();
        
        // Write the results to the output file
        std::ofstream outputStream(outputFile);
        if (!outputStream.is_open()) {
            std::cerr << "ERROR: Could not open output file for writing: " << outputFile << std::endl;
            return 1;
        }
        
        outputStream << results.dump(4);  // Pretty-print with 4-space indent
        outputStream.close();
        
        std::cout << "COMPLETED" << std::endl;
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "ERROR: " << e.what() << std::endl;
        return 1;
    } catch (...) {
        std::cerr << "ERROR: Unknown exception occurred" << std::endl;
        return 1;
    }
} 