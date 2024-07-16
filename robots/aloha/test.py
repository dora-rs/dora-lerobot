import time

import pyarrow as pa
import json

from common.dynamixel_bus import DynamixelBus, TorqueMode, OperatingMode
from common.position_control.utils import physical_to_logical, logical_to_physical
from common.position_control.configure import build_physical_to_logical, build_logical_to_physical

FULL_ARM = pa.array([
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
], type=pa.string())

FULL_ARM_WITHOUT_GRIPPER = pa.array([
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
], type=pa.string())

GRIPPER = pa.array(["9"], type=pa.string())


def main():
    leader = DynamixelBus(
        "COM13", {
            "1": (1, "x_series"),
            "2": (2, "x_series"),
            "3": (3, "x_series"),
            "4": (4, "x_series"),
            "5": (5, "x_series"),
            "6": (6, "x_series"),
            "7": (7, "x_series"),
            "8": (8, "x_series"),
            "9": (9, "x_series"),
        }
    )

    follower = DynamixelBus(
        "COM12", {
            "1": (1, "x_series"),
            "2": (2, "x_series"),
            "3": (3, "x_series"),
            "4": (4, "x_series"),
            "5": (5, "x_series"),
            "6": (6, "x_series"),
            "7": (7, "x_series"),
            "8": (8, "x_series"),
            "9": (9, "x_series"),
        }
    )

    follower.write_torque_enable(TorqueMode.ENABLED, FULL_ARM)

    with open("./robots/aloha/configs/leader.right.json", "r") as file:
        leader_config = json.load(file)

    with open("./robots/aloha/configs/follower.right.json", "r") as file:
        follower_config = json.load(file)

    leader_control = {
        key: {
            "physical_to_logical": build_physical_to_logical(value["physical_to_logical"]),
            "logical_to_physical": build_logical_to_physical(value["logical_to_physical"]),
        }

        for key, value in leader_config.items()
    }

    follower_control = {
        key: {
            "physical_to_logical": build_physical_to_logical(value["physical_to_logical"]),
            "logical_to_physical": build_logical_to_physical(value["logical_to_physical"]),
        }

        for key, value in follower_config.items()
    }

    while True:
        leader_position = leader.read_position(FULL_ARM_WITHOUT_GRIPPER)
        follower_position = follower.read_position(FULL_ARM_WITHOUT_GRIPPER)

        logical_leader_position = physical_to_logical(leader_position, leader_control)
        logical_follower_position = physical_to_logical(follower_position, follower_control)

        physical_follower_goal = logical_to_physical(logical_leader_position, follower_control)

        follower.write_goal_position(physical_follower_goal["positions"].values,
                                     physical_follower_goal["joints"].values)

        gripper_leader = leader.read_position(GRIPPER)
        logical_gripper = physical_to_logical(gripper_leader, leader_control)

        interpolated = logical_gripper["positions"].values[0].as_py() * 1.9

        interpolated = pa.scalar({
            "joints": GRIPPER,
            "positions": pa.array([interpolated], type=pa.int32())
        }, type=pa.struct({
            pa.field("joints", pa.list_(pa.string())),
            pa.field("positions", pa.list_(pa.int32()))
        }))

        interpolated_physical = logical_to_physical(interpolated, follower_control)

        follower.write_goal_position(interpolated_physical["positions"].values, GRIPPER)

        print(interpolated)

        time.sleep(0.016)


if __name__ == "__main__":
    main()
