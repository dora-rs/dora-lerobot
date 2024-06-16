import os
import numpy as np
from dora import Node
import pyarrow as pa

from robot import Robot, pos2pwm, pwm2pos

ROBOT_PORTS = {
    'follower': '/dev/ttyACM0'
}

if __name__ == '__main__':
    # init follower
    follower = Robot(device_name=os.environ.get('PUPPET_PATH', ROBOT_PORTS['follower']))

    node = Node()

    for event in node:
        event_type = event["type"]
        if event_type == "INPUT":
            if event["id"] == "puppet_goal_position":
                puppet_goal_position = event["value"].to_numpy()
                pwm_goal_pos = pos2pwm(puppet_goal_position)
                # apply action
                print("Setting goal position to: ", pwm_goal_pos, "from: ", puppet_goal_position)
                follower.set_goal_pos(pwm_goal_pos)
            elif event["id"] == "tick":
                pwm_qpos = follower.read_position()
                pos = pwm2pos(pwm_qpos)
                node.send_output(
                    "puppet_position",
                    pa.array(pos.ravel()),
                    event["metadata"])
            elif event["id"] == "terminated":
                break

    # Finished
    follower._disable_torque()
