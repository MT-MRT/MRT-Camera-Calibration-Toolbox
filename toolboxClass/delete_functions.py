import numpy as np


def create_empty_error():
    """Create empty error-related data structures.

    Returns:
        tuple: (r_error, r_error_p, projected, projected_stereo)
    """
    r_error = [None, None]
    r_error_p = [[], []]
    projected = [[], []]
    projected_stereo = [[], []]
    return r_error, r_error_p, projected, projected_stereo


def create_empty_camera_parameters():
    """Create empty camera parameter data structures.

    Returns:
        tuple: (camera_matrix, dev_camera_matrix, dist_coefs,
                dev_dist_coefs, R_stereo, T_stereo, rms)
    """
    camera_matrix = [np.zeros((3, 3), dtype=np.float32),
                     np.zeros((3, 3), dtype=np.float32)]
    dev_camera_matrix = [np.zeros((3, 3), dtype=np.float32),
                         np.zeros((3, 3), dtype=np.float32)]
    dist_coefs = [np.zeros((5, 1), dtype=np.float32),
                  np.zeros((5, 1), dtype=np.float32)]
    dev_dist_coefs = [np.zeros((5, 1), dtype=np.float32),
                      np.zeros((5, 1), dtype=np.float32)]
    R_stereo = np.zeros((3, 3), dtype=np.float32)
    T_stereo = np.zeros((3, 1), dtype=np.float32)
    rms = [0, 0, 0]
    return (camera_matrix, dev_camera_matrix, dist_coefs,
            dev_dist_coefs, R_stereo, T_stereo, rms)


def delete_single_image_data(paths, img_original, detected_features,
                             projected, projected_stereo,
                             r_error, r_error_p, n_cameras, index):
    """Delete a single image's data from all arrays.

    Args:
        paths: List of path lists per camera.
        img_original: List of original image lists per camera.
        detected_features: List of detected feature lists per camera.
        projected: List of projection lists per camera.
        projected_stereo: List of stereo projection lists per camera.
        r_error: List of RMS error lists per camera.
        r_error_p: List of pixel distance error lists per camera.
        n_cameras: Number of cameras.
        index: Index of the image to delete.
    """
    for j in range(n_cameras):
        del paths[j][index]
        del img_original[j][index]
        del detected_features[j][index]
        if projected[j]:
            del projected[j][index]
        if j == 1:
            if projected_stereo[0]:
                del projected_stereo[0][index]
                del projected_stereo[1][index]
        if r_error[j]:
            del r_error[j][index]
            del r_error_p[j][index]
