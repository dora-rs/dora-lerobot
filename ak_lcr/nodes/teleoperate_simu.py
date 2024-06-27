"""
LCR teleoperate_simu: this Dora node teleoperates a simulated puppet robot using a real master robot.

1. It reads the current positions of the master robot.
2. It writes the current positions to the puppet robot.

"""

import os
import time

import numpy as np
import pyarrow as pa

from dora import Node
from dynamixel_sdk import PortHandler, PacketHandler

from alexk_arm import write_goal_current, read_present_current, write_goal_position, read_present_positions, \
    enable_torque, enable_torques, write_goal_positions, read_present_velocities, disable_torque, disable_torques

import mujoco
import mujoco.viewer


def u32_to_i32(value):
    """
    Convert an unsigned 32-bit integer to a signed 32-bit integer
    :param value: int
    :return: int
    """
    return value if value < 2 ** 31 else value - 2 ** 32


def i32_to_u32(value):
    """
    Convert a signed 32-bit integer to an unsigned 32-bit integer
    :param value: int
    :return: int
    """
    return value if value >= 0 else value + 2 ** 32


def i32_pos_to_rad(value):
    """
    Convert a signed 32-bit integer to a radian
    :param value: int
    :return: float
    """
    return (value / 2048) * 3.14


def u32_pos_to_rad(value):
    """
    Convert an unsigned 32-bit integer to a radian
    :param value: int
    :return: float
    """
    return i32_pos_to_rad(u32_to_i32(value))


def main():
    # Check if the MASTER_PATH environment variables are set
    if not os.environ.get("MASTER_PATH"):
        raise ValueError("Please set the MASTER_PATH environment variables")

    # Initialize the serial ports, set the baud rate and packet timeout
    master_path = os.environ.get("MASTER_PATH")

    master_serial = PortHandler(master_path)

    if not master_serial.openPort():
        raise ValueError(f"Failed to open port {master_path}")

    master_serial.setBaudRate(1000000)

    master_serial.setPacketTimeoutMillis(1000)

    # Initialize the packet handler
    io = PacketHandler(2.0)

    # Set somme shortcuts for robots
    full_arm = np.array([1, 2, 3, 4, 5, 6])
    gripper = 6

    # Enable all torques
    enable_torque(io, master_serial, gripper)

    # Place the master gripper at 400
    write_goal_position(io, master_serial, gripper, -450)

    # Place the master gripper current goal at 20
    write_goal_current(io, master_serial, gripper, 40)

    # Create env

    m = mujoco.MjModel.from_xml_path("gym_lowcostrobot/assets/low_cost_robot_6dof/reach_cube.xml")

    data = mujoco.MjData(m)

    with mujoco.viewer.launch_passive(m, data) as viewer:
        # Ready to loop and teleoperate the puppet robot
        node = Node()

        for event in node:
            event_type = event["type"]

            if event_type == "INPUT":
                event_id = event["id"]

                if event_id == "tick":
                    step_start = time.time()

                    # Step the simulation forward
                    mujoco.mj_step(m, data)
                    viewer.sync()

                    master_positions = read_present_positions(io, master_serial, full_arm)

                    master_positions = np.array(
                        [u32_to_i32(pos) if pos is not None else None for pos in master_positions])

                    # Ensure that every joint is within the range of -2048 to 2048 (0 can become 4095 for no reason)
                    for i in [0, 1, 2, 3, 5]:
                        if master_positions[i] is not None:
                            if master_positions[i] > 2048:
                                master_positions[i] = master_positions[i] - 4096
                            elif master_positions[i] < -2048:
                                master_positions[i] = master_positions[i] + 4096

                    # For this joint, the range may be -1024 to 3072
                    if master_positions[4] is not None:
                        if master_positions[4] > 3072:
                            master_positions[4] = master_positions[4] - 4096
                        elif master_positions[4] < -1024:
                            master_positions[4] = master_positions[4] + 4096

                    command_positions = np.array(
                        [i32_pos_to_rad(pos) if pos is not None else None for pos in master_positions])

                    # write_goal_positions(io, puppet_serial, full_arm, command_positions)

                    data.joint("shoulder_pan_joint").qpos[:3] = [0, 0, command_positions[0]]
                    data.joint("shoulder_lift_joint").qpos[:3] = [0, 0, command_positions[1]]
                    data.joint("elbow_flex_joint").qpos[:3] = [0, 0, command_positions[2]]
                    data.joint("wrist_flex_joint").qpos[:3] = [0, 0, command_positions[3]]
                    data.joint("wrist_roll_joint").qpos[:3] = [0, 0, command_positions[4]]
                    data.joint("gripper_joint").qpos[:3] = [0, 0, command_positions[5]]

            elif event_type == "STOP":
                break
            elif event_type == "ERROR":
                print("[lcr_teleoperate] error: ", event["error"])
                break

    # disable all torques
    disable_torque(io, master_serial, gripper)

    # Close the serial ports
    master_serial.closePort()


if __name__ == "__main__":
    main()
