#pragma once

class FluxCalculationParameters {
public:
    FluxCalculationParameters();
    
    // Parameters needed for flux calculations
    double voltage;
    double pH;
    double time;
    double area;
    double nernstConstant;
    double vesicleHydrogenFree;
    double exteriorHydrogenFree;
}; 