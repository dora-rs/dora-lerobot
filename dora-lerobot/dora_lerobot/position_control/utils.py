import enum

import numpy as np


class DriveMode(enum.Enum):
    POSITIVE_CURRENT = np.uint32(0)
    NEGATIVE_CURRENT = np.uint32(1)


def physical_to_logical(values: np.array, offsets: np.array, drive_modes: np.array) -> np.array:
    """
    Convert physical values to logical values.
    :param values: numpy array of physical values
    :param offsets: numpy array of offsets
    :param drive_modes: numpy array of DriveMode
    :return: numpy array of logical values
    """
    result = np.array([None] * len(values))

    for i in range(len(values)):
        if values[i] is not None:
            result[i] = np.int32(values[i])

    for i, drive_mode in enumerate(drive_modes):
        if drive_mode is not None and result[i] is not None and drive_mode == DriveMode.NEGATIVE_CURRENT:
            result[i] = -result[i]

    for i, offset in enumerate(offsets):
        if offset is not None and result[i] is not None:
            result[i] += offset

    return result


def logical_to_physical(values: np.array, offsets: np.array, drive_modes: np.array) -> np.array:
    """
    Convert logical values to physical values.
    :param values: numpy array of logical values
    :param offsets: numpy array of offsets
    :param drive_modes: numpy array of drive_mode (0 clockwise or 1 counterclockwise)
    :return: numpy array of physical values
    """

    result = np.array([None] * len(values))

    for i in range(len(values)):
        if values[i] is not None:
            result[i] = np.int32(values[i])

    for i, offset in enumerate(offsets):
        if offset is not None and result[i] is not None:
            result[i] -= offset

    for i, drive_mode in enumerate(drive_modes):
        if drive_mode is not None and result[i] is not None and drive_mode == DriveMode.NEGATIVE_CURRENT:
            result[i] = -result[i]

    return result


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
