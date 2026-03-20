#!/usr/bin/env python3
# Copyright (c) 2018-2022, Martin Günther (DFKI GmbH) and contributors
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
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

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class FakeMirJointPublisher(Node):
    def __init__(self):
        super().__init__('fake_mir_joint_publisher')

        # Parameter for optional joint name prefix (for TF prefixes / multi-robot)
        self.declare_parameter('prefix', '')
        self.prefix = self.get_parameter('prefix').get_parameter_value().string_value

        self.publisher_ = self.create_publisher(JointState, 'joint_states', 10)

        # 50 Hz timer
        timer_period = 1.0 / 50.0
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        js = JointState()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = [
            self.prefix + 'left_wheel_joint',
            self.prefix + 'right_wheel_joint',
            self.prefix + 'fl_caster_rotation_joint',
            self.prefix + 'fl_caster_wheel_joint',
            self.prefix + 'fr_caster_rotation_joint',
            self.prefix + 'fr_caster_wheel_joint',
            self.prefix + 'bl_caster_rotation_joint',
            self.prefix + 'bl_caster_wheel_joint',
            self.prefix + 'br_caster_rotation_joint',
            self.prefix + 'br_caster_wheel_joint',
        ]
        js.position = [0.0 for _ in js.name]
        js.velocity = [0.0 for _ in js.name]
        js.effort = [0.0 for _ in js.name]
        self.publisher_.publish(js)


def main(args=None):
    rclpy.init(args=args)
    node = FakeMirJointPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

{
  "cells": [],
  "metadata": {
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 2
}