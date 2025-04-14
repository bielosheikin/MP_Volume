#pragma once

#include <string>
#include <cmath>
#include <unordered_map>
#include "HistoriesStorage.h"  // For Trackable interface

class Vesicle : public Trackable {
public:
    Vesicle(
        double initRadius = 1.3e-6,
        double initVoltage = 4e-2,
        double initPH = 7.4,
        double specificCapacitance = 1e-2,
        const std::string& displayName = "Vesicle"
    );
    
    // Methods to update physical properties
    void updateVolume(double newVolume);
    void updateArea();
    void updateCapacitance();
    void updateCharge(double newCharge);
    void updateVoltage();
    void updatePH(double newPH);
    
    // Getters
    std::string getDisplayName() const override { return displayName_; }
    double getPH() const { return pH_; }
    double getVolume() const { return volume_; }
    double getInitVolume() const { return initVolume_; }
    double getArea() const { return area_; }
    double getCapacitance() const { return capacitance_; }
    double getCharge() const { return charge_; }
    double getVoltage() const { return voltage_; }
    
    // Implement Trackable interface
    std::unordered_map<std::string, double> getCurrentState() const override {
        return {
            {"pH", pH_},
            {"volume", volume_},
            {"area", area_},
            {"capacitance", capacitance_},
            {"charge", charge_},
            {"voltage", voltage_}
        };
    }
    
private:
    // Configuration properties
    double specificCapacitance_;
    double initVoltage_;
    double initRadius_;
    double initPH_;
    std::string displayName_;
    
    // Derived initial properties
    double initVolume_;
    double initArea_;
    double initCapacitance_;
    double initCharge_;
    
    // Runtime properties
    double pH_;
    double volume_;
    double area_;
    double capacitance_;
    double charge_;
    double voltage_;
}; 