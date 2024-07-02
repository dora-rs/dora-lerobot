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

    values = values.astype(np.int32)

    for i, drive_mode in enumerate(drive_modes):
        if drive_mode is not None and values[i] is not None and drive_mode == DriveMode.NEGATIVE_CURRENT:
            values[i] = -values[i]

    for i, offset in enumerate(offsets):
        if offset is not None and values[i] is not None:
            values[i] += offset

    return values


def logical_to_physical(values: np.array, offsets: np.array, drive_modes: np.array) -> np.array:
    """
    Convert logical values to physical values.
    :param values: numpy array of logical values
    :param offsets: numpy array of offsets
    :param drive_modes: numpy array of drive_mode (0 clockwise or 1 counterclockwise)
    :return: numpy array of physical values
    """

    values = values.astype(np.int32)

    for i, offset in enumerate(offsets):
        if offset is not None and values[i] is not None:
            values[i] -= offset

    for i, drive_mode in enumerate(drive_modes):
        if drive_mode is not None and values[i] is not None and drive_mode == DriveMode.NEGATIVE_CURRENT:
            values[i] = -values[i]

    return values
