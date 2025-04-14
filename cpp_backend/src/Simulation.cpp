#include "Simulation.h"
#include "Vesicle.h"
#include "Exterior.h"
#include "IonSpecies.h"
#include "IonChannel.h"
#include "HistoriesStorage.h"
#include <cmath>
#include <iostream>
#include <stdexcept>

// Define M_PI if not already defined (Windows MSVC doesn't define it by default)
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// Constants matching the Python implementation
constexpr double IDEAL_GAS_CONSTANT = 8.31446261815324;
constexpr double FARADAY_CONSTANT = 96485.0;
constexpr double VOLUME_TO_AREA_CONSTANT = 4.83598;  // Pre-computed value of std::pow(36.0 * M_PI, 1.0/3.0)

Simulation::Simulation(
    double timeStep,
    double totalTime,
    const std::string& displayName
) : timeStep_(timeStep),
    totalTime_(totalTime),
    time_(0.0),
    temperature_(2578.5871 / IDEAL_GAS_CONSTANT),
    initBufferCapacity_(5e-4),
    bufferCapacity_(initBufferCapacity_),
    displayName_(displayName) {
    
    // Initialize storage for histories
    histories_ = std::make_shared<HistoriesStorage>();
}

void Simulation::loadFromJson(const std::string& jsonConfig) {
    try {
        nlohmann::json config = nlohmann::json::parse(jsonConfig);
        
        // Validate required parameters
        std::vector<std::string> requiredParams = {"time_step", "total_time"};
        for (const auto& param : requiredParams) {
            if (!config.contains(param)) {
                throw std::runtime_error("Missing required parameter: " + param);
            }
        }
        
        // Load basic simulation parameters with validation
        timeStep_ = config["time_step"];
        if (timeStep_ <= 0) {
            throw std::runtime_error("time_step must be positive");
        }
        
        totalTime_ = config["total_time"];
        if (totalTime_ <= 0) {
            throw std::runtime_error("total_time must be positive");
        }
        
        if (config.contains("display_name")) {
            displayName_ = config["display_name"];
        }
        
        if (config.contains("temperature")) {
            temperature_ = config["temperature"];
            if (temperature_ <= 0) {
                throw std::runtime_error("temperature must be positive");
            }
        }
        
        if (config.contains("init_buffer_capacity")) {
            initBufferCapacity_ = config["init_buffer_capacity"];
            if (initBufferCapacity_ < 0) {
                throw std::runtime_error("init_buffer_capacity cannot be negative");
            }
        }
        bufferCapacity_ = initBufferCapacity_;
        
        // Create vesicle
        if (config.contains("vesicle_params")) {
            auto vp = config["vesicle_params"];
            vesicle_ = std::make_shared<Vesicle>(
                vp.value("init_radius", 1.3e-6),
                vp.value("init_voltage", 4e-2),
                vp.value("init_pH", 7.4),
                vp.value("specific_capacitance", 1e-2),
                vp.value("display_name", "Vesicle")
            );
        } else {
            vesicle_ = std::make_shared<Vesicle>();
        }
        
        // Create exterior
        if (config.contains("exterior_params")) {
            auto ep = config["exterior_params"];
            exterior_ = std::make_shared<Exterior>(
                ep.value("pH", 7.2),
                ep.value("display_name", "Exterior")
            );
        } else {
            exterior_ = std::make_shared<Exterior>();
        }
        
        // Create ion species
        if (config.contains("species")) {
            for (const auto& [name, speciesData] : config["species"].items()) {
                species_[name] = std::make_shared<IonSpecies>(
                    name,
                    speciesData.value("init_vesicle_conc", 0.0),
                    speciesData.value("exterior_conc", 0.0),
                    speciesData.value("elementary_charge", 0.0)
                );
            }
        }
        
        // Create channels
        if (config.contains("channels")) {
            for (const auto& [name, channelData] : config["channels"].items()) {
                channels_[name] = std::make_shared<IonChannel>(
                    channelData.value("conductance", 0.0),
                    channelData.value("channel_type", ""),
                    channelData.value("dependence_type", ""),
                    channelData.value("voltage_multiplier", 1.0),
                    channelData.value("nernst_multiplier", 1.0),
                    channelData.value("voltage_shift", 0.0),
                    channelData.value("flux_multiplier", 1.0),
                    channelData.value("allowed_primary_ion", ""),
                    channelData.value("allowed_secondary_ion", ""),
                    channelData.value("primary_exponent", 1),
                    channelData.value("secondary_exponent", 1),
                    channelData.value("custom_nernst_constant", 0.0),
                    channelData.value("use_free_hydrogen", false),
                    channelData.value("voltage_exponent", 0.0),
                    channelData.value("half_act_voltage", 0.0),
                    channelData.value("pH_exponent", 0.0),
                    channelData.value("half_act_pH", 0.0),
                    channelData.value("time_exponent", 0.0),
                    channelData.value("half_act_time", 0.0),
                    name  // Use channel name as display_name
                );
            }
        }
        
        // Process ion channel links
        if (config.contains("ion_channel_links")) {
            for (const auto& [speciesName, channelLinks] : config["ion_channel_links"].items()) {
                for (const auto& link : channelLinks) {
                    std::string channelName = link[0];
                    std::string secondarySpeciesName = link.size() > 1 && !link[1].is_null() ? link[1].get<std::string>() : "";
                    
                    // Store the link
                    ionChannelLinks_[speciesName].push_back(std::make_pair(channelName, secondarySpeciesName));
                    
                    // Connect the species to the channel
                    auto primarySpecies = species_.find(speciesName);
                    auto channel = channels_.find(channelName);
                    
                    if (primarySpecies != species_.end() && channel != channels_.end()) {
                        if (!secondarySpeciesName.empty()) {
                            auto secondarySpecies = species_.find(secondarySpeciesName);
                            if (secondarySpecies != species_.end()) {
                                primarySpecies->second->connectChannel(channel->second, secondarySpecies->second);
                            }
                        } else {
                            primarySpecies->second->connectChannel(channel->second);
                        }
                    }
                }
            }
        }
        
        // Register objects for history tracking
        histories_->registerObject(vesicle_);
        histories_->registerObject(exterior_);
        
        for (const auto& [name, species] : species_) {
            histories_->registerObject(species);
        }
        
        for (const auto& [name, channel] : channels_) {
            histories_->registerObject(channel);
        }
        
        // Initialize the simulation
        setIonAmounts();
        
    } catch (const std::exception& e) {
        throw std::runtime_error(std::string("Error loading simulation configuration: ") + e.what());
    }
}

void Simulation::runOneIteration() {
    // Get the current flux calculation parameters
    FluxCalculationParameters params = getFluxCalculationParameters();
    
    // Compute the fluxes for each ion species
    std::unordered_map<std::string, double> fluxes;
    for (const auto& [speciesName, species] : species_) {
        fluxes[speciesName] = species->computeTotalFlux(params);
    }
    
    // Update the ion amounts based on the computed fluxes
    updateIonAmounts(fluxes);
    
    // Update the vesicle concentrations
    updateVesicleConcentrations();
    
    // Update physical properties
    updateSimulationState();
    
    // Update histories
    histories_->updateHistories();
    
    // Update simulation time
    time_ += timeStep_;
}

void Simulation::run(std::function<void(int)> progressCallback) {
    // Calculate the number of iterations
    int iterNum = static_cast<int>(totalTime_ / timeStep_);
    
    // Run all iterations
    for (int i = 0; i < iterNum; i++) {
        // Run one iteration
        runOneIteration();
        
        // Report progress
        if (progressCallback && (i % 1000 == 0 || i == iterNum - 1)) {
            int progress = static_cast<int>((static_cast<double>(i + 1) / iterNum) * 100);
            progressCallback(progress);
        }
    }
}

FluxCalculationParameters Simulation::getFluxCalculationParameters() {
    FluxCalculationParameters params;
    
    // Set the current parameters
    params.voltage = vesicle_->getVoltage();
    params.pH = vesicle_->getPH();
    params.time = time_;
    params.area = vesicle_->getArea();
    
    // Calculate the Nernst constant
    params.nernstConstant = IDEAL_GAS_CONSTANT * temperature_ / FARADAY_CONSTANT;
    
    // Calculate free hydrogen concentrations
    // Free H+ concentration = total H+ concentration * fraction of free H+
    // fraction of free H+ = 1 / (1 + buffer capacity / (10^-pH))
    double vesicleHPlusTotalConc = std::pow(10, -vesicle_->getPH());
    double exteriorHPlusTotalConc = std::pow(10, -exterior_->getPH());
    
    double vesicleHPlusFreeConc = vesicleHPlusTotalConc / (1.0 + bufferCapacity_ / vesicleHPlusTotalConc);
    double exteriorHPlusFreeConc = exteriorHPlusTotalConc; // Assuming no buffer in exterior
    
    params.vesicleHydrogenFree = vesicleHPlusFreeConc;
    params.exteriorHydrogenFree = exteriorHPlusFreeConc;
    
    return params;
}

void Simulation::setIonAmounts() {
    // Calculate volume in liters
    double volumeInLiters = vesicle_->getVolume();
    
    // Set ion amounts based on concentrations and volume
    for (const auto& [speciesName, species] : species_) {
        double concentration = species->getVesicleConc();  // moles/liter
        double amount = concentration * volumeInLiters;    // moles
        species->setVesicleAmount(amount);
    }
}

void Simulation::updateIonAmounts(const std::unordered_map<std::string, double>& fluxes) {
    // Update ion amounts based on fluxes
    // flux units: moles/second
    for (const auto& [speciesName, flux] : fluxes) {
        auto species = species_.find(speciesName);
        if (species != species_.end()) {
            double currentAmount = species->second->getVesicleAmount();
            double newAmount = currentAmount + flux * timeStep_;
            species->second->setVesicleAmount(newAmount);
        }
    }
}

void Simulation::updateVesicleConcentrations() {
    // Calculate volume in liters
    double volumeInLiters = vesicle_->getVolume();
    
    // Update concentrations based on amounts and volume
    for (const auto& [speciesName, species] : species_) {
        double amount = species->getVesicleAmount();       // moles
        double concentration = amount / volumeInLiters;    // moles/liter
        species->setVesicleConc(concentration);
    }
}

double Simulation::getUnaccountedIonAmount() {
    // Calculate total ionic charge inside the vesicle (moles)
    double totalIonicCharge = 0.0;
    for (const auto& [speciesName, species] : species_) {
        double amount = species->getVesicleAmount();           // moles
        double charge = species->getElementaryCharge();        // elementary charge
        totalIonicCharge += amount * charge;                   // moles of charge
    }
    
    // Calculate charge from capacitor (Coulombs)
    double capacitorCharge = vesicle_->getCharge();            // Coulombs
    
    // Convert capacitor charge to moles of charge
    double capacitorChargeInMoles = capacitorCharge / FARADAY_CONSTANT;  // moles
    
    // Calculate unaccounted charge (should be close to zero)
    double unaccountedCharge = totalIonicCharge + capacitorChargeInMoles;
    
    return unaccountedCharge;
}

void Simulation::updateVolume() {
    // Calculate new volume based on osmotic pressure effects (matching Python implementation)
    if (vesicle_ && !species_.empty()) {
        double sumCurrentConc = 0.0;
        double sumInitConc = 0.0;
        double unaccountedIonAmount = getUnaccountedIonAmount();
        
        // Sum concentrations excluding hydrogen ions
        for (const auto& [name, species] : species_) {
            if (name != "h") {
                sumCurrentConc += species->getVesicleConc();
                sumInitConc += species->getVesicleConc(); // We're using the initial concentration value
            }
        }
        
        // Add unaccounted ion amount to both sums
        sumCurrentConc += std::abs(unaccountedIonAmount);
        sumInitConc += std::abs(unaccountedIonAmount);
        
        // Calculate new volume based on concentration ratio
        if (sumInitConc > 0) {
            double newVolume = vesicle_->getInitVolume() * (sumCurrentConc / sumInitConc);
            vesicle_->updateVolume(newVolume);
        }
    }
}

void Simulation::updateArea() {
    vesicle_->updateArea();
}

void Simulation::updateCharge() {
    // Calculate total ionic charge inside the vesicle (moles)
    double totalIonicCharge = 0.0;
    for (const auto& [speciesName, species] : species_) {
        double amount = species->getVesicleAmount();           // moles
        double charge = species->getElementaryCharge();        // elementary charge
        totalIonicCharge += amount * charge;                   // moles of charge
    }
    
    // Convert to Coulombs
    double ionicChargeInCoulombs = totalIonicCharge * FARADAY_CONSTANT;
    
    // Update vesicle charge (negative of ionic charge for charge neutrality)
    vesicle_->updateCharge(-ionicChargeInCoulombs);
}

void Simulation::updateCapacitance() {
    vesicle_->updateCapacitance();
}

void Simulation::updateVoltage() {
    vesicle_->updateVoltage();
}

void Simulation::updateBuffer() {
    // For simplicity, buffer capacity is kept constant
    // In a more complex implementation, this would update buffer capacity based on pH
    bufferCapacity_ = initBufferCapacity_;
}

void Simulation::updatePH() {
    // Find hydrogen ion species
    auto hydrogen = species_.find("h");
    if (hydrogen != species_.end()) {
        // Get hydrogen concentration
        double hConc = hydrogen->second->getVesicleConc();
        
        // Convert to pH (pH = -log10([H+]))
        double newPH = -std::log10(hConc);
        
        // Update vesicle pH
        vesicle_->updatePH(newPH);
    }
}

void Simulation::updateSimulationState() {
    // Update physical properties in the correct order
    updateVolume();
    updateArea();
    updateCapacitance();
    updateCharge();
    updateVoltage();
    updateBuffer();
    updatePH();
}

nlohmann::json Simulation::getHistoriesJson() const {
    // Add simulation time to histories
    auto result = histories_->toJson();
    
    // Calculate number of data points
    int numPoints = 0;
    for (const auto& [key, values] : result.items()) {
        numPoints = values.size();
        break;
    }
    
    // Generate simulation time array
    std::vector<double> timePoints;
    timePoints.reserve(numPoints);
    for (int i = 0; i < numPoints; i++) {
        timePoints.push_back(i * timeStep_);
    }
    
    // Add to result
    result["simulation_time"] = timePoints;
    
    return result;
} 