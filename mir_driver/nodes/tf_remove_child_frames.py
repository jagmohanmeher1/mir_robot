#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 The Cartographer Authors
# Copyright 2018 DFKI GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import rclpy
from rclpy.node import Node
from tf2_msgs.msg import TFMessage


class TfRemoveChildFrames(Node):
    def __init__(self):
        super().__init__('tf_remove_child_frames')

        self.declare_parameter('remove_frames', [])
        param_value = self.get_parameter('remove_frames').get_parameter_value()
        if param_value.type == param_value.TYPE_STRING_ARRAY:
            self.remove_frames = list(param_value.string_array_value)
        else:
            self.remove_frames = []

        # filter tf_in topic
        self.tf_pub = self.create_publisher(TFMessage, 'tf_out', 10)
        self.tf_sub = self.create_subscription(
            TFMessage,
            'tf_in',
            self.tf_cb,
            10,
        )

        # filter tf_static_in topic
        self.tf_static_pub = self.create_publisher(TFMessage, 'tf_static_out', 10)
        self.tf_static_sub = self.create_subscription(
            TFMessage,
            'tf_static_in',
            self.tf_static_cb,
            10,
        )

    def _filter_msg(self, msg: TFMessage):
        filtered = TFMessage()
        filtered.transforms = [
            t
            for t in msg.transforms
            if t.child_frame_id.lstrip('/') not in self.remove_frames
        ]
        if not filtered.transforms:
            return None
        return filtered

    def tf_cb(self, msg: TFMessage):
        filtered = self._filter_msg(msg)
        if filtered is not None:
            self.tf_pub.publish(filtered)

    def tf_static_cb(self, msg: TFMessage):
        filtered = self._filter_msg(msg)
        if filtered is not None:
            self.tf_static_pub.publish(filtered)


def main(args=None):
    rclpy.init(args=args)
    node = TfRemoveChildFrames()
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