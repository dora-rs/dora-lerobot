import pyarrow as pa
import pyarrow.compute as pc

ARROW_LOGICAL_VALUES = pa.struct({
    "joints": pa.list_(pa.string()),
    "values": pa.list_(pa.float32())
})

ARROW_PWM_VALUES = pa.struct({
    "joints": pa.list_(pa.string()),
    "values": pa.list_(pa.int32())
})


def physical_to_logical(physical_position: pa.Scalar, table: {}):
    joints = physical_position["joints"].values
    positions = physical_position["values"].values

    result = []

    for i in range(len(joints)):
        if joints[i].as_py() in table:
            result.append(table[joints[i].as_py()]["physical_to_logical"](
                (positions[i].as_py() % 4096) * 360 / 4096
            ) if positions[i].as_py() is not None else None)

    return pa.scalar({
        "joints": joints,
        "values": pa.array(result, type=pa.float32()),
    }, type=ARROW_LOGICAL_VALUES)


def logical_to_physical(logical_position: pa.Scalar, table: {}):
    joints = logical_position["joints"].values
    positions = logical_position["values"].values

    result = []

    for i in range(len(joints)):
        if joints[i].as_py() in table:
            result.append(int(table[joints[i].as_py()]["logical_to_physical"](
                positions[i].as_py() if positions[i].as_py() is not None else None
            ) * 4096 / 360) if positions[i].as_py() is not None else None)

    return pa.scalar({
        "joints": joints,
        "values": pa.array(result, type=pa.int32()),
    }, type=ARROW_PWM_VALUES)


def compute_goal_with_offset(physical_position: pa.Scalar, logical_goal: pa.Scalar, table: {}):
    goal = logical_to_physical(logical_goal, table)

    base = logical_to_physical(physical_to_logical(physical_position, table), table)

    return pa.scalar({
        "joints": base["joints"].values,
        "values": pc.add(pc.subtract(physical_position["values"].values, base["values"].values),
                         goal["values"].values)
    }, type=ARROW_PWM_VALUES)
