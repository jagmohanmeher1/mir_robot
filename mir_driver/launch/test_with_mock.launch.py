from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Launch file for testing mir_driver with mock rosbridge server."""

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_mock_server',
            default_value='true',
            description='Use mock rosbridge server for simulation',
        ),
        DeclareLaunchArgument(
            'rosbridge_port',
            default_value='9091',
            description='WebSocket port for mock server (9091 avoids clash with other rosbridge on 9090)',
        ),

        # Start mock rosbridge server
        ExecuteProcess(
            condition=IfCondition(LaunchConfiguration('use_mock_server')),
            cmd=[
                'ros2', 'run', 'mir_driver', 'mock_mir_rosbridge_server.py', '--',
                '--port', LaunchConfiguration('rosbridge_port'),
            ],
            output='screen',
            name='mock_rosbridge_server',
        ),

        # Start mir_bridge connecting to localhost
        Node(
            package='mir_driver',
            executable='mir_bridge_ros2.py',
            name='mir_bridge',
            output='screen',
            parameters=[
                {
                    'hostname': 'localhost',
                    'port': ParameterValue(LaunchConfiguration('rosbridge_port'), value_type=int),
                    'tf_prefix': '',
                }
            ],
        ),
    ])
