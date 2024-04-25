#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dora
from dora import Node
import pyarrow as pa
import numpy as np

CHECK_TICK = 50

# Create a ROS2 Context
ros2_context = dora.experimental.ros2_bridge.Ros2Context()
ros2_node = ros2_context.new_node(
    "robot_model_master",
    "/dora",
    dora.experimental.ros2_bridge.Ros2NodeOptions(rosout=True),
)

# Define a ROS2 QOS
topic_qos = dora.experimental.ros2_bridge.Ros2QosPolicies(
    reliable=True, max_blocking_time=0.1
)

# Create a publisher to cmd_vel topic
turtle_twist_topic = ros2_node.create_topic(
    "/robot_model_puppet/commands/joint_group",
    "interbotix_xs_msgs/JointGroupCommand",
    topic_qos,
)
twist_writer = ros2_node.create_publisher(turtle_twist_topic)

# Create a listener to pose topic
turtle_pose_topic = ros2_node.create_topic(
    "/robot_model_master/joint_states", "sensor_msgs/JointState", topic_qos
)
pose_reader = ros2_node.create_subscription(turtle_pose_topic)

# Create a dora node
dora_node = Node()

# Listen for both stream on the same loop as Python does not handle well multiprocessing
dora_node.merge_external_events(pose_reader)

print("looping", flush=True)

for event in dora_node:
    event_kind = event["kind"]

    # ROS2 Event
    if event_kind == "external":
        pose = event.inner()[0]
        values = np.array(pose["position"].values, dtype=np.float32)
        twist_writer.publish(
            pa.array(
                [
                    {
                        "name": "all",
                        "cmd": values,
                    }
                ]
            ),
        )
    # dora_node.send_output("turtle_pose", event.inner())
