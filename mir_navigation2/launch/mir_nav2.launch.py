from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    params_file = LaunchConfiguration('params_file')
    map_file = LaunchConfiguration('map_file', default='')
    use_lifecycle_mgr = LaunchConfiguration('use_lifecycle_mgr', default='true')
    autostart = LaunchConfiguration('autostart', default='true')

    # Get Nav2 bringup launch
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('nav2_bringup'),
                'launch',
                'bringup_launch.py'
            ])
        ]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file': params_file,
            'map': map_file,
            'use_lifecycle_mgr': use_lifecycle_mgr,
            'autostart': autostart,
        }.items()
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time if true'
        ),
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('mir_navigation2'),
                'config',
                'nav2_params.yaml'
            ]),
            description='Full path to the Nav2 parameters file'
        ),
        DeclareLaunchArgument(
            'map_file',
            default_value='',
            description='Full path to map file (optional)'
        ),
        DeclareLaunchArgument(
            'use_lifecycle_mgr',
            default_value='true',
            description='Whether to launch the lifecycle manager'
        ),
        DeclareLaunchArgument(
            'autostart',
            default_value='true',
            description='Automatically startup the nav2 stack'
        ),
        nav2_bringup,
    ])
