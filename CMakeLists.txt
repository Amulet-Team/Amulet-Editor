cmake_minimum_required(VERSION 4.1)

project(amulet_app LANGUAGES CXX)

set(amulet_app_DIR ${CMAKE_CURRENT_LIST_DIR}/src/amulet/app CACHE PATH "")

# Set C++20
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Set platform variables
if (WIN32)
	# set windows 7 as the minimum version
	add_definitions(-D_WIN32_WINNT=0x0601)
elseif(APPLE)
    set(CMAKE_OSX_DEPLOYMENT_TARGET "10.15")
elseif(UNIX)
    set(CMAKE_POSITION_INDEPENDENT_CODE ON)
else()
    message( FATAL_ERROR "Unsupported platform. Please submit a pull request to support this platform." )
endif()

if (MSVC)
    add_definitions("/MP")
endif()

find_package(Python3 COMPONENTS Interpreter Development.Module REQUIRED)

# Find libraries
if (NOT TARGET pybind11::module)
    find_package(pybind11 CONFIG REQUIRED)
endif()
if (NOT TARGET amulet_pybind11_extensions)
    find_package(amulet_pybind11_extensions CONFIG REQUIRED)
endif()
if (NOT TARGET amulet_io)
    find_package(amulet_io CONFIG REQUIRED)
endif()
if (NOT TARGET leveldb)
    find_package(amulet_leveldb CONFIG REQUIRED)
endif()
if (NOT TARGET amulet_utils)
    find_package(amulet_utils CONFIG REQUIRED)
endif()
if (NOT TARGET amulet_nbt)
    find_package(amulet_nbt CONFIG REQUIRED)
endif()
if (NOT TARGET amulet_core)
    find_package(amulet_core CONFIG REQUIRED)
endif()
if (NOT TARGET amulet_resource_pack)
    find_package(amulet_resource_pack CONFIG REQUIRED)
endif()
if (NOT TARGET amulet_game)
    find_package(amulet_game CONFIG REQUIRED)
endif()
if (NOT TARGET amulet_anvil)
    find_package(amulet_anvil CONFIG REQUIRED)
endif()
if (NOT TARGET amulet_level)
    find_package(amulet_level CONFIG REQUIRED)
endif()

# Find C++ files
file(REAL_PATH src SOURCE_PATH)
file(GLOB_RECURSE EXTENSION_SOURCES LIST_DIRECTORIES false ${SOURCE_PATH}/amulet/app/*.py.cpp)
file(GLOB_RECURSE EXTENSION_HEADERS LIST_DIRECTORIES false ${SOURCE_PATH}/amulet/app/*.py.hpp)

# Add python extension
pybind11_add_module(_amulet_app)
if(APPLE)
    set_target_properties(_amulet_app PROPERTIES INSTALL_RPATH "@loader_path")
elseif(UNIX)
    set_target_properties(_amulet_app PROPERTIES INSTALL_RPATH "$ORIGIN")
endif()
set_target_properties(_amulet_app PROPERTIES CXX_VISIBILITY_PRESET hidden)
set_target_properties(_amulet_app PROPERTIES FOLDER "Python")
target_link_libraries(_amulet_app PRIVATE amulet_pybind11_extensions)
target_compile_definitions(_amulet_app PRIVATE PYBIND11_DETAILED_ERROR_MESSAGES)
target_compile_definitions(_amulet_app PRIVATE PYBIND11_VERSION="${pybind11_VERSION}")
target_compile_definitions(_amulet_app PRIVATE COMPILER_ID="${CMAKE_CXX_COMPILER_ID}")
target_compile_definitions(_amulet_app PRIVATE COMPILER_VERSION="${CMAKE_CXX_COMPILER_VERSION}")
target_sources(_amulet_app PRIVATE ${EXTENSION_SOURCES} ${EXTENSION_HEADERS})
foreach(FILE ${EXTENSION_SOURCES} ${EXTENSION_HEADERS})
    file(RELATIVE_PATH REL_PATH ${SOURCE_PATH} ${FILE})
    get_filename_component(GROUP ${REL_PATH} DIRECTORY)
    string(REPLACE "/" "\\" GROUP ${GROUP})
    source_group(${GROUP} FILES ${FILE})
endforeach()

if(NOT DEFINED AMULET_APP_EXT_DIR)
    set(AMULET_APP_EXT_DIR ${amulet_app_DIR})
endif()

# Install
install(TARGETS _amulet_app DESTINATION ${AMULET_APP_EXT_DIR})

add_subdirectory("src/plugin/amulet/editor/widget/_view_3d")
