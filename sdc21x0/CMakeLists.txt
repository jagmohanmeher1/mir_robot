cmake_minimum_required(VERSION 3.8)
project(sdc21x0)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)

################################################
## Declare ROS 2 messages and services        ##
################################################

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Encoders.msg"
  "msg/MotorCurrents.msg"
  "msg/StampedEncoders.msg"
  "srv/Flags.srv"
  DEPENDENCIES
    builtin_interfaces
    std_msgs
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()
