## ROS 2 Jazzy: Visualizing MiR Description in RViz2

This document explains how to use the ROS 2 launch file `mir_display.launch.py` to visualize the MiR robot model from `mir_description` in RViz2, and what manual steps are needed inside RViz2.

---

## 1. Prerequisites

- ROS 2 **Jazzy** installed and sourced:

  ```bash
  source /opt/ros/jazzy/setup.bash
  ```

- The `mir_robot` workspace built and sourced (from the workspace root, e.g. `/home/jag/ws_mir`):

  ```bash
  cd /home/jag/ws_mir
  colcon build --symlink-install
  source install/setup.bash
  ```

---

## 2. Launching the MiR description in RViz2

From the workspace root:

```bash
cd /home/jag/ws_mir
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 launch mir_description mir_display.launch.py
```

This will start:

- `robot_state_publisher` (publishes TF tree based on the MiR URDF),
- `joint_state_publisher_gui` (GUI for manipulating joint states),
- `rviz2` (visualization).

### Launch arguments

- `mir_type` (default: `mir_100`)
  - MiR variant, supports at least:
    - `mir_100`
    - `mir_250`
  - Example:

    ```bash
    ros2 launch mir_description mir_display.launch.py mir_type:=mir_250
    ```

- `gui` (default: `true`)
  - Reserved for selecting GUI/non-GUI joint state publisher.

- `use_sim_time` (default: `false`)
  - Use simulation time if set to `true`.

---

## 3. RViz2: How to make the MiR model visible

The launch file currently starts RViz2 with a **blank/default configuration** (the old RViz1 config `mir_description.rviz` is not used because it references deprecated plugin names).

Follow these steps inside RViz2:

### 3.1 Set the Fixed Frame

1. In the left panel, under **Global Options**:
2. Set **Fixed Frame** to:

   ```text
   base_link
   ```

This is the root link of the MiR model (no TF prefix by default).

### 3.2 Add a Robot Model display

1. Click **Add** (bottom-left).
2. In the dialog, select **By display type**.
3. Choose:

   ```text
   rviz_default_plugins/RobotModel
   ```

4. Click **OK**.
5. In the new **RobotModel** display:
   - Ensure **Description** is:

     ```text
     robot_description
     ```

   - Leave **TF Prefix** empty.

You should now see the MiR base appear in the 3D view.

### 3.3 (Optional) Add a Grid

1. Click **Add** again.
2. Choose:

   ```text
   rviz_default_plugins/Grid
   ```

3. In the **Grid** display, you can set:
   - **Reference Frame** = `base_link`
   - Adjust cell size, color, etc. as desired.

---

## 4. Using the Joint State Publisher GUI

The launch file also starts `joint_state_publisher_gui`, which allows you to move joints interactively:

- The GUI window will show sliders for all joints in the MiR model.
- Moving the sliders updates `/joint_states`, which `robot_state_publisher` turns into TF updates.
- RViz2 will update the robot pose accordingly (if the **RobotModel** display is enabled).

If you do **not** need the GUI, you can later change the launch file (or add a launch argument) to use the non-GUI `joint_state_publisher` instead.

---

## 5. Troubleshooting

- **RViz2 starts but no robot is visible**
  - Check that:
    - **Fixed Frame** is set to `base_link`.
    - A **RobotModel** display is added and points to `robot_description`.
  - Ensure the launch is running and `robot_state_publisher` is active:

    ```bash
    ros2 node list | grep robot_state_publisher
    ```

- **Old RViz config errors (rviz/Grid, rviz/RobotModel, etc.)**
  - Caused by the legacy RViz1 config file.
  - The ROS2 launch does **not** load that config; it starts RViz2 clean.
  - You can safely ignore old `.rviz` configs and create a new one in RViz2.

- **No frames in TF tree**
  - Check that `robot_state_publisher` is running and that `robot_description` is set:

    ```bash
    ros2 param get /robot_state_publisher robot_description
    ```

  - If empty, re-run the launch ensuring `xacro` is installed and in PATH:

    ```bash
    sudo apt install ros-jazzy-xacro
    ```

---

## 6. Summary

1. Build and source the workspace.
2. Run:

   ```bash
   ros2 launch mir_description mir_display.launch.py
   ```

3. In RViz2:
   - Set **Fixed Frame** to `base_link`.
   - Add a **RobotModel** display using `robot_description`.
   - Optionally add a **Grid** display.
4. Use `joint_state_publisher_gui` to inspect joint motion and verify the MiR URDF.

