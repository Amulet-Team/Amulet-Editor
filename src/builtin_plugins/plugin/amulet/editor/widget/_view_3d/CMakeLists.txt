cmake_minimum_required(VERSION 3.13)

project(view_3d LANGUAGES CXX)

# Add pybind11
find_package(pybind11 CONFIG REQUIRED)

# Add Amulet libraries
if (NOT TARGET amulet_pybind11_extensions)
    find_package(amulet_pybind11_extensions CONFIG REQUIRED)
endif()
if (NOT TARGET amulet_core)
    find_package(amulet_core CONFIG REQUIRED)
endif()
if (NOT TARGET amulet_level)
    find_package(amulet_level CONFIG REQUIRED)
endif()
if (NOT TARGET amulet_resource_pack)
    find_package(amulet_resource_pack CONFIG REQUIRED)
endif()
find_package(Qt6 REQUIRED COMPONENTS OpenGL Gui)

# Find C++ files
file(GLOB_RECURSE SOURCES LIST_DIRECTORIES false ${CMAKE_CURRENT_LIST_DIR}/*.cpp)
file(GLOB_RECURSE HEADERS LIST_DIRECTORIES false ${CMAKE_CURRENT_LIST_DIR}/*.hpp)

# Add python extension
pybind11_add_module(_view_3d)
target_link_libraries( _view_3d PRIVATE amulet_pybind11_extensions )
target_link_libraries( _view_3d PRIVATE amulet_core )
target_link_libraries( _view_3d PRIVATE amulet_level )
target_link_libraries( _view_3d PRIVATE amulet_resource_pack )
target_link_libraries( _view_3d PRIVATE Qt6::Gui )
target_link_libraries( _view_3d PRIVATE Qt6::OpenGL )
target_include_directories(_view_3d PUBLIC ${CMAKE_CURRENT_LIST_DIR})
target_compile_definitions(_view_3d PRIVATE PYBIND11_DETAILED_ERROR_MESSAGES)
target_compile_definitions(_view_3d PRIVATE PYBIND11_VERSION="${pybind11_VERSION}")
target_compile_definitions(_view_3d PRIVATE COMPILER_ID="${CMAKE_CXX_COMPILER_ID}")
target_compile_definitions(_view_3d PRIVATE COMPILER_VERSION="${CMAKE_CXX_COMPILER_VERSION}")
target_sources(_view_3d PRIVATE ${SOURCES} ${HEADERS})
foreach(FILE ${SOURCES} ${HEADERS})
    file(RELATIVE_PATH REL_PATH ${CMAKE_CURRENT_LIST_DIR} ${FILE})
    get_filename_component(GROUP ${REL_PATH} DIRECTORY)
    string(REPLACE "/" "\\" GROUP ${GROUP})
    source_group(${GROUP} FILES ${FILE})
endforeach()

if(NOT DEFINED AMULET_APP_EXT_DIR)
    set(AMULET_APP_EXT_DIR ${amulet_app_DIR})
endif()

# Install
install(TARGETS _view_3d DESTINATION ${AMULET_APP_EXT_DIR}/../../builtin_plugins/plugin/amulet/editor/widget/_view_3d/_view_3d)
