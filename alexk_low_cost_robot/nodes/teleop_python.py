import os
import numpy as np
from dora import Node
import pyarrow as pa

from robot import Robot, pwm2pos, pwm2vel

ROBOT_PORTS = {
    'leader': '/dev/ttyACM1',
    'follower': '/dev/ttyACM0'
}

if __name__ == '__main__':
    # init follower
    follower = Robot(device_name=os.environ.get('PUPPET_PATH', ROBOT_PORTS['follower']))
    # init leader
    leader = Robot(device_name=os.environ.get('MASTER_PATH', ROBOT_PORTS['leader']))
    leader.set_trigger_torque(int(os.environ.get('STRENGTH', 70)))
    for _ in range(200):
        follower.set_goal_pos(leader.read_position())

    node = Node()

    for event in node:
        event_type = event["type"]
        if event_type == "INPUT":
            # observation
            pwm_qpos = follower.read_position()
            pwm_qvel = follower.read_velocity()

            # action (leader's position)
            pwm_action = leader.read_position()

            # apply action
            follower.set_goal_pos(pwm_action)

            # Sotre in dataset
            qpos = pwm2pos(pwm_qpos)
            qvel = pwm2vel(pwm_qvel)
            action = pwm2pos(pwm_action)

            node.send_output(
                "puppet_position",
                pa.array(qpos.ravel()),
                event["metadata"],
            )
            node.send_output(
                "puppet_velocity",
                pa.array(qvel.ravel()),
                event["metadata"],
            )
            node.send_output(
                "puppet_goal_position",
                pa.array(action.ravel()),
                event["metadata"],
            )

    # Finished
    leader._disable_torque()
    follower._disable_torque()
