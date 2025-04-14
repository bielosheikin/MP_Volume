#pragma once

#include <string>
#include <memory>
#include <optional>
#include <unordered_map>
#include "FluxCalculationParameters.h"
#include "HistoriesStorage.h"  // For Trackable interface

// Forward declaration to avoid circular dependency
class IonSpecies;

class IonChannel : public Trackable {
public:
    IonChannel(
        double conductance,
        const std::string& channelType,
        const std::string& dependenceType,
        double voltageMultiplier,
        double nernstMultiplier,
        double voltageShift,
        double fluxMultiplier,
        const std::string& allowedPrimaryIon,
        const std::string& allowedSecondaryIon = "",
        int primaryExponent = 1,
        int secondaryExponent = 1,
        double customNernstConstant = 0.0,
        bool useFreeHydrogen = false,
        double voltageExponent = 0.0,
        double halfActVoltage = 0.0,
        double pHExponent = 0.0,
        double halfActPH = 0.0,
        double timeExponent = 0.0,
        double halfActTime = 0.0,
        const std::string& displayName = ""
    );
    
    // Methods for computing dependencies
    double computePHDependence(double pH);
    double computeVoltageDependence(double voltage);
    double computeTimeDependence(double time);
    
    // Connect species to this channel
    void connectSpecies(std::shared_ptr<IonSpecies> primarySpecies,
                       std::shared_ptr<IonSpecies> secondarySpecies = nullptr);
    
    // Compute Nernst potential and flux
    double computeLogTerm(const FluxCalculationParameters& params);
    double computeNernstPotential(const FluxCalculationParameters& params);
    double computeFlux(const FluxCalculationParameters& params);
    
    // Getters
    std::string getDisplayName() const override { return displayName_; }
    const std::string& getAllowedPrimaryIon() const { return allowedPrimaryIon_; }
    const std::string& getAllowedSecondaryIon() const { return allowedSecondaryIon_; }
    double getFlux() const { return flux_; }
    double getNernstPotential() const { return nernstPotential_; }
    double getPHDependence() const { return pHDependence_; }
    double getVoltageDependence() const { return voltageDependence_; }
    double getTimeDependence() const { return timeDependence_; }
    
    // Implement Trackable interface
    std::unordered_map<std::string, double> getCurrentState() const override {
        return {
            {"flux", flux_},
            {"nernst_potential", nernstPotential_},
            {"pH_dependence", pHDependence_},
            {"voltage_dependence", voltageDependence_},
            {"time_dependence", timeDependence_}
        };
    }
    
private:
    // Configuration properties
    double conductance_;
    std::string channelType_;
    std::string dependenceType_;
    double voltageMultiplier_;
    double nernstMultiplier_;
    double voltageShift_;
    double fluxMultiplier_;
    std::string allowedPrimaryIon_;
    std::string allowedSecondaryIon_;
    int primaryExponent_;
    int secondaryExponent_;
    double customNernstConstant_;
    bool useFreeHydrogen_;
    
    // Dependency parameters
    double voltageExponent_;
    double halfActVoltage_;
    double pHExponent_;
    double halfActPH_;
    double timeExponent_;
    double halfActTime_;
    
    // Display name
    std::string displayName_;
    
    // Connected species
    std::shared_ptr<IonSpecies> primarySpecies_;
    std::shared_ptr<IonSpecies> secondarySpecies_;
    
    // Tracked values (for history)
    double flux_;
    double nernstPotential_;
    double pHDependence_;
    double voltageDependence_;
    double timeDependence_;
}; 