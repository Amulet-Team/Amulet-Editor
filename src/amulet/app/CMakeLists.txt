cmake_minimum_required(VERSION 3.13)

project(amulet_app LANGUAGES CXX)

# Add pybind11
if (NOT TARGET pybind11::module)
    find_package(pybind11 CONFIG REQUIRED)
endif()

# Find C++ files
file(GLOB_RECURSE SOURCES LIST_DIRECTORIES false ${CMAKE_CURRENT_LIST_DIR}/*.cpp)
file(GLOB_RECURSE HEADERS LIST_DIRECTORIES false ${CMAKE_CURRENT_LIST_DIR}/*.hpp)

# Add python extension
pybind11_add_module(_sys)
target_compile_definitions(_sys PRIVATE PYBIND11_DETAILED_ERROR_MESSAGES)
target_sources(_sys PRIVATE ${SOURCES} ${HEADERS})

if(NOT DEFINED AMULET_EDITOR_EXT_SRC_DIR)
    set(AMULET_EDITOR_EXT_SRC_DIR ${AMULET_EDITOR_SRC_DIR})
endif()

# Install
install(TARGETS _sys DESTINATION ${AMULET_EDITOR_EXT_SRC_DIR}/amulet/app)
