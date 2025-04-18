#pragma once

#include <string>
#include <unordered_map>
#include <memory>
#include <vector>
#include <nlohmann/json.hpp>

#include "FluxCalculationParameters.h"

// Forward declarations
class Vesicle;
class Exterior;
class IonSpecies;
class IonChannel;
class HistoriesStorage;

class Simulation {
public:
    Simulation(
        double timeStep = 0.001,
        double totalTime = 100.0,
        const std::string& displayName = "simulation"
    );
    
    // Configuration from JSON
    void loadFromJson(const std::string& jsonConfig);
    
    // Diagnostic methods
    void printDetailedDiagnostics();
    void printFinalValues();
    void verifyChannelConnections();
    
    // Main simulation methods
    virtual void runOneIteration();
    virtual void run(std::function<void(int)> progressCallback = nullptr);
    
    // Initialization methods
    void setIonAmounts();
    
    // Update methods for physical properties
    void updateVolume();
    void updateArea();
    void updateCharge();
    void updateCapacitance();
    void updateVoltage();
    void updateBuffer();
    void updatePH();
    void updateIonAmounts(const std::vector<double>& fluxes);
    void updateVesicleConcentrations();
    void updateSimulationState();
    
    // Helper methods
    FluxCalculationParameters getFluxCalculationParameters();
    double getUnaccountedIonAmount();
    
    // Getters
    double getTimeStep() const { return timeStep_; }
    double getTotalTime() const { return totalTime_; }
    double getTime() const { return time_; }
    const std::string& getDisplayName() const { return displayName_; }
    nlohmann::json getHistoriesJson() const;
    
protected:
    // Configuration properties
    double timeStep_;
    double totalTime_;
    double time_;
    double temperature_;
    double initBufferCapacity_;
    double bufferCapacity_;
    std::string displayName_;
    
    // Simulation state
    double unaccountedIonAmount_; // Store unaccounted ion amount like Python
    bool ionAmountsUpdated_; // Track if ion amounts have been updated
    
    // Physical objects
    std::shared_ptr<Vesicle> vesicle_;
    std::shared_ptr<Exterior> exterior_;
    std::unordered_map<std::string, std::shared_ptr<IonSpecies>> species_;
    std::unordered_map<std::string, std::shared_ptr<IonChannel>> channels_;
    
    // Ion channel links (mapping from species to channels)
    std::unordered_map<std::string, std::vector<std::pair<std::string, std::string>>> ionChannelLinks_;
    
    // Histories storage
    std::shared_ptr<HistoriesStorage> histories_;
}; 