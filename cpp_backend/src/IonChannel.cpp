#include "IonChannel.h"
#include "IonSpecies.h"
#include <cmath>
#include <stdexcept>

// Constants matching the Python implementation
constexpr double IDEAL_GAS_CONSTANT = 8.31446261815324;
constexpr double FARADAY_CONSTANT = 96485.0;

IonChannel::IonChannel(
    double conductance,
    const std::string& channelType,
    const std::string& dependenceType,
    double voltageMultiplier,
    double nernstMultiplier,
    double voltageShift,
    double fluxMultiplier,
    const std::string& allowedPrimaryIon,
    const std::string& allowedSecondaryIon,
    int primaryExponent,
    int secondaryExponent,
    double customNernstConstant,
    bool useFreeHydrogen,
    double voltageExponent,
    double halfActVoltage,
    double pHExponent,
    double halfActPH,
    double timeExponent,
    double halfActTime,
    const std::string& displayName
) : conductance_(conductance),
    channelType_(channelType),
    dependenceType_(dependenceType),
    voltageMultiplier_(voltageMultiplier),
    nernstMultiplier_(nernstMultiplier),
    voltageShift_(voltageShift),
    fluxMultiplier_(fluxMultiplier),
    allowedPrimaryIon_(allowedPrimaryIon),
    allowedSecondaryIon_(allowedSecondaryIon),
    primaryExponent_(primaryExponent),
    secondaryExponent_(secondaryExponent),
    customNernstConstant_(customNernstConstant),
    useFreeHydrogen_(useFreeHydrogen),
    voltageExponent_(voltageExponent),
    halfActVoltage_(halfActVoltage),
    pHExponent_(pHExponent),
    halfActPH_(halfActPH),
    timeExponent_(timeExponent),
    halfActTime_(halfActTime),
    displayName_(displayName.empty() ? "UnnamedChannel" : displayName),
    flux_(0.0),
    nernstPotential_(0.0),
    pHDependence_(1.0),
    voltageDependence_(1.0),
    timeDependence_(1.0),
    primarySpecies_(nullptr),
    secondarySpecies_(nullptr) {
}

void IonChannel::connectSpecies(std::shared_ptr<IonSpecies> primarySpecies, 
                               std::shared_ptr<IonSpecies> secondarySpecies) {
    // Validate species
    if (!primarySpecies) {
        throw std::invalid_argument("Primary ion species cannot be null");
    }
    
    if (allowedSecondaryIon_ != "" && !secondarySpecies) {
        throw std::invalid_argument("Secondary ion species required for two-ion channel");
    }
    
    // Store species references
    primarySpecies_ = primarySpecies;
    secondarySpecies_ = secondarySpecies;
}

double IonChannel::computePHDependence(double pH) {
    // If required parameters are not set, return default value
    if (!pHExponent_ || !halfActPH_) {
        return 1.0;
    }
    
    // Calculate pH dependence using the same logistic function as in Python
    double logisticTerm = 1.0 / (1.0 + std::exp(pHExponent_ * (pH - halfActPH_)));
    
    // Store for tracking
    pHDependence_ = logisticTerm;
    
    return logisticTerm;
}

double IonChannel::computeVoltageDependence(double voltage) {
    // If required parameters are not set, return default value
    if (!voltageExponent_ || !halfActVoltage_) {
        return 1.0;
    }
    
    // Calculate voltage dependence using the same logistic function as in Python
    double effectiveVoltage = voltage * voltageMultiplier_ - voltageShift_;
    double logisticTerm = 1.0 / (1.0 + std::exp(voltageExponent_ * (effectiveVoltage - halfActVoltage_)));
    
    // Store for tracking
    voltageDependence_ = logisticTerm;
    
    return logisticTerm;
}

double IonChannel::computeTimeDependence(double time) {
    // If required parameters are not set, return default value
    if (!timeExponent_ || !halfActTime_) {
        return 1.0;
    }
    
    // Calculate time dependence using the same logistic function as in Python
    double logisticTerm = 1.0 / (1.0 + std::exp(timeExponent_ * (time - halfActTime_)));
    
    // Store for tracking
    timeDependence_ = logisticTerm;
    
    return logisticTerm;
}

double IonChannel::computeLogTerm(const FluxCalculationParameters& params) {
    if (!primarySpecies_) {
        throw std::runtime_error("Cannot compute log term: primary species not connected");
    }
    
    // Get concentrations from species
    double vesicleConc = primarySpecies_->getVesicleConc();
    double exteriorConc = primarySpecies_->getExteriorConc();
    
    // Handle hydrogen ion special case
    if (useFreeHydrogen_ && primarySpecies_->getDisplayName() == "h") {
        vesicleConc = params.vesicleHydrogenFree;
        exteriorConc = params.exteriorHydrogenFree;
    }
    
    // Handle two-ion channels (like NHE where flux depends on both Na+ and H+)
    if (secondarySpecies_) {
        double secondaryVesicleConc = secondarySpecies_->getVesicleConc();
        double secondaryExteriorConc = secondarySpecies_->getExteriorConc();
        
        // Handle hydrogen ion special case for secondary species
        if (useFreeHydrogen_ && secondarySpecies_->getDisplayName() == "h") {
            secondaryVesicleConc = params.vesicleHydrogenFree;
            secondaryExteriorConc = params.exteriorHydrogenFree;
        }
        
        // FIXED: Match Python implementation order of operations
        // Python uses exterior/vesicle for primary and vesicle/exterior for secondary
        double primaryTerm = std::pow(exteriorConc / vesicleConc, primaryExponent_);
        double secondaryTerm = std::pow(secondaryVesicleConc / secondaryExteriorConc, secondaryExponent_);
        
        double logTerm = primaryTerm * secondaryTerm;
        
        if (logTerm <= 0) {
            return 0.0; // Avoid log of zero or negative
        }
        
        return std::log(logTerm);
    } 
    else {
        // Single ion channel
        // FIXED: Match Python implementation for single ion channels
        if (exteriorConc <= 0 || vesicleConc <= 0) {
            return 0.0; // Avoid log of zero or negative
        }
        
        // Use exterior/vesicle to match Python
        return std::log(std::pow(exteriorConc / vesicleConc, primaryExponent_));
    }
}

double IonChannel::computeNernstPotential(const FluxCalculationParameters& params) {
    // Get voltage from params
    double voltage = params.voltage;
    
    // Use custom Nernst constant if provided, otherwise use the one from params
    double nernstConstant;
    if (customNernstConstant_ != 0.0) {
        nernstConstant = customNernstConstant_;
    } else {
        nernstConstant = params.nernstConstant;
    }
    
    // Calculate log term
    double logTerm = computeLogTerm(params);
    
    // FIXED: Match Python implementation by including voltage and shifts
    // Python: return (self.voltage_multiplier * voltage + (self.nernst_multiplier * nernst_constant * log_term) - self.voltage_shift)
    double potential = voltageMultiplier_ * voltage + 
                      (nernstMultiplier_ * nernstConstant * logTerm) - 
                      voltageShift_;
    
    // Store for tracking
    nernstPotential_ = potential;
    
    return potential;
}

double IonChannel::computeFlux(const FluxCalculationParameters& params) {
    // Skip flux computation if conductance is zero
    if (conductance_ == 0.0) {
        return 0.0;
    }
    
    // Calculate individual dependence terms based on dependence type
    double pHDependence = 1.0;
    double voltageDependence = 1.0;
    double timeDependence = 1.0;
    
    if (dependenceType_ == "voltage") {
        voltageDependence = computeVoltageDependence(params.voltage);
    } else if (dependenceType_ == "pH") {
        pHDependence = computePHDependence(params.pH);
    } else if (dependenceType_ == "time") {
        timeDependence = computeTimeDependence(params.time);
    } else if (dependenceType_ == "voltage_and_pH") {
        voltageDependence = computeVoltageDependence(params.voltage);
        pHDependence = computePHDependence(params.pH);
    }
    
    // Compute the Nernst potential
    double nernstPotential = computeNernstPotential(params);
    
    // FIXED: Match Python implementation flux calculation
    // Python: flux = self.flux_multiplier * self.nernst_potential * self.conductance * area
    double area = params.area;
    double flux = fluxMultiplier_ * nernstPotential * conductance_ * area;
    
    // Apply dependencies
    flux *= pHDependence * voltageDependence * timeDependence;
    
    // Update trackable fields
    flux_ = flux;
    
    return flux;
} 