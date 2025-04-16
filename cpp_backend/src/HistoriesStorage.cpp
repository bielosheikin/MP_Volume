#include "HistoriesStorage.h"
#include "Vesicle.h"
#include "Exterior.h"
#include "IonSpecies.h"
#include "IonChannel.h"
#include <stdexcept>

HistoriesStorage::HistoriesStorage() {
    // Initialize empty maps
}

void HistoriesStorage::registerObject(std::shared_ptr<Trackable> obj) {
    if (!obj) {
        throw std::invalid_argument("Cannot register null object");
    }
    
    std::string objName = obj->getDisplayName();
    
    // Check for duplicates
    if (objects_.find(objName) != objects_.end()) {
        std::string existingType = typeid(*objects_[objName]).name();
        std::string newType = typeid(*obj).name();
        
        if (existingType == newType) {
            throw std::runtime_error("Duplicate object: An object with the name \"" + 
                                    objName + "\" has already been registered.");
        } else {
            throw std::runtime_error("Name conflict: \"" + objName + 
                                    "\" is already used by a " + existingType + 
                                    ", cannot use it for a " + newType + 
                                    ". Please ensure all objects have unique names.");
        }
    }
    
    // Register the object
    objects_[objName] = obj;
    
    // Initialize histories for each field in the object's current state
    auto currentState = obj->getCurrentState();
    for (const auto& [fieldName, fieldValue] : currentState) {
        std::string historyKey = objName + "_" + fieldName;
        histories_[historyKey] = std::vector<double>();
    }
}

void HistoriesStorage::registerObject(std::shared_ptr<Vesicle> obj) {
    // Create a Trackable adapter for Vesicle
    std::shared_ptr<Trackable> trackable = std::static_pointer_cast<Trackable>(obj);
    registerObject(trackable);
}

void HistoriesStorage::registerObject(std::shared_ptr<Exterior> obj) {
    // Create a Trackable adapter for Exterior
    std::shared_ptr<Trackable> trackable = std::static_pointer_cast<Trackable>(obj);
    registerObject(trackable);
}

void HistoriesStorage::registerObject(std::shared_ptr<IonSpecies> obj) {
    // Create a Trackable adapter for IonSpecies
    std::shared_ptr<Trackable> trackable = std::static_pointer_cast<Trackable>(obj);
    registerObject(trackable);
}

void HistoriesStorage::registerObject(std::shared_ptr<IonChannel> obj) {
    // Create a Trackable adapter for IonChannel
    std::shared_ptr<Trackable> trackable = std::static_pointer_cast<Trackable>(obj);
    registerObject(trackable);
}

void HistoriesStorage::updateHistories() {
    // Update histories with current state of all objects
    for (const auto& [objName, obj] : objects_) {
        auto currentState = obj->getCurrentState();
        for (const auto& [fieldName, fieldValue] : currentState) {
            std::string historyKey = objName + "_" + fieldName;
            histories_[historyKey].push_back(fieldValue);
        }
    }
}

void HistoriesStorage::flushHistories() {
    // Clear all history values but keep registered objects
    for (auto& [historyKey, historyValues] : histories_) {
        historyValues.clear();
    }
}

void HistoriesStorage::reset() {
    // Clear everything
    objects_.clear();
    histories_.clear();
}

const std::unordered_map<std::string, std::vector<double>>& HistoriesStorage::getHistories() const {
    return histories_;
}

nlohmann::json HistoriesStorage::toJson() const {
    // Convert histories to JSON
    nlohmann::json result;
    
    for (const auto& [historyKey, historyValues] : histories_) {
        result[historyKey] = historyValues;
    }
    
    return result;
}

void HistoriesStorage::addHistory(const std::string& name, double value) {
    histories_[name].push_back(value);
} 