# MiR Navigation2 Package

This package provides Nav2 configuration and launch files for the MiR robot on ROS2 Jazzy.

## Prerequisites

### 1. Install Required ROS2 Packages

Before building Nav2 from source, install these dependencies:

```bash
sudo apt update
sudo apt install -y \
  ros-jazzy-geographic-msgs \
  ros-jazzy-behaviortree-cpp-v3 \
  ros-jazzy-robot-localization \
  ros-jazzy-tf2-geometry-msgs \
  ros-jazzy-tf2-sensor-msgs \
  ros-jazzy-visualization-msgs \
  ros-jazzy-nav2-common \
  ros-jazzy-nav2-msgs
```

### 2. Build Nav2 from Source

Nav2 has been cloned into `/home/jag/ws_mir/src/navigation2`. To build it:

```bash
cd /home/jag/ws_mir
source /opt/ros/jazzy/setup.bash

# Install all Nav2 dependencies via rosdep
rosdep install --from-paths src --ignore-src -r -y

# Build Nav2 (this will take a while)
colcon build --symlink-install --packages-select nav2_common nav2_msgs nav_2d_msgs nav2_voxel_grid nav2_util nav2_costmap_2d nav2_core nav2_amcl nav2_behavior_tree nav2_lifecycle_manager nav2_map_server nav2_controller nav2_planner nav2_recoveries nav2_bt_navigator nav2_waypoint_follower nav2_dwb_controller nav2_navfn_planner nav2_bringup

# Or build everything at once
colcon build --symlink-install
```

### 3. Build This Package

```bash
cd /home/jag/ws_mir
source /opt/ros/jazzy/setup.bash
source install/setup.bash  # Source Nav2 if already built
colcon build --packages-select mir_navigation2 --symlink-install
```

## Usage

### Launch Nav2 with MiR

```bash
# Terminal 1: Start MiR driver
source /home/jag/ws_mir/install/setup.bash
ros2 launch mir_driver mir_bridge_ros2.launch.py hostname:=<your_mir_ip>

# Terminal 2: Start Nav2
source /home/jag/ws_mir/install/setup.bash
ros2 launch mir_navigation2 mir_nav2.launch.py map_file:=/path/to/your/map.yaml

# Terminal 3: RViz2 for visualization
source /home/jag/ws_mir/install/setup.bash
rviz2
```

### Launch Arguments

- `use_sim_time` (default: `false`) - Use simulation time if true
- `params_file` (default: `config/nav2_params.yaml`) - Full path to Nav2 parameters file
- `map_file` (default: `''`) - Full path to map file (optional)
- `use_lifecycle_mgr` (default: `true`) - Whether to launch the lifecycle manager
- `autostart` (default: `true`) - Automatically startup the nav2 stack

## Configuration

The Nav2 parameters are configured in `config/nav2_params.yaml`. Key settings:

- **Robot radius**: 0.5m (adjust based on your MiR variant)
- **Controller**: DWB Local Planner
- **Planner**: NavFn
- **Costmap resolution**: 0.05m
- **Laser scan topic**: `/scan`
- **Odometry topic**: `/odom`
- **Base frame**: `base_link`
- **Global frame**: `map`
- **Local frame**: `odom`

Adjust these parameters based on your specific MiR robot configuration and environment.

## Troubleshooting

### Missing Dependencies

If you see errors about missing packages, install them:

```bash
sudo apt install ros-jazzy-<package-name>
```

### Nav2 Not Found

Ensure Nav2 is built and sourced:

```bash
source /home/jag/ws_mir/install/setup.bash
ros2 pkg list | grep nav2
```

### TF Errors

Ensure your MiR driver is publishing TF frames correctly. Check:

```bash
ros2 run tf2_ros tf2_echo map base_link
```
