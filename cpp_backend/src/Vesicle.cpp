#include "Vesicle.h"
#include <cmath>
#include <iostream>

// Constants for PI
const double PI = 3.14159265358979323846;

Vesicle::Vesicle(
    double initRadius,
    double initVoltage,
    double initPH,
    double specificCapacitance,
    const std::string& displayName
) : specificCapacitance_(specificCapacitance),
    initVoltage_(initVoltage),
    initRadius_(initRadius),
    initPH_(initPH),
    displayName_(displayName) {
    
    // Safety check for voltage - same as in Python implementation
    double voltageExponent = 80.0;
    double halfActVoltage = -0.04;
    double MAX_VOLTAGE = 709 / voltageExponent + halfActVoltage;
    
    if (initVoltage > MAX_VOLTAGE) {
        std::cout << "Warning: init_voltage " << initVoltage 
                  << " exceeds the safe limit. Clamping to " << MAX_VOLTAGE << "." << std::endl;
        initVoltage_ = MAX_VOLTAGE;
    } else if (initVoltage < -MAX_VOLTAGE) {
        std::cout << "Warning: init_voltage " << initVoltage 
                  << " is below the negative safe limit. Clamping to " << -MAX_VOLTAGE << "." << std::endl;
        initVoltage_ = -MAX_VOLTAGE;
    }
    
    // Calculate initial properties
    initVolume_ = (4.0 / 3.0) * PI * std::pow(initRadius_, 3);
    volume_ = initVolume_;
    
    initArea_ = 4.0 * PI * std::pow(initRadius_, 2);
    area_ = initArea_;
    
    initCapacitance_ = initArea_ * specificCapacitance_;
    capacitance_ = area_ * specificCapacitance_;
    
    initCharge_ = initVoltage_ * initCapacitance_;
    charge_ = initVoltage_ * capacitance_;
    
    pH_ = initPH_;
    voltage_ = initVoltage_;
}

void Vesicle::updateVolume(double newVolume) {
    volume_ = newVolume;
}

void Vesicle::updateArea() {
    // Calculate area from volume assuming sphere
    // A = (36π)^(1/3) * V^(2/3)
    area_ = std::pow(36.0 * PI, 1.0/3.0) * std::pow(volume_, 2.0/3.0);
}

void Vesicle::updateCapacitance() {
    capacitance_ = area_ * specificCapacitance_;
}

void Vesicle::updateCharge(double newCharge) {
    charge_ = newCharge;
}

void Vesicle::updateVoltage() {
    voltage_ = charge_ / capacitance_;
}

void Vesicle::updatePH(double newPH) {
    pH_ = newPH;
} 