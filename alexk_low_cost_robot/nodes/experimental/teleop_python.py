import os
import numpy as np
from dora import Node
import pyarrow as pa

from alexk_low_cost_robot.nodes.experimental.robot import Robot

ROBOT_PORTS = {
    'leader': '/dev/ttyACM1',
    'follower': '/dev/ttyACM0'
}

def pwm2pos(pwm:np.ndarray) -> np.ndarray:
    """
    :param pwm: numpy array of pwm values in range [0, 4096]
    :return: numpy array of joint positions in range [-pi, pi]
    """
    return (pwm / 2048 - 1) * 3.14

def pwm2vel(pwm:np.ndarray) -> np.ndarray:
    """
    :param pwm: numpy array of pwm/s joint velocities
    :return: numpy array of rad/s joint velocities 
    """
    return pwm * 3.14 / 2048


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
