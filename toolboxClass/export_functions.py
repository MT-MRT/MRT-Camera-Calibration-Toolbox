import numpy as np
import toolboxClass.miscTools.datastring as datastring


def export_features_to_folder(object_pattern, detected_features, paths,
                              n_cameras, op_folder, ip_folders):
    """Export object points and image points to folders.

    Args:
        object_pattern: 3D pattern points array.
        detected_features: List of detected feature lists per camera.
        paths: List of path lists per camera.
        n_cameras: Number of cameras.
        op_folder: Folder path for object points (or empty string to skip).
        ip_folders: List of folder paths for image points per camera
                    (or empty strings to skip).
    """
    if object_pattern is not None:
        if op_folder != '':
            np.savetxt(op_folder + '/op.txt',
                       object_pattern.reshape(-1), newline=',')
        if len(paths[0]) > 0:
            for j in range(n_cameras):
                if ip_folders[j] != '':
                    for index in range(len(paths[j])):
                        feature = detected_features[j][index]
                        np.savetxt(ip_folders[j] + '/f_%d.txt' % index,
                                   feature.reshape(-1), newline=',')


def format_intrinsics(camera_matrix, dist_coefs):
    """Format intrinsic parameters as a string.

    Args:
        camera_matrix: 3x3 camera matrix.
        dist_coefs: 5x1 distortion coefficients.

    Returns:
        str: Formatted string of intrinsic parameters.
    """
    return datastring.instrinsic2string(camera_matrix, dist_coefs)


def format_extrinsics(R_stereo, T_stereo):
    """Format extrinsic parameters as a string.

    Args:
        R_stereo: 3x3 rotation matrix.
        T_stereo: 3x1 translation vector.

    Returns:
        str: Formatted string of extrinsic parameters.
    """
    return datastring.extrinsic2string(R_stereo, T_stereo)


def save_calibration_iteration(fx_array, fy_array, cx_array, cy_array,
                               k1_array, k2_array, k3_array, k4_array,
                               k5_array, R_array, T_array, RMS_array,
                               samples, paths, n_cameras, path_folder,
                               translate=None):
    """Save calibration results per iteration to a folder.

    Args:
        fx_array, fy_array, cx_array, cy_array: Camera parameter arrays.
        k1_array..k5_array: Distortion parameter arrays.
        R_array: Rotation matrices per iteration.
        T_array: Translation vectors per iteration.
        RMS_array: RMS error per iteration.
        samples: Sample indices per iteration.
        paths: List of path lists per camera.
        n_cameras: Number of cameras.
        path_folder: Output folder path.
        translate: Optional translation function (defaults to identity).
    """
    if translate is None:
        def translate(s):
            return s

    if path_folder != '':
        for j in range(n_cameras):
            filename = '/fx_cam_' + str(j + 1) + '.txt'
            np.array(fx_array[j]).tofile(path_folder + filename, '\n')
            filename = '/fy_cam_' + str(j + 1) + '.txt'
            np.array(fy_array[j]).tofile(path_folder + filename, '\n')
            filename = '/cx_cam_' + str(j + 1) + '.txt'
            np.array(cx_array[j]).tofile(path_folder + filename, '\n')
            filename = '/cy_cam_' + str(j + 1) + '.txt'
            np.array(cy_array[j]).tofile(path_folder + filename, '\n')
            filename = '/k1_cam_' + str(j + 1) + '.txt'
            np.array(k1_array[j]).tofile(path_folder + filename, '\n')
            filename = '/k2_cam_' + str(j + 1) + '.txt'
            np.array(k2_array[j]).tofile(path_folder + filename, '\n')
            filename = '/k3_cam_' + str(j + 1) + '.txt'
            np.array(k3_array[j]).tofile(path_folder + filename, '\n')
            filename = '/k4_cam_' + str(j + 1) + '.txt'
            np.array(k4_array[j]).tofile(path_folder + filename, '\n')
            filename = '/k5_cam_' + str(j + 1) + '.txt'
            np.array(k5_array[j]).tofile(path_folder + filename, '\n')
            if j == 1:
                filename = translate('/rotation.txt')
                f = open(path_folder + filename, 'w')
                for r in R_array:
                    f.write(','.join(str(e) for e in r) + '\n')
                f.close()
                filename = translate('/translation.txt')
                f = open(path_folder + filename, 'w')
                for t in T_array:
                    f.write(','.join(str(e[0]) for e in t) + '\n')
                f.close()

        filename = translate('/rms') + '.txt'
        np.array(RMS_array).tofile(path_folder + filename, '\n')
        filename = translate('/samples') + '.txt'
        f = open(path_folder + filename, 'w')
        for s in samples:
            f.write('[')
            for j in range(n_cameras):
                if j == 1:
                    f.write(',')
                f.write('[')
                l_paths_s = list(paths[j][i] for i in s)
                f.write(','.join(str(e) for e in l_paths_s))
                f.write(']')
            f.write(']')
            f.write('\n')
        f.close()
