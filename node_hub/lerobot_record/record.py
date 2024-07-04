"""
This Dora node is a minimalistic interface that shows two images and text in a Pygame window.
"""

import os
import argparse
import pygame

import pyarrow as pa

from dora import Node


def main():
    # Handle dynamic nodes, ask for the name of the node in the dataflow
    parser = argparse.ArgumentParser(
        description="Camera Client: This node is used to represent a camera. ")

    parser.add_argument("--name", type=str, required=False, help="The name of the node in the dataflow.",
                        default="opencv_camera")

    args = parser.parse_args()

    if not os.getenv("CAMERA_WIDTH") or not os.getenv("CAMERA_HEIGHT"):
        raise ValueError("Please set the CAMERA_ID, CAMERA_WIDTH, and CAMERA_HEIGHT environment variables")

    camera_width = os.getenv("CAMERA_WIDTH")
    camera_height = os.getenv("CAMERA_HEIGHT")

    image_left = pygame.Surface((int(camera_width), int(camera_height)))
    image_right = pygame.Surface((int(camera_width), int(camera_height)))

    pygame.font.init()
    font = pygame.font.SysFont("Comic Sans MS", 30)
    text = font.render("No text to render", True, (255, 255, 255))

    pygame.init()

    screen = pygame.display.set_mode((int(camera_width) * 2, int(camera_height) + text.get_height()))

    pygame.display.set_caption("Pygame minimalistic interface")

    node = Node(args.name)

    episode_index = 1
    recording = False

    for event in node:
        event_type = event["type"]
        if event_type == "STOP":
            break

        elif event_type == "INPUT":
            event_id = event["id"]

            if event_id == "image_left":
                raw_data = event["value"].to_numpy()
                image_left = pygame.image.frombuffer(raw_data, (int(camera_width), int(camera_height)), "BGR")

            elif event_id == "image_right":
                raw_data = event["value"].to_numpy()
                image_right = pygame.image.frombuffer(raw_data, (int(camera_width), int(camera_height)), "BGR")

            elif event_id == "tick":
                node.send_output(
                    "tick",
                    pa.array([]),
                    event["metadata"]
                )

                running = True
                for pygame_event in pygame.event.get():
                    if pygame_event.type == pygame.QUIT:
                        running = False
                        break
                    elif pygame_event.type == pygame.KEYDOWN:
                        key = pygame.key.name(pygame_event.key)

                        if key == "space":
                            recording = not recording
                            if recording:
                                text = font.render(f"Recording episode {episode_index}", True, (255, 255, 255))

                                node.send_output(
                                    "episode",
                                    pa.array([episode_index]),
                                    event["metadata"],
                                )
                            else:
                                text = font.render(f"Stopped recording episode {episode_index}", True, (255, 255, 255))

                                node.send_output(
                                    "episode",
                                    pa.array([-1]),
                                    event["metadata"],
                                )

                                episode_index += 1

                        elif key == "return":
                            if recording:
                                recording = not recording
                                text = font.render(f"Failed episode {episode_index}", True, (255, 255, 255))

                                node.send_output(
                                    "failed",
                                    pa.array([episode_index]),
                                    event["metadata"],
                                )
                                episode_index += 1
                                node.send_output(
                                    "episode",
                                    pa.array([-1]),
                                    event["metadata"],
                                )

                            elif episode_index >= 2:
                                text = font.render(f"Failed episode {episode_index - 1}", True, (255, 255, 255))

                                node.send_output(
                                    "failed",
                                    pa.array([episode_index - 1]),
                                    event["metadata"],
                                )

                if not running:
                    break

                screen.fill((0, 0, 0))

                # Draw the left image
                screen.blit(image_left, (0, 0))

                # Draw the right image
                screen.blit(image_right, (int(camera_width), 0))

                # Draw the text bottom center
                screen.blit(text,
                            (int(camera_width) - text.get_width() // 2, int(camera_height)))

                pygame.display.flip()

    node.send_output(
        "end",
        pa.array([])
    )

    pygame.quit()


if __name__ == "__main__":
    main()
