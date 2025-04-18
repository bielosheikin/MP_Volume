#include "IonSpecies.h"
#include "IonChannel.h"
#include <stdexcept>
#include <iostream>

IonSpecies::IonSpecies(
    const std::string& displayName,
    double initVesicleConc,
    double exteriorConc,
    double elementaryCharge
) : displayName_(displayName.empty() ? "UnnamedSpecies" : displayName),
    initVesicleConc_(initVesicleConc),
    exteriorConc_(exteriorConc),
    elementaryCharge_(elementaryCharge),
    vesicleConc_(initVesicleConc),
    vesicleAmount_(0.0) {
}

void IonSpecies::connectChannel(
    std::shared_ptr<IonChannel> channel,
    std::shared_ptr<IonSpecies> secondarySpecies
) {
    // Validate arguments
    if (!channel) {
        throw std::invalid_argument("Channel cannot be null");
    }
    
    // Validate compatibility with this species
    if (!validateChannelCompatibility(channel, shared_from_this(), secondarySpecies)) {
        if (secondarySpecies) {
            throw std::invalid_argument(
                "Channel '" + channel->getDisplayName() + 
                "' is not compatible with the provided ion species: primary='" + 
                displayName_ + "', secondary='" + secondarySpecies->getDisplayName() + "'"
            );
        } else {
            throw std::invalid_argument(
                "Channel '" + channel->getDisplayName() + 
                "' does not support the ion species '" + displayName_ + "'. " +
                "Expected primary ion type is '" + channel->getAllowedPrimaryIon() + "'"
            );
        }
    }
    
    // Connect the channel to this species (and secondary if provided)
    channel->connectSpecies(shared_from_this(), secondarySpecies);
    
    // Add to list of connected channels
    channels_.push_back(channel);
}

double IonSpecies::computeTotalFlux(const FluxCalculationParameters& params) {
    double totalFlux = 0.0;
    
    // Compute flux across all connected channels
    for (const auto& channel : channels_) {
        // Do not silently catch errors - if a channel is not properly connected,
        // this should cause an exception that identifies the issue
        double flux = channel->computeFlux(params);
        totalFlux += flux;
    }
    
    return totalFlux;
}

bool IonSpecies::validateChannelCompatibility(
    std::shared_ptr<IonChannel> channel,
    std::shared_ptr<IonSpecies> primarySpecies,
    std::shared_ptr<IonSpecies> secondarySpecies
) {
    // Get allowed ions from channel
    const std::string& allowedPrimaryIon = channel->getAllowedPrimaryIon();
    const std::string& allowedSecondaryIon = channel->getAllowedSecondaryIon();
    
    if (!allowedSecondaryIon.empty()) {
        // Two-ion channel check - check both orders
        if (!secondarySpecies) {
            return false; // Secondary species required but not provided
        }
        
        bool validOrder1 = (primarySpecies->getDisplayName() == allowedPrimaryIon && 
                           secondarySpecies->getDisplayName() == allowedSecondaryIon);
        
        bool validOrder2 = (primarySpecies->getDisplayName() == allowedSecondaryIon && 
                           secondarySpecies->getDisplayName() == allowedPrimaryIon);
        
        return validOrder1 || validOrder2;
    } else {
        // Single-ion channel check
        return primarySpecies->getDisplayName() == allowedPrimaryIon;
    }
}

void IonSpecies::setVesicleAmount(double value) { 
    // Add safety check to prevent negative amounts
    if (value < 0) {
        std::cout << "Warning: " << displayName_ << " ion amount fell below zero and has been reset to zero." << std::endl;
        vesicleAmount_ = 0;
    } else {
        vesicleAmount_ = value; 
    }
}

void IonSpecies::setVesicleConc(double value) { 
    // Add safety check to prevent negative concentrations
    if (value <= 0) {
        std::cout << "Warning: " << displayName_ << " vesicle concentration is zero or negative. Setting to a minimum threshold." << std::endl;
        vesicleConc_ = 1e-9;  // Minimum threshold for concentration
    } else {
        vesicleConc_ = value; 
    }
}

void IonSpecies::printConnectedChannels() const {
    if (channels_.empty()) {
        std::cout << "  No channels connected to this species." << std::endl;
        return;
    }
    
    for (const auto& channel : channels_) {
        std::cout << "  - " << channel->getDisplayName();
        
        // Print primary and secondary species info if available
        std::cout << " (allowed primary: " << channel->getAllowedPrimaryIon();
        
        if (!channel->getAllowedSecondaryIon().empty()) {
            std::cout << ", allowed secondary: " << channel->getAllowedSecondaryIon();
        }
        
        std::cout << ")" << std::endl;
    }
} 