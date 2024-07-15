import pyarrow as pa
import pyarrow.compute as pc


def physical_to_logical(physical_positions: pa.Scalar, table: {str: {str: []}}) -> pa.Scalar:
    result = {
        str: pa.Array,

        "joints": physical_positions["joints"].values
    }

    physical = physical_positions["positions"].values
    logical = []

    for i in range(len(physical)):
        if physical[i].as_py() is None:
            logical.append(None)
            continue

        ranged = physical[i].as_py() % 4096
        index = ranged // 1024

        a = index * 1024
        b = (index + 1) * 1024

        c = table[result["joints"][i].as_py()]["physical_to_logical"][str(index)][0]
        d = table[result["joints"][i].as_py()]["physical_to_logical"][str(index)][1]

        logical.append(pa.scalar(c + (ranged - a) * (d - c) / (b - a), type=pa.int32()))

    result["positions"] = pa.array(logical, type=pa.int32())

    return pa.scalar(result, type=pa.struct([
        pa.field("joints", pa.list_(pa.string())),
        pa.field("positions", pa.list_(pa.int32()))
    ]))


def logical_to_physical(logical_positions: pa.Scalar, table: {str: {str: []}}) -> pa.Scalar:
    result = {
        str: pa.Array,

        "joints": logical_positions["joints"].values
    }

    logical = logical_positions["positions"].values
    physical = []

    for i in range(len(logical)):
        if logical[i].as_py() is None:
            physical.append(None)
            continue

        ranged = (logical[i].as_py() + 2048) % 4096
        index = ranged // 1024

        a = index * 1024
        b = (index + 1) * 1024

        c = table[result["joints"][i].as_py()]["logical_to_physical"][str(index)][0]
        d = table[result["joints"][i].as_py()]["logical_to_physical"][str(index)][1]

        physical.append(pa.scalar(c + (ranged - a) * (d - c) / (b - a), type=pa.int32()))

    result["positions"] = pa.array(physical, type=pa.int32())

    return pa.scalar(result, type=pa.struct([
        pa.field("joints", pa.list_(pa.string())),
        pa.field("positions", pa.list_(pa.int32()))
    ]))


def calculate_offset(physical_positions: pa.Scalar, table: {str: {str: pa.Array}}) -> pa.Scalar:
    result = {
        str: pa.Array,

        "joints": physical_positions["joints"].values
    }

    physical = physical_positions["positions"].values

    logical = physical_to_logical(physical_positions, table)
    base = logical_to_physical(logical, table)["positions"].values

    offset = pc.subtract(physical, base)

    result["positions"] = pa.array(offset, type=pa.int32())

    return pa.scalar(result, type=pa.struct([
        pa.field("joints", pa.list_(pa.string())),
        pa.field("positions", pa.list_(pa.int32()))
    ]))
