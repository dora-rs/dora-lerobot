import pyarrow as pa
from dora import DoraStatus

MAX_GRIPPER = 3145
MIN_GRIPPER = 2504

UP_POSITION = [2034, 1200, 1300, 2474, 2507, 2012, 2518, 2238, 2545]


class Operator:
    def on_event(self, event: dict, send_output) -> DoraStatus:
        if event["type"] == "INPUT":
            print("sending", flush=True)
            send_output(
                "puppet_goal_position",
                pa.array(
                    [2034, 787, 874, 3111, 3145, 2012, 2518, 2238, 2545],
                    # UP_POSITION,
                    type=pa.uint32(),
                ),
            )
        return DoraStatus.CONTINUE
