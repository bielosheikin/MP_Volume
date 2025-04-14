cmake_minimum_required(VERSION 3.15)
project(MPVolumeSimulationEngine)

# Set policy to address DOWNLOAD_EXTRACT_TIMESTAMP warning if using CMake 3.24+
if(POLICY CMP0135)
  cmake_policy(SET CMP0135 NEW)
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add nlohmann/json (header-only library)
include(FetchContent)
FetchContent_Declare(json
  URL https://github.com/nlohmann/json/releases/download/v3.11.2/json.tar.xz
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
FetchContent_MakeAvailable(json)

# Source files
set(SOURCE_FILES
    src/main.cpp
    src/Simulation.cpp
    src/IonChannel.cpp
    src/IonSpecies.cpp
    src/Vesicle.cpp
    src/Exterior.cpp
    src/HistoriesStorage.cpp
    src/FluxCalculationParameters.cpp
)

# Include directories
include_directories(include)

# Add executable
add_executable(simulation_engine ${SOURCE_FILES})
target_link_libraries(simulation_engine PRIVATE nlohmann_json::nlohmann_json)

# Optimization flags for Release build - use compiler-specific flags
if(MSVC)
  # MSVC doesn't support -O3, it uses /O2 for full optimization
  set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /O2")
else()
  # GCC and Clang use -O3
  set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3")
endif() 