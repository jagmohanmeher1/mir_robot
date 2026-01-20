## ROS2 Jazzy Migration Plan for `mir_robot`

This document tracks the detailed plan and progress for migrating the `mir_robot` stack from **ROS1/catkin** to **ROS2 Jazzy/ament**.  
We will **update this file with every commit** as we migrate packages and add tests.

---

## 1. Goals

- **Primary goal**: Provide a fully working **ROS2 Jazzy** version of `mir_robot` (MiR 100/200/250/500, etc.) using **ament** and `colcon`.
- **Secondary goals**:
  - Keep the **package structure recognizable** to existing `mir_robot` users.
  - Provide **simulation (Gazebo / gz)** and **navigation (Nav2)** examples.
  - Make it easy to **mount and integrate a UR arm** (UR5e, etc.) on top of the MiR base.

---

## 2. Workspace and Branch Setup

- ROS2 workspace: `/home/jag/ws_mir`
- Source folder: `/home/jag/ws_mir/src`
- Forked repo: `/home/jag/ws_mir/src/mir_robot`
- Git workflow:
  - Upstream: `https://github.com/DFKI-NI/mir_robot.git`
  - Fork origin: `https://github.com/<your-username>/mir_robot.git`
  - Working branch for ROS2: **`ros2-jazzy-migration`**

> With each logical step (package migrated / major feature added), we will:
> - Update this file (checklists, notes).
> - Commit with a clear message (e.g. `Migrate mir_msgs to ROS2 Jazzy (ament_cmake)`).

---

## 3. High-Level Migration Strategy

We will migrate **incrementally**, package by package, in a dependency-aware order:

1. **Core interfaces**
   - `mir_msgs` (messages)
   - `mir_actions` (actions), if present
2. **Description & simulation**
   - `mir_description` (URDF/Xacro, meshes)
   - `mir_gazebo` / `mir_simulation` (if present)
3. **Runtime**
   - `mir_driver` (C++/Python nodes)
   - `mir_navigation` (Nav stack configs)
   - `mir_dwb_critics` (custom Nav2 plugins), if present
4. **Integration & examples**
   - Unified bringup launch files
   - Example navigation + (optionally) UR integration

At each stage:
- Ensure **builds with `colcon`** on ROS2 Jazzy.
- Provide at least a **basic launch file** to demonstrate functionality.

---

## 4. Package-by-Package Plan & Checklists

### 4.1 `mir_msgs`

**Goal**: Provide all MiR message definitions as a ROS2 interface package using `ament_cmake` + `rosidl`.

**Tasks**
- [x] Convert `package.xml` to **format 3** with `ament_cmake` and `rosidl_default_generators`.
- [x] Replace ROS1 dependencies:
  - [x] `message_generation` → `rosidl_default_generators`
  - [x] `message_runtime` → `rosidl_default_runtime`
- [x] Rewrite `CMakeLists.txt`:
  - [x] Use `find_package(ament_cmake REQUIRED)` and `find_package(rosidl_default_generators REQUIRED)`.
  - [x] Use `rosidl_generate_interfaces()` for `.msg` / `.srv` / `.action`.
  - [x] Add `ament_export_dependencies(rosidl_default_runtime)`.
  - [x] Call `ament_package()` at the end.
- [x] Verify that generated interfaces appear:
  - [x] `colcon build --packages-select mir_msgs`
  - [ ] `source install/setup.bash`
  - [ ] `ros2 interface list | grep mir`

**Notes**
- Keep message names and fields identical where possible to ease migration from ROS1.

---

### 4.2 `mir_actions` (if present)

**Goal**: Port MiR action definitions (move base, etc.) to ROS2 action interfaces.

**Tasks**
- [x] Convert `package.xml` to format 3 with `ament_cmake` + `rosidl_default_generators`.
- [x] Update `CMakeLists.txt` with `rosidl_generate_interfaces()` for `.action` files.
- [x] Ensure dependencies (e.g. `builtin_interfaces`, `geometry_msgs`, `nav_msgs`, `mir_msgs`) are declared.
- [x] Build and verify:
  - [x] `colcon build --packages-select mir_actions`
  - [ ] `ros2 interface list | grep mir`

**Notes**
- ROS2 actions replace `actionlib` APIs; consumers must use `rclcpp_action` / `rclpy` action clients/servers.

---

### 4.3 `mir_description`

**Goal**: Make all MiR URDF/Xacro/meshes available in a ROS2-friendly description package.

**Tasks**
- [x] Convert `package.xml` to format 3 with `ament_cmake`.
- [x] Update `CMakeLists.txt`:
  - [x] Install `urdf`, `xacro`, `meshes`, `config` directories using `install(DIRECTORY ...)`.
  - [x] Add `ament_package()`.
- [x] Add/convert a minimal ROS2 launch file for visualization:
  - [x] `mir_display.launch.py` (robot_state_publisher + joint_state_publisher + RViz).
- [x] Test:
  - [x] `colcon build --packages-select mir_description`
  - [ ] `ros2 launch mir_description mir_display.launch.py`

**Notes**
- URDF content itself is typically ROS-version-agnostic; main changes are in launch + install.

---

### 4.4 `mir_driver`

**Goal**: Port the main driver node(s) to ROS2 (`rclcpp` / `rclpy`), publishing MiR state and accepting command topics/actions.

**Tasks**
- [ ] Convert `package.xml`:
  - [ ] `buildtool_depend` → `ament_cmake`
  - [ ] `roscpp` / `rospy` → `rclcpp` / `rclpy`
  - [ ] Depend on `mir_msgs`, `mir_actions`, `geometry_msgs`, `nav_msgs`, `sensor_msgs`, `tf2`, `tf2_ros`.
- [ ] Rewrite `CMakeLists.txt`:
  - [ ] Replace `catkin_package()` with `ament_package()`.
  - [ ] Replace `find_package(catkin ...)` with `find_package(ament_cmake REQUIRED)` and individual `find_package(...)` for ROS2 deps.
  - [ ] Use `add_executable()` + `ament_target_dependencies()` for each node.
  - [ ] Install executables to `lib/${PROJECT_NAME}`.
- [ ] Port C++/Python nodes:
  - [ ] Replace `ros::NodeHandle` → `rclcpp::Node` subclasses.
  - [ ] Replace `ros::Publisher`/`Subscriber` → `create_publisher`/`create_subscription`.
  - [ ] Replace `ros::Rate` loops with ROS2 timers.
  - [ ] Replace tf1 (`tf`) with `tf2` + `tf2_ros`.
  - [ ] Replace `actionlib` with ROS2 actions (`rclcpp_action`).
- [ ] Convert launch files:
  - [ ] ROS1 `.launch` → ROS2 Python `.launch.py`.
  - [ ] Use `launch_ros.actions.Node`.
- [ ] Testing:
  - [ ] `colcon build --packages-select mir_driver`
  - [ ] Run core driver launch (real robot or simulation).

**Notes**
- This is one of the heaviest parts of the migration; we will likely create several commits and update this plan as we go.

---

### 4.5 `mir_gazebo` / simulation packages

**Goal**: Provide a working ROS2-based simulation (preferably with **Gazebo Harmonic / gz** as recommended for Jazzy).

**Tasks**
- [ ] Assess current Gazebo integration (Classic vs Ignition).
- [ ] Update plugins and launch files to ROS2 equivalents:
  - [ ] Use `gazebo_ros` / `gz_ros2_control` as appropriate.
- [ ] Expose a `mir_gazebo.launch.py` that:
  - [ ] Spawns MiR robot using `mir_description` URDF.
  - [ ] Starts `mir_driver` in simulation mode.
  - [ ] Optionally loads Nav2 stack.

**Notes**
- Jazzy favors Gazebo Harmonic; Classic is deprecated. We may keep a Classic path only if needed.

---

### 4.6 `mir_navigation` / `mir_dwb_critics`

**Goal**: Replace/upgrade the ROS1 navigation stack (`move_base`) to **Nav2** on ROS2.

**Tasks**
- [ ] Identify configs (costmaps, planners, local controllers) in ROS1.
- [ ] Map them to Nav2 equivalents (BT Navigator, DWB, etc.).
- [ ] Convert navigation launch files to ROS2 (`nav2_bringup` style).
- [ ] If `mir_dwb_critics` exists:
  - [ ] Port custom critics/plugins to ROS2 plugin API.
  - [ ] Update CMake and plugin.xml for ROS2.

**Notes**
- This will likely come after the driver and basic simulation work.

---

## 5. Integration with UR (UR5e on MiR) – Future Work

Once the core `mir_robot` stack is stable on ROS2 Jazzy, we plan to:

- [ ] Create a separate package (e.g. `mir_ur5e_mobile_manipulator`) that:
  - [ ] Includes MiR base (from `mir_description`) and UR5e arm (from UR ROS2 driver description).
  - [ ] Defines a fixed joint between MiR mounting plate and UR base link.
  - [ ] Provides `ros2_control` configuration for both base and arm.
  - [ ] Integrates with MoveIt2 for manipulation and Nav2 for base navigation.

This will likely **not** be part of the first PR to upstream `mir_robot`, but will live in a separate repo or branch.

---

## 6. Testing & CI Plan

**Local testing**
- [ ] `colcon build` on Ubuntu 24.04 with ROS2 Jazzy:
  - [ ] Build succeeds for all migrated packages.
- [ ] Run basic bringup:
  - [ ] Description + robot_state_publisher in RViz2.
  - [ ] Driver node connects to MiR (or simulation) and publishes odom, tf, etc.
  - [ ] Simple teleop / navigation demo (later).

**CI (future)**
- [ ] Add GitHub Actions workflow (e.g. `ros2_jazzy_build.yml`) to:
  - [ ] Build `mir_robot` on ubuntu-24.04 with ROS2 Jazzy.
  - [ ] Run basic tests (e.g. linting, unit tests if available).

---

## 7. PR Strategy for Upstream

When the migration is stable, we plan to:

- [ ] Open an **issue** on upstream `DFKI-NI/mir_robot` describing:
  - [ ] Motivation for ROS2 Jazzy support.
  - [ ] Scope of changes.
  - [ ] Proposed branch structure (e.g. keep ROS1 on `noetic-devel`, ROS2 on `ros2-jazzy`).
- [ ] Submit one or more **pull requests**:
  - [ ] Preferably split into logical chunks (e.g. interfaces, description, driver, navigation).
  - [ ] Each PR will reference this plan and update status checklists.

---

## 8. Progress Log

We will update this log with **each commit** touching the migration.

- **[YYYY-MM-DD]**: Initial plan created in `ROS2_MIGRATION_PLAN.md`.
  - Forked `mir_robot` into `/home/jag/ws_mir/src/mir_robot`.
  - Created `ros2-jazzy-migration` branch.
  - Wrote initial migration strategy and package checklists.

- **[2026-01-20]**: Migrated `mir_msgs` to ROS2 Jazzy.
  - Converted `package.xml` to format 3 with `ament_cmake` + `rosidl_default_generators`.
  - Replaced ROS1 message generation/runtime dependencies with `rosidl_default_*`.
  - Replaced catkin-based `CMakeLists.txt` with `rosidl_generate_interfaces(...)` + `ament_package()`.
  - Updated message definitions to ROS2 naming/type rules (fully-qualified `std_msgs/Header`, `builtin_interfaces/Time`, `builtin_interfaces/Duration`, lower_snake_case fields).
  - Verified `colcon build --packages-select mir_msgs` succeeds on ROS2 Jazzy.

- **[2026-01-20]**: Migrated `mir_actions` to ROS2 Jazzy.
  - Converted `package.xml` to format 3 with `ament_cmake` + `rosidl_default_generators`.
  - Replaced catkin-based `CMakeLists.txt` with `rosidl_generate_interfaces(action/MirMoveBase.action, ...)` + `ament_package()`.
  - Declared ROS2 dependencies on `geometry_msgs`, `mir_msgs`, `nav_msgs`, and `builtin_interfaces`.
  - Verified `colcon build --packages-select mir_actions` succeeds on ROS2 Jazzy.

- **[2026-01-20]**: Migrated `mir_description` to ROS2 Jazzy (build-only).
  - Converted `package.xml` from catkin format 2 to format 3 with `ament_cmake`.
  - Replaced catkin-based `CMakeLists.txt` with ament version installing `config`, `launch`, `meshes`, `rviz`, and `urdf` into `share/${PROJECT_NAME}`.
  - Verified `colcon build --packages-select mir_description` succeeds on ROS2 Jazzy.

_(Add new entries below as work progresses.)_

