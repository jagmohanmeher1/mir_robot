cmake_minimum_required(VERSION 3.8)
project(mir_driver)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

#############
## Install ##
#############

# Install Python nodes (ROS2 ported)
install(
  PROGRAMS
    nodes/fake_mir_joint_publisher.py
    nodes/mir_bridge_ros2.py
    nodes/mock_mir_rosbridge_server.py
    nodes/rep117_filter.py
    nodes/tf_remove_child_frames.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files
install(
  DIRECTORY
    launch
  DESTINATION share/${PROJECT_NAME}
)

# Install Python module (src/mir_driver) so imports like
# `from mir_driver import rosbridge` work at runtime.
ament_python_install_package(${PROJECT_NAME} PACKAGE_DIR src/${PROJECT_NAME})

ament_package()
