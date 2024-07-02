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

    for event in node:
        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "leader_position":
                leader_position = event["value"].to_numpy()
                leader_position = in_range_position(leader_position.copy())

                node.send_output(
                    "goal_position",
                    pa.array(leader_position.ravel()),
                    event["metadata"]
                )

        elif event_type == "STOP":
            break
        elif event_type == "ERROR":
            print("[lcr_interpolate] error: ", event["error"])
            break


if __name__ == "__main__":
    main()
