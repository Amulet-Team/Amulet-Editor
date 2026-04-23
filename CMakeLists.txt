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

add_subdirectory("src/amulet/app")
add_subdirectory("src/builtin_plugins/plugin/amulet/editor/widget/_view_3d")
