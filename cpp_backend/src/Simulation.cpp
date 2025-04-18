#include "Simulation.h"
#include "Vesicle.h"
#include "Exterior.h"
#include "IonSpecies.h"
#include "IonChannel.h"
#include "HistoriesStorage.h"
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <iomanip>

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
    temperature_(310.0), // Temperature in K (body temp)
    initBufferCapacity_(0.0005),
    bufferCapacity_(0.0005),
    displayName_(displayName.empty() ? "simulation" : displayName),
    unaccountedIonAmount_(0.0),
    ionAmountsUpdated_(false),
    vesicle_(nullptr),
    exterior_(nullptr),
    histories_(std::make_shared<HistoriesStorage>()) {
    
    // Initialize storage for histories
    histories_ = std::make_shared<HistoriesStorage>();
    
    // Initialize the vesicle with default parameters
    vesicle_ = std::make_shared<Vesicle>();
    
    // Initialize the exterior with default parameters
    exterior_ = std::make_shared<Exterior>();
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
        
        // Debug: print vesicle state BEFORE initialization
        std::cout << "\n=== C++ STATE BEFORE INITIALIZATION ===" << std::endl;
        std::cout << "Vesicle init volume: " << vesicle_->getInitVolume() << " L" << std::endl;
        std::cout << "Vesicle volume: " << vesicle_->getVolume() << " L" << std::endl;
        std::cout << "Vesicle area: " << vesicle_->getArea() << " m²" << std::endl;
        std::cout << "Vesicle init charge: " << vesicle_->getInitCharge() << " C" << std::endl;
        std::cout << "Vesicle charge: " << vesicle_->getCharge() << " C" << std::endl;
        std::cout << "Vesicle init voltage: " << vesicle_->getInitVoltage() << " V" << std::endl;
        std::cout << "Vesicle voltage: " << vesicle_->getVoltage() << " V" << std::endl;
        std::cout << "Vesicle pH: " << vesicle_->getPH() << std::endl;
        std::cout << "Buffer capacity: " << bufferCapacity_ << std::endl;
        
        // Debug: ion species before setting ion amounts
        std::cout << "\n=== ION SPECIES BEFORE setIonAmounts (C++) ===" << std::endl;
        for (const auto& [name, species] : species_) {
            std::cout << "Ion: " << name << std::endl;
            std::cout << "  Elementary charge: " << species->getElementaryCharge() << std::endl;
            std::cout << "  Init vesicle concentration: " << species->getInitVesicleConc() << " M" << std::endl;
            std::cout << "  Current vesicle concentration: " << species->getVesicleConc() << " M" << std::endl;
            std::cout << "  Vesicle amount: " << species->getVesicleAmount() << " mol" << std::endl;
            std::cout << "  Exterior concentration: " << species->getExteriorConc() << " M" << std::endl;
        }
        
        // Initialize the simulation - match Python's initialization order
        std::cout << "\n=== INITIALIZING SIMULATION (SETTING ION AMOUNTS) ===" << std::endl;
        setIonAmounts();
        
        // Debug: ion species after setting ion amounts
        std::cout << "\n=== ION SPECIES AFTER setIonAmounts (C++) ===" << std::endl;
        for (const auto& [name, species] : species_) {
            std::cout << "Ion: " << name << std::endl;
            std::cout << "  Vesicle concentration: " << species->getVesicleConc() << " M" << std::endl;
            std::cout << "  Vesicle amount: " << species->getVesicleAmount() << " mol" << std::endl;
        }
        
        std::cout << "\n=== CALCULATING UNACCOUNTED ION AMOUNT ===" << std::endl;
        unaccountedIonAmount_ = getUnaccountedIonAmount(); // Store the value for later use
        std::cout << "Unaccounted ion amount: " << unaccountedIonAmount_ << " mol" << std::endl;
        
        // Print debug information about state after initialization
        std::cout << "\n=== C++ STATE AFTER INITIALIZATION ===" << std::endl;
        std::cout << "Vesicle volume: " << vesicle_->getVolume() << " L" << std::endl;
        std::cout << "Vesicle area: " << vesicle_->getArea() << " m²" << std::endl;
        std::cout << "Vesicle capacitance: " << vesicle_->getCapacitance() << " F" << std::endl;
        std::cout << "Vesicle charge: " << vesicle_->getCharge() << " C" << std::endl;
        std::cout << "Vesicle voltage: " << vesicle_->getVoltage() << " V" << std::endl;
        std::cout << "Vesicle pH: " << vesicle_->getPH() << std::endl;
        std::cout << "Buffer capacity: " << bufferCapacity_ << std::endl;
        
        // Run updateSimulationState to make sure we're fully initialized like Python
        std::cout << "\n=== RUNNING updateSimulationState() ===" << std::endl;
        updateSimulationState();
        
        // Print detailed debug information for each physical property update
        std::cout << "\n=== DETAILED STATE AFTER updateSimulationState ===" << std::endl;
        std::cout << "Vesicle volume: " << vesicle_->getVolume() << " L" << std::endl;
        std::cout << "Vesicle area: " << vesicle_->getArea() << " m²" << std::endl;
        std::cout << "Vesicle capacitance: " << vesicle_->getCapacitance() << " F" << std::endl;
        std::cout << "Vesicle charge: " << vesicle_->getCharge() << " C" << std::endl;
        std::cout << "Vesicle voltage: " << vesicle_->getVoltage() << " V" << std::endl;
        std::cout << "Vesicle pH: " << vesicle_->getPH() << std::endl;
        std::cout << "Buffer capacity: " << bufferCapacity_ << std::endl;
        
        std::cout << "\n=== ION SPECIES AFTER updateSimulationState (C++) ===" << std::endl;
        for (const auto& [name, species] : species_) {
            std::cout << "Ion: " << name << std::endl;
            std::cout << "  Vesicle concentration: " << species->getVesicleConc() << " M" << std::endl;
            std::cout << "  Vesicle amount: " << species->getVesicleAmount() << " mol" << std::endl;
        }
        
        // Record the initial state in histories
        histories_->updateHistories();
        
        // After registering objects, add detailed connection information
        std::cout << "\n=== DETAILED ION-CHANNEL CONNECTION STATUS ===" << std::endl;
        for (const auto& [speciesName, species] : species_) {
            std::cout << "Species: " << speciesName << " has " << species->getChannelCount() << " channels connected:" << std::endl;
            species->printConnectedChannels();
        }
        
        // Add after loadFromJson method
        printDetailedDiagnostics();
        
        // Verify all channel connections
        verifyChannelConnections();
        
    } catch (const std::exception& e) {
        throw std::runtime_error(std::string("Error loading simulation configuration: ") + e.what());
    }
}

void Simulation::runOneIteration() {
    // First update the simulation state
    updateSimulationState();
    
    // Get the current flux calculation parameters
    FluxCalculationParameters params = getFluxCalculationParameters();
    
    // Compute channel fluxes first (required for species total flux calculation)
    std::cout << "  Computing channel fluxes:" << std::endl;
    for (const auto& [channelName, channel] : channels_) {
        double flux = channel->computeFlux(params);
        std::cout << "    " << channelName << ": " << flux << " mol/s" << std::endl;
    }
    
    // Compute the fluxes for each ion species
    std::cout << "  Computing ion species fluxes:" << std::endl;
    std::vector<double> fluxes;
    for (const auto& [speciesName, species] : species_) {
        double flux = species->computeTotalFlux(params);
        fluxes.push_back(flux);
        std::cout << "    " << speciesName << ": " << flux << " mol/s" << std::endl;
    }
    
    // Update histories BEFORE updating ion amounts - to match Python implementation exactly
    histories_->updateHistories();
    
    // Reset ion amounts updated flag before updating
    ionAmountsUpdated_ = false;
    
    // Update the ion amounts based on the computed fluxes
    updateIonAmounts(fluxes);
    
    // CRITICAL FIX: Update simulation state AGAIN after ion amounts are updated
    // This ensures all derived values (voltage, pH, etc.) are recalculated
    // based on the new ion amounts, matching the Python implementation
    updateSimulationState();
    
    // Update simulation time
    time_ += timeStep_;
}

void Simulation::run(std::function<void(int)> progressCallback) {
    // Debug: Print simulation state before starting
    std::cout << "\n=== STARTING SIMULATION RUN SEQUENCE ===" << std::endl;
    
    // Set initial ion amounts
    std::cout << "\n=== SETTING ION AMOUNTS AT START OF RUN ===" << std::endl;
    setIonAmounts();
    
    // Calculate the unaccounted ion amount (this is crucial for correct charge calculation)
    std::cout << "\n=== CALCULATING UNACCOUNTED ION AMOUNT AT START OF RUN ===" << std::endl;
    unaccountedIonAmount_ = getUnaccountedIonAmount(); // Store the value
    std::cout << "Unaccounted ion amount: " << unaccountedIonAmount_ << " mol" << std::endl;
    
    // Print initial state
    std::cout << "\n=== SIMULATION STATE BEFORE STARTING ITERATIONS ===" << std::endl;
    std::cout << "Time: " << time_ << " s" << std::endl;
    std::cout << "Vesicle volume: " << vesicle_->getVolume() << " L" << std::endl;
    std::cout << "Vesicle area: " << vesicle_->getArea() << " m²" << std::endl;
    std::cout << "Vesicle capacitance: " << vesicle_->getCapacitance() << " F" << std::endl;
    std::cout << "Vesicle charge: " << vesicle_->getCharge() << " C" << std::endl;
    std::cout << "Vesicle voltage: " << vesicle_->getVoltage() << " V" << std::endl;
    std::cout << "Vesicle pH: " << vesicle_->getPH() << std::endl;
    
    // Calculate number of iterations
    int iterNum = static_cast<int>(totalTime_ / timeStep_);
    std::cout << "Number of iterations: " << iterNum << std::endl;
    
    // Reset histories for time
    histories_->addHistory("simulation_time", time_);
    
    // Main simulation loop - MATCH PYTHON IMPLEMENTATION
    for (int iter = 0; iter < iterNum; iter++) {
        // Print iteration info
        std::cout << "\n=== ITERATION " << iter << " (Time: " << time_ << "s) ===" << std::endl;
        
        // Use runOneIteration which has been fixed to match Python implementation
        runOneIteration();
        
        // Report progress
        if (progressCallback && iterNum > 0) {
            int progressPercent = static_cast<int>(100.0 * (iter + 1) / iterNum);
            progressCallback(progressPercent);
        }
    }
    
    // Make sure final state is recorded
    updateSimulationState();
    histories_->updateHistories();
    
    // Add final time point to histories
    histories_->addHistory("simulation_time", time_);
    
    std::cout << "\n=== SIMULATION COMPLETE ===" << std::endl;
    std::cout << "Final time: " << time_ << " s" << std::endl;
    std::cout << "Final vesicle voltage: " << vesicle_->getVoltage() << " V" << std::endl;
    std::cout << "Final vesicle pH: " << vesicle_->getPH() << std::endl;
    
    // Output detailed final values for comparison
    printFinalValues();
    
    std::cout << "COMPLETED" << std::endl;
}

void Simulation::printFinalValues() {
    std::cout << "\n=== FINAL VALUES FOR COMPARISON ===" << std::endl;
    
    // Vesicle properties
    std::cout << "== Vesicle Properties ==" << std::endl;
    std::cout << "vesicle_init_volume: " << vesicle_->getInitVolume() << " L" << std::endl;
    std::cout << "vesicle_volume: " << vesicle_->getVolume() << " L" << std::endl;
    std::cout << "vesicle_init_charge: " << vesicle_->getInitCharge() << " C" << std::endl;
    std::cout << "vesicle_charge: " << vesicle_->getCharge() << " C" << std::endl;
    std::cout << "vesicle_capacitance: " << vesicle_->getCapacitance() << " F" << std::endl;
    std::cout << "vesicle_voltage: " << vesicle_->getVoltage() << " V" << std::endl;
    std::cout << "vesicle_pH: " << vesicle_->getPH() << " F" << std::endl;
    
    // Ion concentrations and amounts
    std::cout << "== Ion Values ==" << std::endl;
    for (const auto& [name, species] : species_) {
        std::cout << name << "_final_conc: " << species->getVesicleConc() << " M" << std::endl;
        std::cout << name << "_final_amount: " << species->getVesicleAmount() << " mol" << std::endl;
    }
    
    // Unaccounted ion amount
    std::cout << "unaccounted_ion_amount: " << unaccountedIonAmount_ << " mol" << std::endl;
    
    // Other values
    std::cout << "buffer_capacity: " << bufferCapacity_ << std::endl;
    std::cout << "time: " << time_ << " s" << std::endl;
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
    
    // FIXED: Calculate free hydrogen concentrations to exactly match Python implementation
    // Python: flux_calculation_parameters.vesicle_hydrogen_free = hydrogen_species.vesicle_conc * self.buffer_capacity
    
    // Find hydrogen species
    auto hydrogen = species_.find("h");
    if (hydrogen != species_.end()) {
        // Get hydrogen concentration directly from the species
        double hConc = hydrogen->second->getVesicleConc();
        double exteriorHConc = hydrogen->second->getExteriorConc();
        
        // Simply multiply by buffer capacity to match Python exactly
        params.vesicleHydrogenFree = hConc * bufferCapacity_;
        params.exteriorHydrogenFree = exteriorHConc * initBufferCapacity_; 
    } else {
        // Use pH-based calculation as fallback if no hydrogen species found
        double vesicleHPlusTotalConc = std::pow(10, -vesicle_->getPH());
        double exteriorHPlusTotalConc = std::pow(10, -exterior_->getPH());
        
        params.vesicleHydrogenFree = vesicleHPlusTotalConc * bufferCapacity_;
        params.exteriorHydrogenFree = exteriorHPlusTotalConc * initBufferCapacity_;
    }
    
    return params;
}

void Simulation::setIonAmounts() {
    // Calculate volume in liters
    double volumeInLiters = vesicle_->getVolume();
    
    // Set ion amounts based on concentrations and volume
    // Match Python implementation by multiplying by 1000 for unit conversion (L to mL)
    for (const auto& [speciesName, species] : species_) {
        double concentration = species->getVesicleConc();  // moles/liter
        double amount = concentration * 1000 * volumeInLiters;    // moles
        species->setVesicleAmount(amount);
    }
}

void Simulation::updateIonAmounts(const std::vector<double>& fluxes) {
    std::cout << "  updateIonAmounts calculation:" << std::endl;
    
    // Make sure we have the right number of fluxes
    if (fluxes.size() != species_.size()) {
        std::cerr << "Error: Number of fluxes (" << fluxes.size() 
                  << ") doesn't match number of species (" << species_.size() << ")" << std::endl;
        return;
    }
    
    // Update each ion's amount based on its flux
    size_t i = 0;
    for (auto& [name, species] : species_) {
        double oldAmount = species->getVesicleAmount();
        double flux = fluxes[i++];
        
        // Update = old_amount + (flux * time_step)
        double newAmount = oldAmount + (flux * timeStep_);
        
        // Ensure amount doesn't go negative
        if (newAmount < 0) {
            std::cout << "    Warning: " << name << " ion amount below zero, resetting to zero" << std::endl;
            newAmount = 0;
        }
        
        species->setVesicleAmount(newAmount);
        std::cout << "    " << name << ": " << oldAmount << " + (" << flux << " * " << timeStep_ 
                  << ") = " << newAmount << " mol" << std::endl;
    }
    
    // Set the flag to indicate ion amounts have been updated
    ionAmountsUpdated_ = true;
}

void Simulation::updateVesicleConcentrations() {
    // Remove the special case for t=0 to match Python implementation
    // Calculate volume in liters
    double volumeInLiters = vesicle_->getVolume();
    
    // Update concentrations based on amounts and volume
    // Match Python implementation by dividing by 1000 for unit conversion
    for (const auto& [speciesName, species] : species_) {
        double amount = species->getVesicleAmount();       // moles
        double concentration = amount / (1000 * volumeInLiters);  // moles/liter
        species->setVesicleConc(concentration);
    }
}

double Simulation::getUnaccountedIonAmount() {
    // Python implementation exactly:
    // self.unaccounted_ion_amounts = ((self.vesicle.init_charge / FARADAY_CONSTANT) - 
    //         (sum(ion.elementary_charge * ion.init_vesicle_conc for ion in self.all_species)) * self.vesicle.init_volume)
    
    // Debug output of all steps
    std::cout << "  getUnaccountedIonAmount calculation:" << std::endl;
    
    // Step 1: Calculate the initial charge in moles (vesicle.init_charge / FARADAY_CONSTANT)
    double initCharge = vesicle_->getInitCharge();
    double initChargeInMoles = initCharge / FARADAY_CONSTANT;
    std::cout << "    Init charge: " << initCharge << " C" << std::endl;
    std::cout << "    Init charge in moles: " << initChargeInMoles << " mol" << std::endl;
    
    // Step 2: Calculate sum(ion.elementary_charge * ion.init_vesicle_conc for ion in self.all_species)
    double totalIonicChargeConcentration = 0.0;
    std::cout << "    Ion contributions to charge concentration:" << std::endl;
    
    // Count how many species we're processing to verify all are included
    int speciesCount = 0;
    for (const auto& [speciesName, species] : species_) {
        speciesCount++;
        double initConc = species->getInitVesicleConc();         // mol/L
        double charge = species->getElementaryCharge();          // elementary charge
        double contribution = charge * initConc;
        totalIonicChargeConcentration += contribution;      // sum of charge * concentration
        std::cout << "      " << speciesName << ": " << charge << " * " << initConc << " = " << contribution << std::endl;
    }
    
    std::cout << "    Total number of ion species processed: " << speciesCount << std::endl;
    std::cout << "    Total ionic charge concentration: " << totalIonicChargeConcentration << " mol/L" << std::endl;
    
    // Step 3: Calculate the rest of the formula - EXACTLY MATCH PYTHON
    double initVolume = vesicle_->getInitVolume();
    std::cout << "    Init volume: " << initVolume << " L" << std::endl;
    
    // Fix: Add the factor of 1000 to match Python implementation
    double ionicChargeInMoles = totalIonicChargeConcentration * 1000 * initVolume;
    std::cout << "    Ionic charge in moles: " << ionicChargeInMoles << " mol" << std::endl;
    
    // Python formula is: charge_in_moles - (sum_of(conc * charge) * volume)
    double unaccountedCharge = initChargeInMoles - ionicChargeInMoles;
    std::cout << "    Unaccounted charge: " << unaccountedCharge << " mol" << std::endl;
    
    // In Python, we're calculating exactly:
    // Python: unaccounted_ion_amounts = initChargeInMoles - totalIonicChargeConcentration * 1000 * initVolume
    
    std::cout << "    Python calculation check:" << std::endl;
    std::cout << "      Init charge / FARADAY: " << initCharge << " / " << FARADAY_CONSTANT << " = " << initChargeInMoles << std::endl;
    std::cout << "      Sum(z * c) * 1000 * V: " << totalIonicChargeConcentration << " * 1000 * " << initVolume << " = " << ionicChargeInMoles << std::endl;
    std::cout << "      Difference: " << initChargeInMoles << " - " << ionicChargeInMoles << " = " << unaccountedCharge << std::endl;
    
    // For debug purposes, print with higher precision
    std::cout << std::setprecision(17) << "C++ init_charge_in_moles: " << initChargeInMoles << " mol" << std::endl;
    std::cout << std::setprecision(17) << "C++ total_ionic_charge_concentration: " << totalIonicChargeConcentration << " mol/L" << std::endl;
    std::cout << std::setprecision(17) << "C++ init_volume: " << initVolume << " L" << std::endl;
    std::cout << std::setprecision(17) << "C++ ionic_charge_in_moles: " << ionicChargeInMoles << " mol" << std::endl;
    std::cout << std::setprecision(17) << "C++ unaccounted_charge: " << unaccountedCharge << " mol" << std::endl;
    
    return unaccountedCharge;
}

void Simulation::updateVolume() {
    // Debug output before volume update
    std::cout << "  updateVolume calculation:" << std::endl;
    std::cout << "    Initial volume: " << vesicle_->getVolume() << " L" << std::endl;
    
    // Calculate new volume based on osmotic pressure effects (matching Python implementation)
    if (vesicle_ && !species_.empty()) {
        double sumCurrentConc = 0.0;
        double sumInitConc = 0.0;
        
        // Sum concentrations excluding hydrogen ions - FIXED to use init_vesicle_conc for sumInitConc
        std::cout << "    Ion contributions to concentrations:" << std::endl;
        for (const auto& [name, species] : species_) {
            if (name != "h") {
                double currentConc = species->getVesicleConc();
                double initConc = species->getInitVesicleConc();
                
                sumCurrentConc += currentConc;
                sumInitConc += initConc;
                
                std::cout << "      " << name << " current: " << currentConc << " M, init: " << initConc << " M" << std::endl;
            }
        }
        
        std::cout << "    Sum of current concentrations (excl. h): " << sumCurrentConc << " M" << std::endl;
        std::cout << "    Sum of init concentrations (excl. h): " << sumInitConc << " M" << std::endl;
        
        // Add unaccounted ion amount to both sums
        // Using the pre-calculated value from the start of the simulation
        sumCurrentConc += std::abs(unaccountedIonAmount_);
        sumInitConc += std::abs(unaccountedIonAmount_);
        
        std::cout << "    With unaccounted ion amount:" << std::endl;
        std::cout << "      Sum current: " << sumCurrentConc << " M" << std::endl;
        std::cout << "      Sum init: " << sumInitConc << " M" << std::endl;
        
        // Calculate new volume based on concentration ratio
        if (sumInitConc > 0) {
            double newVolume = vesicle_->getInitVolume() * (sumCurrentConc / sumInitConc);
            std::cout << "    New volume = " << vesicle_->getInitVolume() << " * (" << sumCurrentConc << " / " << sumInitConc << ") = " << newVolume << " L" << std::endl;
            vesicle_->updateVolume(newVolume);
        } else {
            std::cout << "    Warning: sumInitConc is zero, cannot update volume" << std::endl;
        }
    }
    
    std::cout << "    Final volume: " << vesicle_->getVolume() << " L" << std::endl;
}

void Simulation::updateArea() {
    vesicle_->updateArea();
}

void Simulation::updateCharge() {
    // Debug output before calculation
    std::cout << "  updateCharge calculation:" << std::endl;
    std::cout << "    Initial charge: " << vesicle_->getCharge() << " C" << std::endl;
    
    // For the first step and ONLY if ion amounts haven't been updated, use the initial charge value
    if (time_ == 0.0 && !ionAmountsUpdated_) {
        std::cout << "    Using initial charge (t=0, pre-flux): " << vesicle_->getInitCharge() << " C" << std::endl;
        vesicle_->setCharge(vesicle_->getInitCharge());
        std::cout << "    Final charge: " << vesicle_->getCharge() << " C" << std::endl;
        return;
    }
    
    // In all other cases (t>0 or ion amounts updated), calculate charge from ion amounts
    std::cout << "    Calculating charge from ion amounts..." << std::endl;
    
    // Calculate total ionic charge inside the vesicle (moles)
    double totalIonicCharge = 0.0;
    std::cout << "    Ion contributions to charge:" << std::endl;
    for (const auto& [speciesName, species] : species_) {
        double amount = species->getVesicleAmount();           // moles
        double charge = species->getElementaryCharge();        // elementary charge
        double contribution = amount * charge;                 // moles of charge
        totalIonicCharge += contribution;
        std::cout << "      " << speciesName << ": " << charge << " * " << amount << " = " << contribution << " mol" << std::endl;
    }
    
    std::cout << "    Total ionic charge: " << totalIonicCharge << " mol" << std::endl;
    
    // Add unaccounted ion amount to the total charge
    std::cout << "    Unaccounted ion amount: " << unaccountedIonAmount_ << " mol" << std::endl;
    
    totalIonicCharge += unaccountedIonAmount_;
    std::cout << "    Total charge with unaccounted: " << totalIonicCharge << " mol" << std::endl;
    
    // Convert to Coulombs
    double ionicChargeInCoulombs = totalIonicCharge * FARADAY_CONSTANT;
    std::cout << "    Charge in Coulombs: " << ionicChargeInCoulombs << " C" << std::endl;
    
    // Use direct setter rather than update method to ensure consistency
    vesicle_->setCharge(ionicChargeInCoulombs);
    std::cout << "    Final charge: " << vesicle_->getCharge() << " C" << std::endl;
}

void Simulation::updateCapacitance() {
    std::cout << "  updateCapacitance calculation:" << std::endl;
    std::cout << "    Initial capacitance: " << vesicle_->getCapacitance() << " F" << std::endl;
    
    // Update capacitance based on area and specific capacitance
    vesicle_->updateCapacitance();
    
    std::cout << "    Final capacitance: " << vesicle_->getCapacitance() << " F" << std::endl;
}

void Simulation::updateVoltage() {
    std::cout << "  updateVoltage calculation:" << std::endl;
    std::cout << "    Initial voltage: " << vesicle_->getVoltage() << " V" << std::endl;
    
    // Always update voltage based on charge and capacitance
    double charge = vesicle_->getCharge();
    double capacitance = vesicle_->getCapacitance();
    double newVoltage = charge / capacitance;
    std::cout << "    New voltage = " << charge << " / " << capacitance << " = " << newVoltage << " V" << std::endl;
    vesicle_->setVoltage(newVoltage);
    
    std::cout << "    Final voltage: " << vesicle_->getVoltage() << " V" << std::endl;
}

void Simulation::updateBuffer() {
    std::cout << "  updateBuffer calculation:" << std::endl;
    std::cout << "    Initial buffer capacity: " << bufferCapacity_ << std::endl;
    
    // Update buffer capacity based on volume ratio, matching Python implementation
    double oldBufferCapacity = bufferCapacity_;
    bufferCapacity_ = initBufferCapacity_ * vesicle_->getVolume() / vesicle_->getInitVolume();
    
    std::cout << "    New buffer capacity = " << initBufferCapacity_ << " * " 
              << vesicle_->getVolume() << " / " << vesicle_->getInitVolume() 
              << " = " << bufferCapacity_ << std::endl;
}

void Simulation::updatePH() {
    std::cout << "  updatePH calculation:" << std::endl;
    std::cout << "    Initial pH: " << vesicle_->getPH() << std::endl;
    
    // Find hydrogen ion species
    auto hydrogen = species_.find("h");
    if (hydrogen != species_.end()) {
        // Get hydrogen concentration
        double hConc = hydrogen->second->getVesicleConc();
        std::cout << "    Hydrogen concentration: " << hConc << " M" << std::endl;
        
        // Apply buffer effect to get free hydrogen concentration - match Python implementation exactly
        double freeHConc = hConc * bufferCapacity_;
        std::cout << "    Free hydrogen calculation: " << hConc << " * " << bufferCapacity_ << " = " << freeHConc << " M" << std::endl;
        
        // Ensure concentration is positive
        if (freeHConc <= 0) {
            std::cout << "    Warning: free_hydrogen_conc is zero or negative. Setting pH to a default value." << std::endl;
            vesicle_->updatePH(7.0);  // Default pH value
        } else {
            // Convert to pH (pH = -log10([H+]))
            double newPH = -std::log10(freeHConc);
            std::cout << "    New pH = -log10(" << freeHConc << ") = " << newPH << std::endl;
            
            // Update vesicle pH
            vesicle_->updatePH(newPH);
        }
    }
    
    std::cout << "    Final pH: " << vesicle_->getPH() << std::endl;
}

void Simulation::updateSimulationState() {
    // Order matters! Match Python implementation exactly
    
    // Step 1: Update the physical properties
    updateVolume();
    updateVesicleConcentrations();
    updateBuffer();
    updateArea();
    updateCapacitance();
    
    // Step 2: Update electrical properties in this specific order
    // - First charge (depends on ion amounts)
    // - Then voltage (depends on charge and capacitance)
    updateCharge();
    updateVoltage();
    
    // Step 3: Update chemical properties
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

void Simulation::printDetailedDiagnostics() {
    std::cout << "\n=== DETAILED C++ CHARGE CALCULATION (FULL PRECISION) ===" << std::endl;
    double initCharge = vesicle_->getInitCharge();
    std::cout << std::setprecision(17) << "C++ init_charge: " << initCharge << " C" << std::endl;
    
    double initChargeInMoles = initCharge / FARADAY_CONSTANT;
    std::cout << std::setprecision(17) << "C++ init_charge_in_moles: " << initChargeInMoles << " mol" << std::endl;
    
    // Calculate sum(species->getElementaryCharge() * species->getInitVesicleConc())
    double totalIonicChargeConcentration = 0.0;
    for (const auto& [speciesName, species] : species_) {
        double initConc = species->getInitVesicleConc();
        double charge = species->getElementaryCharge();
        double contribution = charge * initConc;
        totalIonicChargeConcentration += contribution;
        std::cout << std::setprecision(17) << "  C++ " << speciesName << ": " << charge << " * " 
                  << initConc << " = " << contribution << std::endl;
    }
    std::cout << std::setprecision(17) << "C++ sum(elementary_charge * init_vesicle_conc): " 
              << totalIonicChargeConcentration << " mol/L" << std::endl;
    
    // Calculate ionic charge in moles
    double initVolume = vesicle_->getInitVolume();
    std::cout << std::setprecision(17) << "C++ init_volume: " << initVolume << " L" << std::endl;
    
    double ionicChargeInMoles = totalIonicChargeConcentration * initVolume;
    std::cout << std::setprecision(17) << "C++ ionic_charge_in_moles: " << ionicChargeInMoles << " mol" << std::endl;
    
    // Calculate unaccounted ion amount
    double unaccountedCharge = initChargeInMoles - ionicChargeInMoles;
    std::cout << std::setprecision(17) << "C++ unaccounted_charge (manual calc): " << unaccountedCharge << " mol" << std::endl;
    
    // Print detailed vesicle properties
    std::cout << "\n=== DETAILED VESICLE PROPERTIES (C++) ===" << std::endl;
    double initRadius = 1.3e-6; // Default value, since C++ doesn't store this directly
    std::cout << std::setprecision(17) << "init_radius: " << initRadius << " m" << std::endl;
    std::cout << std::setprecision(17) << "init_volume: " << vesicle_->getInitVolume() << " L" << std::endl;
    std::cout << std::setprecision(17) << "volume: " << vesicle_->getVolume() << " L" << std::endl;
    double initArea = 4 * M_PI * std::pow(initRadius, 2);
    std::cout << std::setprecision(17) << "init_area: " << initArea << " m²" << std::endl;
    std::cout << std::setprecision(17) << "area: " << vesicle_->getArea() << " m²" << std::endl;
    std::cout << std::setprecision(17) << "init_charge: " << vesicle_->getInitCharge() << " C" << std::endl;
    std::cout << std::setprecision(17) << "charge: " << vesicle_->getCharge() << " C" << std::endl;
    double specificCapacitance = 0.01; // Default value
    std::cout << std::setprecision(17) << "specific_capacitance: " << specificCapacitance << " F/m²" << std::endl;
    double initCapacitance = initArea * specificCapacitance;
    std::cout << std::setprecision(17) << "init_capacitance: " << initCapacitance << " F" << std::endl;
    std::cout << std::setprecision(17) << "capacitance: " << vesicle_->getCapacitance() << " F" << std::endl;
    std::cout << std::setprecision(17) << "init_voltage: " << vesicle_->getInitVoltage() << " V" << std::endl;
    std::cout << std::setprecision(17) << "voltage: " << vesicle_->getVoltage() << " V" << std::endl;
}

// Add a new method to verify channel connections after initialization
void Simulation::verifyChannelConnections() {
    std::cout << "\n=== VERIFYING CHANNEL CONNECTIONS ===" << std::endl;
    
    for (const auto& [channelName, channel] : channels_) {
        std::cout << "Checking channel: " << channelName << std::endl;
        
        // Try to compute a simple flux to verify the channel is connected correctly
        try {
            FluxCalculationParameters testParams;
            testParams.voltage = vesicle_->getVoltage();
            testParams.pH = vesicle_->getPH();
            testParams.time = 0.0;
            testParams.area = vesicle_->getArea();
            testParams.nernstConstant = IDEAL_GAS_CONSTANT * temperature_ / FARADAY_CONSTANT;
            
            // Calculate free hydrogen concentrations
            double vesicleHPlusTotalConc = std::pow(10, -vesicle_->getPH());
            double exteriorHPlusTotalConc = std::pow(10, -exterior_->getPH());
            testParams.vesicleHydrogenFree = vesicleHPlusTotalConc * bufferCapacity_;
            testParams.exteriorHydrogenFree = exteriorHPlusTotalConc;
            
            double testFlux = channel->computeFlux(testParams);
            std::cout << "  ✓ " << channelName << " correctly connected (Test flux: " << testFlux << " mol/s)" << std::endl;
        } 
        catch (const std::exception& e) {
            std::cerr << "  ❌ ERROR: " << channelName << " - " << e.what() << std::endl;
            throw std::runtime_error("Channel connection verification failed for: " + channelName);
        }
    }
    
    std::cout << "All channel connections verified successfully." << std::endl;
} 