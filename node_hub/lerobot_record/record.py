import argparse

import pyarrow as pa

from dora import Node


def main():
    # Handle dynamic nodes, ask for the name of the node in the dataflow
    parser = argparse.ArgumentParser(
        description="Camera Client: This node is used to represent a camera. ")

    parser.add_argument("--name", type=str, required=False, help="The name of the node in the dataflow.",
                        default="lerobot_record")

    args = parser.parse_args()

    node = Node(args.name)

    episode_index = 1
    recording = False

    for event in node:
        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "tick":
                if recording:
                    pass

            if event_id == "key_pressed":
                key = event["value"][0].as_py()
                if key == "space":
                    recording = not recording
                    if recording:
                        node.send_output(
                            "text",
                            pa.array([f"Recording episode {episode_index}"]),
                            event["metadata"],
                        )
                    else:
                        node.send_output(
                            "text",
                            pa.array([f"Stopped recording episode {episode_index}"]),
                            event["metadata"],
                        )
                        episode_index += 1
            elif event_id == "key_released":
                pass

        elif event_type == "STOP":
            break
        elif event_type == "ERROR":
            raise ValueError("An error occurred in the dataflow: " + event["error"])


if __name__ == "__main__":
    main()
