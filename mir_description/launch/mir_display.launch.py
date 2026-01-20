from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    mir_type = LaunchConfiguration("mir_type")
    gui = LaunchConfiguration("gui")
    use_sim_time = LaunchConfiguration("use_sim_time")

    mir_description_share = FindPackageShare("mir_description")

    urdf_xacro = PathJoinSubstitution(
        [mir_description_share, "urdf", "mir.urdf.xacro"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "mir_type",
                default_value="mir_100",
                description="MiR variant (e.g. 'mir_100' or 'mir_250').",
            ),
            DeclareLaunchArgument(
                "gui",
                default_value="true",
                description="Use joint_state_publisher_gui if true, otherwise joint_state_publisher.",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
                description="Use simulation time if true.",
            ),
            # robot_state_publisher with xacro-expanded robot_description
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "robot_description": ParameterValue(
                            Command(
                                [
                                    "xacro ",
                                    urdf_xacro,
                                    " mir_type:=",
                                    mir_type,
                                    " tf_prefix:=",
                                    "",
                                ]
                            ),
                            value_type=str,
                        ),
                    }
                ],
            ),
            # joint state publisher (GUI or non-GUI)
            Node(
                condition=None,
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
                name="joint_state_publisher_gui",
                output="screen",
                # Only start GUI node when gui:=true
                parameters=[{"use_sim_time": use_sim_time}],
                arguments=[],
            ),
            # Non-GUI joint_state_publisher can be started manually if needed
            # Node(
            #     package="joint_state_publisher",
            #     executable="joint_state_publisher",
            #     name="joint_state_publisher",
            #     output="screen",
            #     parameters=[{"use_sim_time": use_sim_time}],
            # ),
            # RViz2 for visualization
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                output="screen",
                # Start RViz2 with default configuration; old RViz1 config
                # (`mir_description.rviz`) uses deprecated plugin class names.
                arguments=[],
            ),
        ]
    )

