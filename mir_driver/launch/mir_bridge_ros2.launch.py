from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    hostname = LaunchConfiguration('hostname')
    port = LaunchConfiguration('port')
    tf_prefix = LaunchConfiguration('tf_prefix')

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'hostname',
                description='Hostname or IP address of the MiR robot (rosbridge server).',
            ),
            DeclareLaunchArgument(
                'port',
                default_value='9090',
                description='TCP port of the MiR rosbridge server.',
            ),
            DeclareLaunchArgument(
                'tf_prefix',
                default_value='',
                description='TF prefix to apply to all MiR frames.',
            ),
            Node(
                package='mir_driver',
                executable='mir_bridge_ros2.py',
                name='mir_bridge',
                output='screen',
                parameters=[
                    {
                        'hostname': hostname,
                        'port': port,
                        'tf_prefix': tf_prefix,
                    }
                ],
            ),
        ]
    )

