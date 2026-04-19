import numpy as np


def create_chessboard_pattern(p_width, p_height, f_distance):
    """Create 3D object points for a chessboard calibration pattern.

    Args:
        p_width: Number of inner corners in the width direction.
        p_height: Number of inner corners in the height direction.
        f_distance: Distance between features in mm.

    Returns:
        numpy.ndarray: Array of 3D points with shape (p_width*p_height, 3).
    """
    object_pattern = np.zeros((p_width * p_height, 3), np.float32)
    grid = np.mgrid[0:p_height, 0:p_width].T.reshape(-1, 2) * f_distance
    object_pattern[:, 0] = -grid[:, 1]
    object_pattern[:, 1] = grid[:, 0]
    return object_pattern


def create_asymmetric_grid_pattern(p_width, p_height, f_distance):
    """Create 3D object points for an asymmetric circle grid pattern.

    Args:
        p_width: Number of circles in the width direction.
        p_height: Number of circles in the height direction.
        f_distance: Distance between features in mm.

    Returns:
        numpy.ndarray: Array of 3D points with shape (p_width*p_height, 3).
    """
    pattern_size = (p_height, p_width)
    object_pattern = np.zeros((np.prod(pattern_size), 3), np.float32)
    object_pattern[:, :2] = np.fliplr(
        np.indices(pattern_size).T.reshape(-1, 2))
    for i in range(np.prod(pattern_size)):
        if object_pattern[i, 0] % 2 == 0:
            object_pattern[i, 1] = object_pattern[i, 1] * f_distance
            object_pattern[i, 0] = object_pattern[i, 0] * f_distance / 2
        else:
            object_pattern[i, 1] = (object_pattern[i, 1] * f_distance
                                    + f_distance / 2)
            object_pattern[i, 0] = object_pattern[i, 0] * f_distance / 2
    return object_pattern


def create_symmetric_grid_pattern(p_width, p_height, f_distance):
    """Create 3D object points for a symmetric circle grid pattern.

    Args:
        p_width: Number of circles in the width direction.
        p_height: Number of circles in the height direction.
        f_distance: Distance between features in mm.

    Returns:
        numpy.ndarray: Array of 3D points with shape (p_width*p_height, 3).
    """
    object_pattern = np.zeros((p_width * p_height, 3), np.float32)
    grid = np.mgrid[0:p_height, 0:p_width].T.reshape(-1, 2) * f_distance
    object_pattern[:, 0] = -grid[:, 1]
    object_pattern[:, 1] = grid[:, 0]
    return object_pattern
