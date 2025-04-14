#pragma once

#include <string>
#include <unordered_map>
#include "HistoriesStorage.h"  // For Trackable interface

class Exterior : public Trackable {
public:
    Exterior(
        double pH = 7.2,
        const std::string& displayName = "Exterior"
    );
    
    // Getters
    std::string getDisplayName() const override { return displayName_; }
    double getPH() const { return pH_; }
    
    // Setters
    void setPH(double value) { pH_ = value; }
    
    // Implement Trackable interface
    std::unordered_map<std::string, double> getCurrentState() const override {
        return {
            {"pH", pH_}
        };
    }
    
private:
    // Properties
    double pH_;
    std::string displayName_;
}; 