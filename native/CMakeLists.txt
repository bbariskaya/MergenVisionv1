cmake_minimum_required(VERSION 3.28 FATAL_ERROR)

project(
    mergenvision_face_core
    VERSION 0.1.0
    LANGUAGES CXX
    DESCRIPTION "MergenVision native face detection/alignment/embedding core"
)

# C++ standard.
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Enable testing/CTest.
include(CTest)

# Public include directory for consumers.
set(MERGENVISION_FACE_CORE_INCLUDE_DIR
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Native face-core library.
add_library(mergenvision_face_core
    src/version.cpp
)
add_library(mergenvision::face_core ALIAS mergenvision_face_core)

target_include_directories(mergenvision_face_core
    PUBLIC
        $<BUILD_INTERFACE:${MERGENVISION_FACE_CORE_INCLUDE_DIR}>
        $<INSTALL_INTERFACE:include>
)

# Conservative warning flags for the library target.
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang|AppleClang")
    target_compile_options(mergenvision_face_core PRIVATE
        -Wall
        -Wextra
        -Wpedantic
        -Werror=return-type
    )
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
    target_compile_options(mergenvision_face_core PRIVATE
        /W4
        /permissive-
        /WX
    )
endif()

# Smoke test executable.
add_executable(version_smoke
    tests/version_smoke.cpp
)

target_link_libraries(version_smoke PRIVATE mergenvision_face_core)

# Register with CTest.
add_test(NAME version_smoke COMMAND version_smoke)
