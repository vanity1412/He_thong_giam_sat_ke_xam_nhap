# ESP32-CAM Web Streaming Project
cmake_minimum_required(VERSION 3.16)

# Add custom components folder
set(EXTRA_COMPONENT_DIRS
    ${CMAKE_CURRENT_SOURCE_DIR}/components
)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(esp32_cam_http_stream)