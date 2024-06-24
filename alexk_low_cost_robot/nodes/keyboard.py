"""
LCR keyboard: this Dora node records the keyboard inputs for the puppet robot.

1. It listens to space key presses.
2. It registers the ID of the episode when the space key is pressed.
3. It sends the ID of the episode to the puppet robot if key is pressed
4. It sends -1 to the puppet robot if key is released
"""

import pyarrow as pa

from pynput.keyboard import Key, Listener

from dora import Node

from threading import Lock


class Keyboard:
    def __init__(self):
        self.cursor = 0
        self.press = False
        self.release = True

        self.space_press = False
        self.space_release = False

        self.lock = Lock()

    def on_press(self, key):
        if key == Key.space:
            with self.lock:
                if self.release:
                    self.press = True
                    self.space_press = True
                    self.release = False
                else:
                    self.press = False

    def on_release(self, key):
        if key == Key.space:
            with self.lock:
                self.cursor += 1
                self.release = True
                self.space_release = True


def main():
    keyboard = Keyboard()
    node = Node()

    listener = Listener(on_press=keyboard.on_press, on_release=keyboard.on_release)
    listener.start()

    for event in node:
        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "tick":
                with keyboard.lock:
                    if keyboard.space_press:
                        node.send_output("space", pa.array([keyboard.cursor]))
                        print(f"Recording episode {keyboard.cursor}", flush=True)

                        keyboard.space_press = False

                    if keyboard.space_release:
                        node.send_output("space", pa.array([-1]))
                        print(f"Pausing recording episode {keyboard.cursor}", flush=True)

                        keyboard.space_release = False

        elif event_type == "STOP":
            break
        elif event_type == "ERROR":
            print("[lcr_keyboard] error: ", event["error"])
            break

    listener.stop()


if __name__ == "__main__":
    main()
