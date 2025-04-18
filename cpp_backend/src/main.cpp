#include <iostream>
#include <fstream>
#include <string>
#include <nlohmann/json.hpp>
#include <stdexcept>
#include <chrono>
#include <iomanip>

#include "Simulation.h"

using json = nlohmann::json;

// Global flag to control output verbosity
bool g_quietMode = false;

// Override standard cout to respect quiet mode
#define DEBUG_PRINT(x) if (!g_quietMode) { std::cout << x; }

int main(int argc, char* argv[]) {
    try {
        bool performanceTiming = false;
        
        // Check command line arguments
        if (argc < 2) {
            std::cerr << "Usage: " << argv[0] << " <config_file.json> [<output_file.json>] [--disable_logging] [-timing]" << std::endl;
            return 1;
        }
        
        std::string configFile = argv[1];
        std::string outputFile = (argc > 2 && argv[2][0] != '-') ? argv[2] : "output.json";
        
        // Process optional arguments
        for (int i = 2; i < argc; i++) {
            std::string arg = argv[i];
            if (arg == "-quiet" || arg == "--disable_logging") {
                g_quietMode = true;
                DEBUG_PRINT("Quiet mode enabled - suppressing debug output\n");
            } else if (arg == "-timing") {
                performanceTiming = true;
                DEBUG_PRINT("Performance timing enabled\n");
            }
        }
        
        // Setup timing variables
        std::chrono::time_point<std::chrono::high_resolution_clock> startTime, endTime, simStartTime, simEndTime;
        
        if (performanceTiming) {
            startTime = std::chrono::high_resolution_clock::now();
        }
        
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
        
        if (performanceTiming) {
            simStartTime = std::chrono::high_resolution_clock::now();
        }
        
        // Run the simulation with progress reporting only if not in quiet mode
        simulation.run([](int progress) {
            DEBUG_PRINT("PROGRESS:" << progress << std::endl);
        });
        
        if (performanceTiming) {
            simEndTime = std::chrono::high_resolution_clock::now();
        }
        
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
        
        if (performanceTiming) {
            endTime = std::chrono::high_resolution_clock::now();
            
            // Calculate durations
            auto totalDuration = std::chrono::duration_cast<std::chrono::milliseconds>(endTime - startTime).count();
            auto simDuration = std::chrono::duration_cast<std::chrono::milliseconds>(simEndTime - simStartTime).count();
            
            // Print timings
            std::cout << "\n==== PERFORMANCE RESULTS ====" << std::endl;
            std::cout << "Total execution time: " << totalDuration / 1000.0 << " seconds" << std::endl;
            std::cout << "Simulation running time: " << simDuration / 1000.0 << " seconds" << std::endl;
            
            // Calculate iterations per second
            double timeStep = simulation.getTimeStep();
            double totalTime = simulation.getTotalTime();
            long numIterations = static_cast<long>(totalTime / timeStep);
            double iterationsPerSecond = numIterations / (simDuration / 1000.0);
            
            std::cout << "Number of iterations: " << numIterations << std::endl;
            std::cout << "Iterations per second: " << iterationsPerSecond << std::endl;
        }
        
        DEBUG_PRINT("COMPLETED" << std::endl);
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "ERROR: " << e.what() << std::endl;
        return 1;
    } catch (...) {
        std::cerr << "ERROR: Unknown exception occurred" << std::endl;
        return 1;
    }
} 