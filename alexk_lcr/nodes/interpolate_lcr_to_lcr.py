"""
Interpolate LCR Node: This Dora node is used to calculates appropriate goal positions for the LCR knowing a Leader position
and Follower position
"""

import numpy as np
import pyarrow as pa

from dora import Node


def i32_to_u32(value: np.array) -> np.array:
    """
    Convert a signed 32-bit integer array to an unsigned 32-bit integer array.
    Args:
        value: np.array

    Returns:
        np.array
    """

    for i in range(len(value)):
        if value[i] is not None and value[i] < 0:
            value[i] = value[i] + 4294967296

    return value


def u32_to_i32(value: np.array) -> np.array:
    """
    Convert an unsigned 32-bit integer array to a signed 32-bit integer array.
    Args:
        value: np.array

    Returns:
        np.array
    """

    for i in range(len(value)):
        if value[i] is not None and value[i] > 2147483647:
            value[i] = value[i] - 4294967296

    return value


def in_range_position(value: np.array) -> np.array:
    i32_values = u32_to_i32(value)

    for i in range(6):
        if i32_values[i] > 4096:
            i32_values[i] = i32_values[i] % 4096
        if i32_values[i] < -4096:
            i32_values[i] = -(-i32_values[i] % 4096)

        if i != 4:
            if i32_values[i] > 2048:
                i32_values[i] = - 2048 + (i32_values[i] % 2048)
            elif i32_values[i] < -2048:
                i32_values[i] = 2048 - (-i32_values[i] % 2048)
        else:
            if i32_values[i] > 3072:
                i32_values[i] = - 2048 + (i32_values[i] % 2048)
            elif i32_values[i] < -1024:
                i32_values[i] = 2048 - (-i32_values[i] % 2048)

    return i32_to_u32(i32_values)


def main():
    node = Node("lcr_interpolate")

    leader_position = np.array([0, 0, 0, 0, 0, 0])
    follower_position = np.array([0, 0, 0, 0, 0, 0])

    follower_received = False

    for event in node:
        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "leader_position":

                if follower_received:
                    leader_position = event["value"].to_numpy()
                    leader_position = in_range_position(leader_position.copy())

                    goal_position = u32_to_i32(leader_position)

                    for i in range(len(goal_position)):
                        if follower_position[i] > 0:
                            goal_position[i] = goal_position[i] + (follower_position[i] // 4096) * 4096
                        else:
                            goal_position[i] = goal_position[i] - (-follower_position[i] // 4096) * 4096

                    goal_position = i32_to_u32(goal_position)

                    node.send_output(
                        "goal_position",
                        pa.array(goal_position.ravel()),
                        event["metadata"]
                    )

            elif event_id == "follower_position":
                follower_received = True
                follower_position = u32_to_i32(event["value"].to_numpy().copy())
        elif event_type == "STOP":
            break
        elif event_type == "ERROR":
            print("[lcr_interpolate] error: ", event["error"])
            break


if __name__ == "__main__":
    main()
