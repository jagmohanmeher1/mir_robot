cmake_minimum_required(VERSION 3.8)
project(mir_compat_msgs)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

find_package(actionlib_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/BoolParameter.msg"
  "msg/IntParameter.msg"
  "msg/StrParameter.msg"
  "msg/DoubleParameter.msg"
  "msg/GroupState.msg"
  "msg/ParamDescription.msg"
  "msg/Group.msg"
  "msg/Config.msg"
  "msg/ConfigDescription.msg"
  "msg/MoveBaseGoal.msg"
  "msg/MoveBaseFeedback.msg"
  "msg/MoveBaseResult.msg"
  "msg/MoveBaseActionGoal.msg"
  "msg/MoveBaseActionFeedback.msg"
  "msg/MoveBaseActionResult.msg"
  DEPENDENCIES
    actionlib_msgs
    geometry_msgs
    std_msgs
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()
