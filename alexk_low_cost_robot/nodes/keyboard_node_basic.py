import os
from pynput import keyboard
from pynput.keyboard import Key, Events
import pyarrow as pa
from dora import Node

node = Node()
print(node.dataflow_descriptor().keys(), flush=True)
cursor = -1
finished = False
with keyboard.Events() as events:
    node.send_output("space", pa.array([-1]))  # Start with -1
    while True:
        event = events.get(0.1)
        if event is not None and isinstance(event, Events.Release):
            if event.key == Key.space and not finished:
                cursor += 1
                os.system(f'spd-say "go {cursor}"')
                node.send_output("space", pa.array([cursor]))
            if event.key == Key.backspace:
                node.send_output("space", pa.array([-1]))   # Pause with -1
                os.system('spd-say "paused"')
            if event.key == Key.esc:
                finished = True
                node.send_output("space", pa.array([-1]))   # Finish with -1
                os.system('spd-say "finished"')
                break

        if node.next(0.001) is None:
            break