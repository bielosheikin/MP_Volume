#pragma once

#include <string>
#include <unordered_map>
#include <vector>
#include <memory>
#include <functional>
#include <nlohmann/json.hpp>

// Forward declarations
class Vesicle;
class Exterior;
class IonSpecies;
class IonChannel;

// Interface for trackable objects
class Trackable {
public:
    virtual ~Trackable() = default;
    virtual std::string getDisplayName() const = 0;
    virtual std::unordered_map<std::string, double> getCurrentState() const = 0;
};

class HistoriesStorage {
public:
    HistoriesStorage();
    
    // Register objects for tracking
    void registerObject(std::shared_ptr<Trackable> obj);
    
    // Template specializations for different object types
    void registerObject(std::shared_ptr<Vesicle> obj);
    void registerObject(std::shared_ptr<Exterior> obj);
    void registerObject(std::shared_ptr<IonSpecies> obj);
    void registerObject(std::shared_ptr<IonChannel> obj);
    
    // Update histories with current state of all objects
    void updateHistories();
    
    // Reset/clear histories
    void flushHistories();
    void reset();
    
    // Get histories data
    const std::unordered_map<std::string, std::vector<double>>& getHistories() const;
    
    // Export histories to JSON
    nlohmann::json toJson() const;
    
private:
    // Map from object to its display name
    std::unordered_map<std::string, std::shared_ptr<Trackable>> objects_;
    
    // Map from tracked field name to its history values
    std::unordered_map<std::string, std::vector<double>> histories_;
}; 