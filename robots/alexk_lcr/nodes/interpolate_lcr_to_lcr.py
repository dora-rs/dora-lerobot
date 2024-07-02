"""
Interpolate LCR Node: This Dora node is used to calculates appropriate goal positions for the LCR knowing a Leader position
and Follower position
"""

import numpy as np
import pyarrow as pa

from dora import Node


def in_range_position(values: np.array) -> np.array:
    """
    This function assures that the position values are in the range of the LCR standard [-2048, 2048] all servos.
    This is important because an issue with communication can cause a +- 4095 offset value, so we need to assure
    that the values are in the range.
    """

    for i in range(6):
        if values[i] > 4096:
            values[i] = values[i] % 4096
        if values[i] < -4096:
            values[i] = -(-values[i] % 4096)

        if values[i] > 2048:
            values[i] = - 2048 + (values[i] % 2048)
        elif values[i] < -2048:
            values[i] = 2048 - (-values[i] % 2048)

    return values


def main():
    node = Node("lcr_interpolate")

    follower_position = np.array([0, 0, 0, 0, 0, 0])

    for event in node:
        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "leader_position":
                leader_position = event["value"][0]["positions"].values.to_numpy()
                leader_joints = event["value"][0]["joints"].values.to_numpy(zero_copy_only=False)

                leader_position = in_range_position(leader_position.copy())

                goal_position = leader_position

                """
                A communication issue with the follower can induces a +- 4095 offset in the position values.
                So we need to assure that the goal_position is in the range of the Follower.
                """
                for i in range(len(goal_position) - 1):
                    if follower_position[i] > 0:
                        goal_position[i] = goal_position[i] + (follower_position[i] // 4096) * 4096
                    else:
                        goal_position[i] = goal_position[i] - (-follower_position[i] // 4096) * 4096

                if follower_position[5] > 0:
                    goal_position[5] = goal_position[5] * (700.0 / 450.0) + (follower_position[5] // 4096) * 4096
                else:
                    goal_position[5] = goal_position[5] * (700.0 / 450.0) - (-follower_position[5] // 4096) * 4096

                goal_position_with_joints = {
                    "joints": leader_joints,
                    "positions": goal_position
                }

                node.send_output(
                    "goal_position",
                    pa.array([goal_position_with_joints]),
                    event["metadata"]
                )

            elif event_id == "follower_position":
                follower_position = event["value"][0]["positions"].values.to_numpy()
        elif event_type == "STOP":
            break
        elif event_type == "ERROR":
            print("[lcr_interpolate] error: ", event["error"])
            break


if __name__ == "__main__":
    main()
