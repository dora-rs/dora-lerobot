import enum

import numpy as np


def physical_to_logical(physical_position: np.array, table: [{}]):
    result = []

    for i in range(len(physical_position)):
        if physical_position[i] is None:
            result.append(None)
            continue

        ranged = physical_position[i] % 4096
        index = ranged // 1024

        a = index * 1024
        b = (index + 1) * 1024

        c = table[i][str(index)][0]
        d = table[i][str(index)][1]

        result.append(np.int32(c + (ranged - a) * (d - c) / (b - a)))

    return np.array(result)


def logical_to_physical(logical_position: np.array, table: [{}]):
    result = []

    for i in range(len(logical_position)):
        if logical_position[i] is None:
            result.append(None)
            continue

        ranged = (logical_position[i] + 2048) % 4096
        index = ranged // 1024

        a = index * 1024
        b = (index + 1) * 1024

        c = table[i][str(index)][0]
        d = table[i][str(index)][1]

        result.append(np.int32(c + (ranged - a) * (d - c) / (b - a)))

    return np.array(result)


def turn_offset(physical_position: np.array, physical_to_logical_table: [{}], logical_to_physical_table: [{}]):
    result = []

    for i in range(len(physical_position)):
        if physical_position[i] is None:
            result.append(None)
            continue

        result.append(np.int32(physical_position[i] - logical_to_physical(
            physical_to_logical(physical_position, physical_to_logical_table), logical_to_physical_table)[i]))

    return np.array(result)
