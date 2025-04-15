#pragma once

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include "FluxCalculationParameters.h"
#include "HistoriesStorage.h"  // For Trackable interface

// Forward declaration to avoid circular dependency
class IonChannel;

class IonSpecies : public std::enable_shared_from_this<IonSpecies>, public Trackable {
public:
    IonSpecies(
        const std::string& displayName,
        double initVesicleConc,
        double exteriorConc,
        double elementaryCharge
    );
    
    // Connect a channel to this ion species
    void connectChannel(std::shared_ptr<IonChannel> channel, 
                       std::shared_ptr<IonSpecies> secondarySpecies = nullptr);
    
    // Compute total flux across all connected channels
    double computeTotalFlux(const FluxCalculationParameters& params);
    
    // Getters
    std::string getDisplayName() const override { return displayName_; }
    double getVesicleConc() const { return vesicleConc_; }
    double getExteriorConc() const { return exteriorConc_; }
    double getElementaryCharge() const { return elementaryCharge_; }
    double getVesicleAmount() const { return vesicleAmount_; }
    double getInitVesicleConc() const { return initVesicleConc_; }
    
    // Setters
    void setVesicleConc(double value);
    void setVesicleAmount(double value);
    
    // Implement Trackable interface
    std::unordered_map<std::string, double> getCurrentState() const override {
        return {
            {"vesicle_conc", vesicleConc_},
            {"vesicle_amount", vesicleAmount_}
        };
    }
    
private:
    // Check if a channel is compatible with this ion species
    bool validateChannelCompatibility(std::shared_ptr<IonChannel> channel,
                                    std::shared_ptr<IonSpecies> primarySpecies,
                                    std::shared_ptr<IonSpecies> secondarySpecies = nullptr);
    
    // Configuration properties
    std::string displayName_;
    double initVesicleConc_;
    double exteriorConc_;
    double elementaryCharge_;
    
    // Runtime properties
    double vesicleConc_;
    double vesicleAmount_;
    
    // Connected channels
    std::vector<std::shared_ptr<IonChannel>> channels_;
}; 