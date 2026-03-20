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
  - Fork origin: `https://github.com/jagmohanmeher1/mir_robot.git`
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
  - [x] `source install/setup.bash`
  - [x] `ros2 interface list | grep mir`

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
  - [x] `ros2 interface list | grep mir`

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
  - [x] `ros2 launch mir_description mir_display.launch.py`

**Notes**
- URDF content itself is typically ROS-version-agnostic; main changes are in launch + install.

---

### 4.4 `mir_driver`

**Goal**: Port the main driver node(s) to ROS2 (`rclcpp` / `rclpy`), publishing MiR state and accepting command topics/actions.

**Tasks**
- [x] Convert `package.xml`:
  - [x] `buildtool_depend` → `ament_cmake`
  - [x] `roscpp` / `rospy` → `rclcpp` / `rclpy` (partially: rclpy added, ROS1 deps still present for compatibility)
  - [x] Depend on `mir_msgs`, `mir_actions`, `geometry_msgs`, `nav_msgs`, `sensor_msgs`, `tf2`, `tf2_ros` (partially: ROS1 deps still present for bridge node).
- [x] Rewrite `CMakeLists.txt`:
  - [x] Replace `catkin_package()` with `ament_package()`.
  - [x] Replace `find_package(catkin ...)` with `find_package(ament_cmake REQUIRED)` (ROS2 deps to be added when code is ported).
  - [ ] Use `add_executable()` + `ament_target_dependencies()` for each node (once C++ nodes exist, if needed).
  - [x] Install Python nodes to `lib/${PROJECT_NAME}` and launch files to `share/${PROJECT_NAME}`.
- [x] Port C++/Python nodes:
  - [x] Replace `ros::NodeHandle` → `rclcpp::Node` subclasses (N/A: no C++ nodes).
  - [x] Replace `ros::Publisher`/`Subscriber` → `create_publisher`/`create_subscription` (All Python nodes ported: `rep117_filter.py`, `fake_mir_joint_publisher.py`, `tf_remove_child_frames.py`, `mir_bridge_ros2.py`).
  - [x] Replace `ros::Rate` loops with ROS2 timers (ported nodes use rclpy timers).
  - [x] Replace tf1 (`tf`) with `tf2` + `tf2_ros` (ported nodes use tf2_ros).
  - [x] Replace `actionlib` with ROS2 actions (action messages bridged via topics, no actionlib client needed).
- [x] Convert launch files:
  - [x] ROS1 `.launch` → ROS2 Python `.launch.py` (`mir.launch.py` and `mir_bridge_ros2.launch.py` created).
  - [x] Use `launch_ros.actions.Node` (in both launch files).
  - [x] Old ROS1 launch file (`mir.launch`) kept for reference but ROS2 version (`mir.launch.py`) is primary.
- [x] Testing:
  - [x] `colcon build --packages-select mir_driver`
  - [x] Smoke test: `ros2 launch mir_driver test_with_mock.launch.py` (mock rosbridge + `mir_bridge_ros2`; default port **9091**).
  - [ ] Run core driver launch against **real robot** (or full simulation once `mir_gazebo` exists).

**Notes**
- This is one of the heaviest parts of the migration; we will likely create several commits and update this plan as we go.
- **`mir_compat_msgs`** (see §4.4.1) supplies ROS1-shaped `dynamic_reconfigure` + `move_base` messages not shipped for Jazzy; the bridge uses **`rosidl_runtime_py`** for dict ↔ message conversion and **`rcl_interfaces/msg/Log`** for `/rosout`-style topics (not `rosgraph_msgs/msg/Log`).
- Install the **`mir_driver`** Python package with **`ament_python_install_package`** so `from mir_driver import rosbridge` works at runtime.
- **`websocket-client`** (newer API): `WebSocketApp` callbacks must accept `(ws, …)`; see `src/mir_driver/rosbridge.py`.

---

### 4.4.1 `mir_compat_msgs` (new)

**Goal**: Provide message definitions that match **ROS 1** shapes still used across the MiR / rosbridge JSON bridge, but which are **not** available as standard ROS 2 Jazzy packages (`dynamic_reconfigure`, `move_base_msgs`).

**Tasks**
- [x] Add `mir_compat_msgs` with `ament_cmake` + `rosidl_generate_interfaces`.
- [x] Port **dynamic_reconfigure**-compatible messages: `Config`, `ConfigDescription`, and dependencies (`BoolParameter`, `IntParameter`, `StrParameter`, `DoubleParameter`, `Group`, `GroupState`, `ParamDescription`).
- [x] Port **move_base**-shaped action wrapper messages: `MoveBaseGoal`, `MoveBaseFeedback`, `MoveBaseResult`, `MoveBaseActionGoal`, `MoveBaseActionFeedback`, `MoveBaseActionResult` (depends on `actionlib_msgs`, `geometry_msgs`, `std_msgs`).
- [x] Wire `mir_driver` / `mir_bridge_ros2.py` to import from `mir_compat_msgs` and `mir_actions.action.MirMoveBase` (not `mir_actions.msg`).

**Notes**
- If upstream later ships ROS 2 equivalents, this package can shrink or be dropped.
- **Build tip (CMake / NumPy)**: if `rosidl_generator_py` fails to find NumPy for Python 3.12, pass e.g. `-DPython3_NumPy_INCLUDE_DIR=/usr/lib/python3/dist-packages/numpy/core/include` (see progress log).

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
- **Branch state (2026-03)**: Legacy **ROS 1** packages **`mir_gazebo`**, **`mir_navigation`**, **`mir_dwb_critics`**, and the **`mir_robot` metapackage** have been **removed from this branch** until they are reintroduced as ROS 2 ports. Do not expect Gazebo/nav demos from this tree until those packages are restored.

---

### 4.6 `mir_navigation` / `mir_dwb_critics` / `mir_navigation2`

**Goal**: Replace/upgrade the ROS1 navigation stack (`move_base`) to **Nav2** on ROS2.

**Tasks**
- [ ] Identify configs (costmaps, planners, local controllers) in ROS1 (reference upstream `noetic-devel` or restore removed `mir_navigation` from git history).
- [ ] Map them to Nav2 equivalents (BT Navigator, DWB, etc.).
- [x] **Parallel track**: `mir_navigation2` package added in workspace (Nav2 params + `mir_nav2.launch.py`); full integration testing TBD.
- [ ] If `mir_dwb_critics` is restored:
  - [ ] Port custom critics/plugins to ROS2 plugin API.
  - [ ] Update CMake and plugin.xml for ROS2.

**Notes**
- This will likely come after the driver and basic simulation work.
- **`mir_dwb_critics`**: removed from branch pending ROS 2 port (same as §4.5).

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
  - [x] Build succeeds for migrated packages in this branch (`mir_msgs`, `mir_actions`, `mir_description`, `sdc21x0`, `mir_compat_msgs`, `mir_driver`, …).
- [ ] Run basic bringup:
  - [x] Description + robot_state_publisher in RViz2 (`mir_display.launch.py`).
  - [x] Driver bridge smoke test with mock rosbridge (`test_with_mock.launch.py`).
  - [ ] Driver node connects to **real** MiR (or full simulation once `mir_gazebo` exists) and publishes odom, tf, etc.
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

- **[2026-01-21]**: Migrated `sdc21x0` to ROS2 Jazzy.
  - Converted `package.xml` to format 3 with `ament_cmake` + `rosidl_default_generators`.
  - Replaced catkin-based `CMakeLists.txt` with `rosidl_generate_interfaces()` for messages and services.
  - Fixed ROS2 naming conventions: `digitalPort` → `digital_port` in `Flags.srv`, `Header` → `std_msgs/Header` in `StampedEncoders.msg`.
  - Verified `colcon build --packages-select sdc21x0` succeeds on ROS2 Jazzy.

- **[2026-01-21]**: Migrated `mir_driver` Python nodes to ROS2 Jazzy.
  - Converted `package.xml` to format 3 with `ament_cmake`.
  - Replaced catkin-based `CMakeLists.txt` with ament version installing Python nodes and launch files.
  - Ported helper nodes from `rospy` to `rclpy`: `fake_mir_joint_publisher.py`, `rep117_filter.py`, `tf_remove_child_frames.py`.
  - Created new ROS2 bridge node `mir_bridge_ros2.py` and launch file `mir_bridge_ros2.launch.py`.
  - Verified `colcon build --packages-select mir_driver` succeeds on ROS2 Jazzy.

- **[2026-01-21]**: Set up Nav2 from source and created `mir_navigation2` package.
  - Cloned Navigation2 repository (jazzy branch) into `/home/jag/ws_mir/src/navigation2`.
  - Created new `mir_navigation2` package with Nav2 configuration and launch files.
  - Created `config/nav2_params.yaml` with DWB controller, NavFn planner, and costmap configurations for MiR.
  - Created `launch/mir_nav2.launch.py` that integrates with `nav2_bringup`.
  - Created build script `build_nav2.sh` to build Nav2 packages in correct dependency order.
  - Created README.md with installation and usage instructions.
  - **Note**: Nav2 packages need to be built before `mir_navigation2` can be used. See `build_nav2.sh` and `mir_navigation2/README.md` for instructions.

- **[2026-01-26]**: Updated migration status and verified completed packages.
  - Verified `mir_msgs`, `mir_actions`, and `mir_description` are fully migrated and tested.
  - Confirmed `mir_driver` Python nodes (`rep117_filter.py`, `fake_mir_joint_publisher.py`, `tf_remove_child_frames.py`, `mir_bridge_ros2.py`) have been ported to ROS2.
  - Noted that `mir_bridge.py` still uses ROS1 (`rospy`) and `mir.launch` is still a ROS1 launch file.
  - Confirmed no C++ nodes exist in `mir_driver` package.
  - Updated checklists to reflect current progress.

- **[2026-01-26]**: Completed `mir_driver` migration to ROS2 Jazzy.
  - Completed port of `mir_bridge.py` to `mir_bridge_ros2.py` with all topics from ROS1 version.
  - Added all missing PUB_TOPICS and SUB_TOPICS from original ROS1 implementation.
  - Fixed `cmd_vel` topic handling with proper Twist to TwistStamped conversion using node's clock.
  - Implemented `tf_static` latching using transient_local QoS profile for ROS2 compatibility.
  - Added helper function `get_message_type_string()` for ROS2 message type conversion.
  - Updated `package.xml` to remove ROS1 dependencies (`rospy`, `tf`, `actionlib`) and keep only ROS2 equivalents.
  - Updated `CMakeLists.txt` to install `mir_bridge_ros2.py` instead of `mir_bridge.py`.
  - Converted `mir.launch` to ROS2 Python launch file `mir.launch.py` with all functionality preserved.
  - All Python nodes now use `rclpy` instead of `rospy`.

- **[2026-03-20]**: `mir_compat_msgs`, `mir_driver` runtime fixes, mock launch smoke test.
  - Added **`mir_compat_msgs`**: ROS1-shaped `dynamic_reconfigure` + `move_base` messages for Jazzy (no standard `move_base_msgs` / `dynamic_reconfigure` packages).
  - **`mir_driver`**: `ament_python_install_package(mir_driver)` so `from mir_driver import rosbridge` works; depend on **`mir_compat_msgs`**, **`rosidl_runtime_py`**, **`rcl_interfaces`** (for `Log`); fix **`rclpy` logging** (no printf-style `warn(a,b,c)`).
  - **`rosbridge.py`**: Update **`websocket-client`** `WebSocketApp` callbacks to `(ws, …)` signature.
  - **`test_with_mock.launch.py`**: Default **`rosbridge_port:=9091`** (avoids clash with other rosbridge on 9090); `ros2 run … -- --port …`; `ParameterValue(..., int)` for node param.
  - **`mock_mir_rosbridge_server.py`**: `argparse --port` (default 9091).
  - Verified: `ros2 launch mir_driver test_with_mock.launch.py` connects and finishes node setup (warnings expected: mock has no MiR topics).
  - Documented: ROS1-only packages (**`mir_gazebo`**, **`mir_navigation`**, **`mir_dwb_critics`**, **`mir_robot` metapackage**) removed from this branch until ROS2 ports land.

_(Add new entries below as work progresses.)_

---

## 9. Current Status Summary & Next Steps

### Completed packages (this branch)

- **mir_msgs**: ROS 2 Jazzy (`ament_cmake` + `rosidl`)
- **mir_actions**: ROS 2 Jazzy (`ament_cmake` + `rosidl`)
- **mir_description**: ROS 2 Jazzy (URDF, `mir_display.launch.py`)
- **sdc21x0**: ROS 2 Jazzy (`ament_cmake` + `rosidl`)
- **mir_compat_msgs**: ROS 1–shaped compat messages for the bridge (`dynamic_reconfigure` + `move_base` layouts)
- **mir_driver**: ROS 2 Python nodes + `mir_bridge_ros2.py`; mock launch smoke test OK
- **mir_navigation2**: Nav2-oriented config/launch (full stack test TBD; lives in this repo / workspace)

### In progress / next

1. **mir_driver**
   - [x] Mock / `test_with_mock.launch.py` smoke test
   - [ ] Real robot: `ros2 launch mir_driver mir.launch.py` / `mir_bridge_ros2.launch.py`

2. **Simulation (§4.5)**
   - [ ] Re-add **`mir_gazebo`** (or new pkg) as ROS 2 + Gazebo Harmonic / gz
   - [ ] Spawn `mir_description` + bridge or sim driver

3. **Navigation**
   - [ ] Exercise **`mir_navigation2`** against robot or sim
   - [ ] Re-port **`mir_dwb_critics`** if still desired for DWB

4. **CI**
   - [ ] Replace / extend `.github/workflows/github-actions.yml` for **Jazzy + `colcon`** (current workflow targets **Noetic + catkin** only)

### Recommended priority

1. Real-robot bringup for `mir_bridge_ros2`
2. ROS 2 `mir_gazebo` (or gz) + maps
3. Nav2 integration tests
4. Jazzy CI job
