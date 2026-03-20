#!/usr/bin/env python3
# Copyright (c) 2018-2022, Martin Günther (DFKI GmbH) and contributors
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the copyright holder nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Author: Martin Günther
# ROS 2 port: Jazzy, rclpy-based

import copy
import sys
from collections import OrderedDict
from collections.abc import Iterable

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
from rosidl_runtime_py.convert import message_to_ordereddict
from rosidl_runtime_py.set_message import set_message_fields

from mir_driver import rosbridge

from actionlib_msgs.msg import GoalID, GoalStatusArray
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus
from geometry_msgs.msg import (
    Pose,
    PoseStamped,
    PoseWithCovarianceStamped,
    PolygonStamped,
    Twist,
)
from mir_actions.action import MirMoveBase
from mir_compat_msgs.msg import (
    Config,
    ConfigDescription,
    MoveBaseActionFeedback,
    MoveBaseActionGoal,
    MoveBaseActionResult,
    MoveBaseGoal,
)
from mir_msgs.msg import LocalMapStat, PlanSegments, RobotMode, RobotState
from nav_msgs.msg import (
    GridCells,
    MapMetaData,
    OccupancyGrid,
    Odometry,
    Path,
)
from rcl_interfaces.msg import Log
from sdc21x0.msg import MotorCurrents  # requires sdc21x0 port/availability
from sensor_msgs.msg import Imu, LaserScan, PointCloud2, Range
from std_msgs.msg import Float64, Header, String
from tf2_msgs.msg import TFMessage
from visualization_msgs.msg import Marker


tf_prefix = ''
static_transforms = OrderedDict()


def get_message_type_string(msg_class):
    """Get ROS2 message type string from message class."""
    # Get the module path (e.g., 'geometry_msgs.msg')
    module = msg_class.__module__
    # Get the class name (e.g., 'Twist')
    class_name = msg_class.__name__
    # Construct type string (e.g., 'geometry_msgs/msg/Twist')
    # Note: message_converter expects format like 'geometry_msgs/Twist' (without /msg/)
    if '.msg' in module:
        package = module.split('.msg')[0]
        return f'{package}/{class_name}'
    return f'{module}/{class_name}'


def convert_dictionary_to_ros_message(msg_class, msg_dict):
    """ROS2-native dict -> message conversion."""
    msg = msg_class()
    set_message_fields(msg, msg_dict)
    return msg


def convert_ros_message_to_dictionary(msg):
    """ROS2-native message -> dict conversion."""
    return dict(message_to_ordereddict(msg))


class TopicConfig:
    def __init__(self, topic, topic_type, latch=False, dict_filter=None):
        self.topic = topic
        self.topic_type = topic_type
        self.latch = latch
        self.dict_filter = dict_filter


def _move_base_goal_dict_filter(msg_dict):
    """Force MirMoveBase goal into GLOBAL_MOVE config."""
    filtered_msg_dict = copy.deepcopy(msg_dict)
    filtered_msg_dict['goal']['move_task'] = MirMoveBase.Goal.GLOBAL_MOVE
    filtered_msg_dict['goal']['goal_dist_threshold'] = 0.25
    filtered_msg_dict['goal']['clear_costmaps'] = True
    return filtered_msg_dict


def _move_base_feedback_dict_filter(msg_dict):
    """Drop feedback fields not present in MoveBaseFeedback."""
    filtered_msg_dict = copy.deepcopy(msg_dict)
    try:
        slots = MoveBaseActionFeedback().feedback.__slots__
        filtered_msg_dict['feedback'] = {key: msg_dict['feedback'][key] for key in slots}
    except Exception:
        pass
    return filtered_msg_dict


def _move_base_result_dict_filter(msg_dict):
    """Drop result fields not present in MoveBaseResult."""
    filtered_msg_dict = copy.deepcopy(msg_dict)
    try:
        slots = MoveBaseActionResult().result.__slots__
        filtered_msg_dict['result'] = {key: msg_dict['result'][key] for key in slots}
    except Exception:
        pass
    return filtered_msg_dict


def _tf_dict_filter(msg_dict):
    """Prepend tf_prefix to child_frame_id."""
    filtered_msg_dict = copy.deepcopy(msg_dict)
    for transform in filtered_msg_dict['transforms']:
        transform['child_frame_id'] = tf_prefix + '/' + transform['child_frame_id'].strip('/')
    return filtered_msg_dict


def _prepend_tf_prefix_dict_filter(msg_dict):
    if not isinstance(msg_dict, dict):
        return msg_dict
    for key, value in msg_dict.items():
        if key == 'header':
            try:
                frame_id = value['frame_id'].strip('/')
                if frame_id != 'map':
                    value['frame_id'] = (tf_prefix + '/' + frame_id).strip('/')
                else:
                    value['frame_id'] = frame_id
            except (TypeError, KeyError):
                pass
        elif isinstance(value, dict):
            _prepend_tf_prefix_dict_filter(value)
        elif isinstance(value, Iterable):
            for item in value:
                _prepend_tf_prefix_dict_filter(item)
    return msg_dict


def _remove_tf_prefix_dict_filter(msg_dict):
    if not isinstance(msg_dict, dict):
        return msg_dict
    for key, value in msg_dict.items():
        if key == 'header':
            try:
                s = value['frame_id'].strip('/')
                if s.find(tf_prefix) == 0:
                    value['frame_id'] = (s[len(tf_prefix):]).strip('/')
            except (TypeError, KeyError):
                pass
        elif isinstance(value, dict):
            _remove_tf_prefix_dict_filter(value)
        elif isinstance(value, Iterable):
            for item in value:
                _remove_tf_prefix_dict_filter(item)
    return msg_dict


def _cmd_vel_dict_filter_factory(node):
    """
    Create a cmd_vel filter function that uses the node's clock.
    """
    def _cmd_vel_dict_filter(msg_dict):
        """
        Convert Twist to TwistStamped.

        Convert a geometry_msgs/Twist message dict (as sent from the ROS side) to
        a geometry_msgs/TwistStamped message dict (as expected by the MiR on
        software version >=2.7).
        """
        # Get current time for header
        now = node.get_clock().now()
        header_dict = {
            'frame_id': '',
            'stamp': {
                'sec': now.nanoseconds // 1_000_000_000,
                'nanosec': now.nanoseconds % 1_000_000_000,
            }
        }
        filtered_msg_dict = {
            'header': header_dict,
            'twist': copy.deepcopy(msg_dict),
        }
        return filtered_msg_dict
    return _cmd_vel_dict_filter


def _tf_static_dict_filter(msg_dict):
    """
    Cache tf_static messages (simulate latching).

    The tf_static topic needs special handling. Publishers on tf_static are *latched*, which means that the ROS master
    caches the last message that was sent by each publisher on that topic, and will forward it to new subscribers.
    However, since the mir_driver node appears to the ROS master as a single node with a single publisher on tf_static,
    and there are multiple actual publishers hiding behind it on the MiR side, only one of those messages will be
    cached. Therefore, we need to implement the caching ourselves and make sure that we always publish the full set of
    transforms as a single message.
    """
    global static_transforms

    # prepend tf_prefix
    filtered_msg_dict = _tf_dict_filter(msg_dict)

    # Process the incoming transforms, merge them with our cache.
    for transform in filtered_msg_dict['transforms']:
        key = transform['child_frame_id']
        static_transforms[key] = transform

    # Return the cached messages.
    filtered_msg_dict['transforms'] = list(static_transforms.values())
    return filtered_msg_dict


# Topics we want to publish to ROS (and subscribe to from the MiR)
PUB_TOPICS = [
    TopicConfig('LightCtrl/us_list', Range),
    TopicConfig('MC/currents', MotorCurrents),
    TopicConfig('MissionController/CheckArea/visualization_marker', Marker),
    TopicConfig('SickPLC/parameter_descriptions', ConfigDescription),
    TopicConfig('SickPLC/parameter_updates', Config),
    TopicConfig('amcl_pose', PoseWithCovarianceStamped),
    TopicConfig('b_raw_scan', LaserScan),
    TopicConfig('b_scan', LaserScan),
    TopicConfig('camera_floor/background', PointCloud2),
    TopicConfig('camera_floor/depth/parameter_descriptions', ConfigDescription),
    TopicConfig('camera_floor/depth/parameter_updates', Config),
    TopicConfig('camera_floor/depth/points', PointCloud2),
    TopicConfig('camera_floor/filter/visualization_marker', Marker),
    TopicConfig('camera_floor/floor', PointCloud2),
    TopicConfig('camera_floor/obstacles', PointCloud2),
    TopicConfig('check_area/polygon', PolygonStamped),
    TopicConfig('diagnostics', DiagnosticArray),
    TopicConfig('diagnostics_agg', DiagnosticArray),
    TopicConfig('diagnostics_toplevel_state', DiagnosticStatus),
    TopicConfig('f_raw_scan', LaserScan),
    TopicConfig('f_scan', LaserScan),
    TopicConfig('imu_data', Imu),
    TopicConfig('laser_back/driver/parameter_descriptions', ConfigDescription),
    TopicConfig('laser_back/driver/parameter_updates', Config),
    TopicConfig('laser_front/driver/parameter_descriptions', ConfigDescription),
    TopicConfig('laser_front/driver/parameter_updates', Config),
    TopicConfig('/map', OccupancyGrid, latch=True),
    TopicConfig('/map_metadata', MapMetaData),
    TopicConfig('mir_amcl/parameter_descriptions', ConfigDescription),
    TopicConfig('mir_amcl/parameter_updates', Config),
    TopicConfig('mir_amcl/selected_points', PointCloud2),
    TopicConfig('mir_log', Log),
    TopicConfig('mir_status_msg', String),
    TopicConfig('mirwebapp/grid_map_metadata', LocalMapStat),
    TopicConfig('mirwebapp/laser_map_metadata', LocalMapStat),
    TopicConfig(
        'move_base/feedback',
        MoveBaseActionFeedback,
        dict_filter=_move_base_feedback_dict_filter,
    ),
    TopicConfig(
        'move_base/result',
        MoveBaseActionResult,
        dict_filter=_move_base_result_dict_filter,
    ),
    TopicConfig('move_base/status', GoalStatusArray),
    TopicConfig('move_base_node/MIRPlannerROS/local_plan', Path),
    TopicConfig('move_base_node/MIRPlannerROS/updated_global_plan', PlanSegments),
    TopicConfig('move_base_node/SBPLLatticePlanner/plan', Path),
    TopicConfig('move_base_node/current_goal', PoseStamped),
    TopicConfig('move_base_node/local_costmap/inflated_obstacles', GridCells),
    TopicConfig('move_base_node/local_costmap/obstacles', GridCells),
    TopicConfig('move_base_node/local_costmap/robot_footprint', PolygonStamped),
    TopicConfig('move_base_node/time_to_coll', Float64),
    TopicConfig('move_base_node/traffic_costmap/inflated_obstacles', GridCells),
    TopicConfig('move_base_node/traffic_costmap/obstacles', GridCells),
    TopicConfig('move_base_node/traffic_costmap/parameter_descriptions', ConfigDescription),
    TopicConfig('move_base_node/traffic_costmap/parameter_updates', Config),
    TopicConfig('move_base_node/traffic_costmap/robot_footprint', PolygonStamped),
    TopicConfig('move_base_node/traffic_costmap/unknown_space', GridCells),
    TopicConfig('move_base_node/visualization_marker', Marker),
    TopicConfig('move_base_simple/visualization_marker', Marker),
    TopicConfig('odom', Odometry),
    TopicConfig('odom_enc', Odometry),
    TopicConfig('robot_mode', RobotMode),
    TopicConfig('robot_pose', Pose),
    TopicConfig('robot_state', RobotState),
    TopicConfig('/rosout', Log),
    TopicConfig('/rosout_agg', Log),
    TopicConfig('scan', LaserScan),
    TopicConfig('scan_filter/visualization_marker', Marker),
    TopicConfig('/tf', TFMessage, dict_filter=_tf_dict_filter),
    TopicConfig('/tf_static', TFMessage, dict_filter=_tf_static_dict_filter, latch=True),
]

# Topics we want to subscribe to from ROS (and publish to the MiR)
# Note: cmd_vel filter is created dynamically in MiRBridge.__init__ to use node's clock
SUB_TOPICS_TEMPLATE = [
    TopicConfig('initialpose', PoseWithCovarianceStamped),
    TopicConfig('light_cmd', String),
    TopicConfig('mir_cmd', String),
    TopicConfig('move_base/cancel', GoalID),
    # really mir_actions/MirMoveBaseActionGoal:
    TopicConfig('move_base/goal', MoveBaseActionGoal, dict_filter=_move_base_goal_dict_filter),
]


class PublisherWrapper:
    """Bridge MiR -> ROS 2 for a single topic."""

    def __init__(self, node: Node, topic_config: TopicConfig, robot: rosbridge.RosbridgeSetup):
        self.node = node
        self.topic_config = topic_config
        self.robot = robot
        self.connected = False

        # Use transient_local QoS for latched topics (like /map, /tf_static)
        if topic_config.latch:
            qos = QoSProfile(
                depth=10,
                durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
                reliability=QoSReliabilityPolicy.RELIABLE,
            )
        else:
            qos = QoSProfile(depth=10)

        self.pub = node.create_publisher(topic_config.topic_type, topic_config.topic, qos)

        node.get_logger().info(
            f"[{node.get_name()}] publishing topic '{topic_config.topic}' [{topic_config.topic_type.__name__}]"
        )

        # For latched topics, subscribe immediately to MiR side via rosbridge
        if topic_config.latch:
            self.peer_subscribe()

    def peer_subscribe(self):
        """Called when a subscriber connects (or immediately for latched topics)."""
        if not self.connected:
            self.connected = True
            self.node.get_logger().info(
                f"[{self.node.get_name()}] starting to stream messages on topic '{self.topic_config.topic}'"
            )
            absolute_topic = '/' + self.topic_config.topic.lstrip('/')
            self.robot.subscribe(topic=absolute_topic, callback=self.callback)

    def callback(self, msg_dict):
        msg_dict = _prepend_tf_prefix_dict_filter(msg_dict)
        if self.topic_config.dict_filter is not None:
            msg_dict = self.topic_config.dict_filter(msg_dict)
        msg = convert_dictionary_to_ros_message(self.topic_config.topic_type, msg_dict)
        self.pub.publish(msg)


class SubscriberWrapper:
    """Bridge ROS 2 -> MiR for a single topic."""

    def __init__(self, node: Node, topic_config: TopicConfig, robot: rosbridge.RosbridgeSetup):
        self.node = node
        self.topic_config = topic_config
        self.robot = robot

        qos = QoSProfile(depth=10)
        self.sub = node.create_subscription(
            topic_config.topic_type,
            topic_config.topic,
            self.callback,
            qos,
        )

        tname = (
            topic_config.topic_type.__name__
            if hasattr(topic_config.topic_type, '__name__')
            else str(topic_config.topic_type)
        )
        node.get_logger().info(
            f"[{node.get_name()}] subscribing to topic '{topic_config.topic}' [{tname}]"
        )

    def callback(self, msg):
        msg_dict = convert_ros_message_to_dictionary(msg)
        msg_dict = _remove_tf_prefix_dict_filter(msg_dict)
        if self.topic_config.dict_filter is not None:
            msg_dict = self.topic_config.dict_filter(msg_dict)
        absolute_topic = '/' + self.topic_config.topic.lstrip('/')
        self.robot.publish(absolute_topic, msg_dict)


class MiRBridge(Node):
    """ROS 2 node that bridges topics to/from MiR via rosbridge."""

    def __init__(self):
        super().__init__('mir_bridge')

        hostname_param = self.declare_parameter('hostname', '')
        hostname = hostname_param.get_parameter_value().string_value
        if not hostname:
            self.get_logger().fatal('parameter "hostname" is not set!')
            sys.exit(-1)

        port_param = self.declare_parameter('port', 9090)
        port = port_param.get_parameter_value().integer_value

        global tf_prefix
        tf_prefix_param = self.declare_parameter('tf_prefix', '')
        tf_prefix = tf_prefix_param.get_parameter_value().string_value.strip('/')

        self.get_logger().info(f"trying to connect to {hostname}:{port}...")
        self.robot = rosbridge.RosbridgeSetup(hostname, port)

        # Wait for connection
        while not self.robot.is_connected():
            if self.robot.is_errored():
                self.get_logger().fatal(f"connection error to {hostname}:{port}, giving up!")
                sys.exit(-1)
            self.get_logger().warn(f"still waiting for connection to {hostname}:{port}...")
            rclpy.spin_once(self, timeout_sec=0.5)

        self.get_logger().info("... connected.")

        # Query topics from MiR
        topics = self.get_topics()
        published_topics = [topic_name for (topic_name, _, has_publishers, _) in topics if has_publishers]
        subscribed_topics = [topic_name for (topic_name, _, _, has_subscribers) in topics if has_subscribers]

        # Setup MiR->ROS publishers
        self.publisher_wrappers = []
        for pub_topic in PUB_TOPICS:
            wrapper = PublisherWrapper(self, pub_topic, self.robot)
            self.publisher_wrappers.append(wrapper)
            absolute_topic = '/' + pub_topic.topic.lstrip('/')
            if absolute_topic not in published_topics:
                self.get_logger().warn(
                    f"[{self.get_name()}] topic '{pub_topic.topic}' is not published by the MiR!"
                )

        # Setup ROS->MiR subscribers
        # Create cmd_vel topic config with node's clock
        cmd_vel_filter = _cmd_vel_dict_filter_factory(self)
        sub_topics = SUB_TOPICS_TEMPLATE + [
            TopicConfig('cmd_vel', Twist, dict_filter=cmd_vel_filter),
        ]
        
        for sub_topic in sub_topics:
            SubscriberWrapper(self, sub_topic, self.robot)
            absolute_topic = '/' + sub_topic.topic.lstrip('/')
            if absolute_topic not in subscribed_topics:
                self.get_logger().warn(
                    f"[{self.get_name()}] topic '{sub_topic.topic}' is not yet subscribed to by the MiR!"
                )

        # Simple goal forwarding: move_base_simple/goal -> move_base/goal
        # At least with software version 2.8 there were issues when forwarding a simple goal to the robot
        # This workaround converts it into an action goal. Check https://github.com/DFKI-NI/mir_robot/issues/60 for details.
        self.move_base_goal_pub = self.create_publisher(MoveBaseActionGoal, 'move_base/goal', 10)
        self.create_subscription(
            PoseStamped,
            'move_base_simple/goal',
            self._move_base_simple_goal_callback,
            10,
        )

    def get_topics(self):
        srv_response = self.robot.callService('/rosapi/topics', msg={})
        topic_names = sorted(srv_response['topics'])
        topics = []

        for topic_name in topic_names:
            srv_response = self.robot.callService("/rosapi/topic_type", msg={'topic': topic_name})
            topic_type = srv_response['type']

            srv_response = self.robot.callService("/rosapi/publishers", msg={'topic': topic_name})
            has_publishers = len(srv_response['publishers']) > 0

            srv_response = self.robot.callService("/rosapi/subscribers", msg={'topic': topic_name})
            has_subscribers = len(srv_response['subscribers']) > 0

            topics.append([topic_name, topic_type, has_publishers, has_subscribers])

        self.get_logger().info('Publishers:')
        for topic_name, topic_type, has_publishers, _ in topics:
            if has_publishers:
                self.get_logger().info(f" * {topic_name} [{topic_type}]")

        self.get_logger().info('Subscribers:')
        for topic_name, topic_type, _, has_subscribers in topics:
            if has_subscribers:
                self.get_logger().info(f" * {topic_name} [{topic_type}]")

        return topics

    def _move_base_simple_goal_callback(self, msg: PoseStamped):
        """Convert move_base_simple/goal (PoseStamped) to move_base/goal (MoveBaseActionGoal)."""
        action_goal = MoveBaseActionGoal()
        action_goal.goal = MoveBaseGoal()
        action_goal.goal.target_pose = copy.deepcopy(msg)
        # Apply the same filter as regular move_base/goal
        goal_dict = convert_ros_message_to_dictionary(action_goal)
        goal_dict = _move_base_goal_dict_filter(goal_dict)
        action_goal = convert_dictionary_to_ros_message(MoveBaseActionGoal, goal_dict)
        self.move_base_goal_pub.publish(action_goal)


def main(args=None):
    rclpy.init(args=args)
    node = MiRBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

