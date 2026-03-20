from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    mir_type = LaunchConfiguration('mir_type')
    tf_prefix = LaunchConfiguration('tf_prefix')
    mir_hostname = LaunchConfiguration('mir_hostname')
    disable_map = LaunchConfiguration('disable_map')

    mir_description_share = FindPackageShare('mir_description')
    urdf_xacro = PathJoinSubstitution([mir_description_share, 'urdf', 'mir.urdf.xacro'])

    # Robot state publisher with remapped TF topics
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {
                'robot_description': ParameterValue(
                    Command(['xacro ', urdf_xacro, ' mir_type:=', mir_type, ' tf_prefix:=', tf_prefix]),
                    value_type=str,
                ),
            }
        ],
        remappings=[
            ('/tf', 'tf_rss'),
            ('/tf_static', 'tf_static_rss'),
        ],
    )

    # Remove TFs that are also published by the MiR to avoid conflicts
    tf_remove_state_publisher_frames_node = Node(
        package='mir_driver',
        executable='tf_remove_child_frames.py',
        name='tf_remove_state_publisher_frames',
        output='screen',
        parameters=[
            {
                'remove_frames': [
                    'base_link',
                    'front_laser_link',
                    'back_laser_link',
                    'camera_top_link',
                    'camera_top_depth_optical_frame',
                    'camera_floor_link',
                    'camera_floor_depth_optical_frame',
                    'imu_link',
                ],
            }
        ],
        remappings=[
            ('tf_in', 'tf_rss'),
            ('tf_out', '/tf'),
            ('tf_static_in', 'tf_static_rss'),
            ('tf_static_out', '/tf_static'),
        ],
    )

    # MiR bridge node (when map is disabled)
    mir_bridge_node_disabled_map = Node(
        package='mir_driver',
        executable='mir_bridge_ros2.py',
        name='mir_bridge',
        output='screen',
        parameters=[
            {
                'hostname': mir_hostname,
                'tf_prefix': tf_prefix,
            }
        ],
        remappings=[
            ('map', 'map_mir'),
            ('map_metadata', 'map_metadata_mir'),
            ('rosout', '/rosout'),
            ('rosout_agg', '/rosout_agg'),
            ('tf', 'tf_mir'),
        ],
    )

    # Remove map -> odom TF transform when map is disabled
    tf_remove_mir_map_frame_node = Node(
        package='mir_driver',
        executable='tf_remove_child_frames.py',
        name='tf_remove_mir_map_frame',
        output='screen',
        parameters=[
            {
                'remove_frames': ['odom'],
            }
        ],
        remappings=[
            ('tf_in', 'tf_mir'),
            ('tf_out', '/tf'),
        ],
    )

    # MiR bridge node (when map is enabled)
    mir_bridge_node_enabled_map = Node(
        package='mir_driver',
        executable='mir_bridge_ros2.py',
        name='mir_bridge',
        output='screen',
        parameters=[
            {
                'hostname': mir_hostname,
                'tf_prefix': tf_prefix,
            }
        ],
        remappings=[
            ('map', '/map'),
            ('map_metadata', '/map_metadata'),
            ('rosout', '/rosout'),
            ('rosout_agg', '/rosout_agg'),
            ('tf', '/tf'),
        ],
    )

    # REP117 laser filters
    b_rep117_laser_filter_node = Node(
        package='mir_driver',
        executable='rep117_filter.py',
        name='b_rep117_laser_filter',
        output='screen',
        remappings=[
            ('scan', 'b_scan'),
            ('scan_filtered', 'b_scan_rep117'),
        ],
    )

    f_rep117_laser_filter_node = Node(
        package='mir_driver',
        executable='rep117_filter.py',
        name='f_rep117_laser_filter',
        output='screen',
        remappings=[
            ('scan', 'f_scan'),
            ('scan_filtered', 'f_scan_rep117'),
        ],
    )

    # Fake joint publisher
    fake_mir_joint_publisher_node = Node(
        package='mir_driver',
        executable='fake_mir_joint_publisher.py',
        name='fake_mir_joint_publisher',
        output='screen',
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'mir_type',
                default_value='mir_100',
                description='The MiR variant. Can be "mir_100" or "mir_250" for now.',
            ),
            DeclareLaunchArgument(
                'tf_prefix',
                default_value='',
                description='TF prefix to use for all of MiR\'s TF frames',
            ),
            DeclareLaunchArgument(
                'mir_hostname',
                default_value='192.168.12.20',
                description='Hostname or IP address of the MiR robot',
            ),
            DeclareLaunchArgument(
                'disable_map',
                default_value='false',
                description='Disable the map topic and map -> odom TF transform from the MiR',
            ),
            robot_state_publisher_node,
            tf_remove_state_publisher_frames_node,
            # Group for when map is disabled
            GroupAction(
                condition=IfCondition(disable_map),
                actions=[
                    mir_bridge_node_disabled_map,
                    tf_remove_mir_map_frame_node,
                ],
            ),
            # Group for when map is enabled
            GroupAction(
                condition=UnlessCondition(disable_map),
                actions=[
                    mir_bridge_node_enabled_map,
                ],
            ),
            b_rep117_laser_filter_node,
            f_rep117_laser_filter_node,
            fake_mir_joint_publisher_node,
        ]
    )
