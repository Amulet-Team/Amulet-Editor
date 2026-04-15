cmake_minimum_required(VERSION 4.1)

project(amulet_meta)

add_definitions("/wd4251")

set(Python3_EXECUTABLE "C:/Program Files/Python314/python3.14t.exe" CACHE PATH "Path to the Python exe" FORCE)
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

set(CMAKE_INSTALL_PREFIX "_install" CACHE PATH "Directory for unused binaries" FORCE)
set(Qt6_DIR "C:/Qt/6.10.2/msvc2022_64/lib/cmake/Qt6" CACHE PATH "The path to Qt6")
set(pybind11_DIR "Amulet-Editor/.venv/Lib/site-packages/pybind11/share/cmake/pybind11" CACHE PATH "The path to pybind11")

add_subdirectory("Amulet-Test-Utils")

set(BUILD_AMULET_PYBIND11_EXTENSIONS_TESTS 1 CACHE BOOL "")
add_subdirectory("Amulet-pybind11-extensions")

add_subdirectory("Amulet-IO")

set(BUILD_AMULET_LEVELDB_TESTS 1 CACHE BOOL "")
add_subdirectory("Amulet-LevelDB")

set(BUILD_AMULET_UTILS_TESTS 1 CACHE BOOL "")
add_subdirectory("Amulet-Utils")

set(BUILD_AMULET_ZLIB_TESTS 1 CACHE BOOL "")
add_subdirectory("Amulet-zlib")

set(BUILD_AMULET_NBT_TESTS 1 CACHE BOOL "")
add_subdirectory("Amulet-NBT")

set(BUILD_AMULET_CORE_TESTS 1 CACHE BOOL "")
add_subdirectory("Amulet-Core")

set(BUILD_AMULET_GAME_TESTS 1 CACHE BOOL "")
add_subdirectory("Amulet-Game")

set(BUILD_AMULET_ANVIL_TESTS 1 CACHE BOOL "")
add_subdirectory("Amulet-Anvil")

set(BUILD_AMULET_LEVEL_TESTS 1 CACHE BOOL "")
add_subdirectory("Amulet-Level")

set(BUILD_AMULET_RESOURCE_PACK_TESTS 1 CACHE BOOL "")
add_subdirectory("Amulet-Resource-Pack")

add_subdirectory("Amulet-Editor")
