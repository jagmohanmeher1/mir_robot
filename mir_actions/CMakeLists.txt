cmake_minimum_required(VERSION 3.8)
project(mir_actions)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(mir_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)

################################################
## Declare ROS 2 actions                      ##
################################################

rosidl_generate_interfaces(${PROJECT_NAME}
  "action/MirMoveBase.action"
  DEPENDENCIES
    builtin_interfaces
    geometry_msgs
    mir_msgs
    nav_msgs
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()
