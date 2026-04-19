import logging
import math
import cv2
import numpy as np
from toolboxClass.miscTools.misc_tools import (get_all_combinations,
                                               get_one_combination,
                                               get_indices_to_average)
from toolboxClass.miscTools.quaternions import averageMatrix

logging.basicConfig(level=logging.ERROR)


def run_single_calibration(objpoints, imgpoints, size, n_cameras, m_stereo,
                           flags_parameters, sample_indices):
    """Run a single calibration (mono or stereo) on a sample of images.

    Args:
        objpoints: Object points for all images.
        imgpoints: Image points per camera [cam0_points, cam1_points].
        size: Image sizes per camera [(h, w), (h, w)].
        n_cameras: Number of cameras (1 or 2).
        m_stereo: Whether stereo mode is enabled.
        flags_parameters: OpenCV calibration flags.
        sample_indices: Indices of images to use for this calibration.

    Returns:
        tuple: (rms, camera_matrices, dist_coefs, R, T) or None on failure.
               camera_matrices and dist_coefs are lists of length n_cameras.
    """
    op = list(objpoints[i] for i in sample_indices)
    ip = []
    c = []
    d = []
    for j in range(n_cameras):
        ip.append(list(imgpoints[j][i] for i in sample_indices))
        c.append(np.eye(3, dtype=np.float32))
        d.append(np.zeros((5, 1), dtype=np.float32))

    R = None
    T = None

    if m_stereo:
        if size[0] != size[1]:
            logging.debug('Different camera resolution')
            ip = np.array(ip)
            index_min = size.index(min(size))
            index_max = size.index(max(size))
            w_max, h_max = size[index_max]
            w_min, h_min = size[index_min]
            w_adj = (w_max - w_min) / 2
            h_adj = (h_max - h_min) / 2
            n_poses, n_points, _, _ = ip[index_min].shape
            for pose in range(n_poses):
                for point in range(n_points):
                    ip[index_min][pose][point] = \
                        np.sum([ip[index_min][pose][point],
                                [[h_adj, w_adj]]], axis=0)
        width = max(size[0][1], size[1][1])
        height = max(size[0][0], size[1][0])
        rms, c[0], d[0], c[1], d[1], R, T, _, _ = \
            cv2.stereoCalibrate(op, ip[0], ip[1], c[0], d[0], c[1],
                                d[1], (width, height),
                                flags=flags_parameters)
    else:
        width = size[0][1]
        height = size[0][0]
        rms, c[0], d[0], _, _ = \
            cv2.calibrateCamera(op, ip[0], (width, height),
                                c[0], d[0], flags=flags_parameters)

    return rms, c, d, R, T


def run_clustering_calibration(objpoints, imgpoints, size, n_cameras, m_stereo,
                               flags_parameters, n_total, c_r, c_k,
                               progress_callback=None):
    """Run clustering-based calibration with multiple subsamples.

    Args:
        objpoints: Object points for all images.
        imgpoints: Image points per camera.
        size: Image sizes per camera.
        n_cameras: Number of cameras.
        m_stereo: Whether stereo mode is enabled.
        flags_parameters: OpenCV calibration flags.
        n_total: Total number of images.
        c_r: Number of elements per group.
        c_k: Number of groups.
        progress_callback: Optional callback(counter, k, elapsed_time)
                           for progress updates.

    Returns:
        dict: Dictionary containing:
            - camera_matrix, dev_camera_matrix
            - dist_coefs, dev_dist_coefs
            - R_stereo, T_stereo
            - rms
            - fx_array..k5_array (per-camera parameter arrays)
            - R_array, T_array, RMS_array
            - samples
            - success (bool)
    """
    from toolboxClass.miscTools.time_tools import chronometer

    max_k = math.comb(n_total, c_r)
    k = min(c_k, max_k)

    time_play = chronometer()

    C_array = []
    D_array = []
    R_array = []
    T_array = []

    fx_array = [[], []]
    fy_array = [[], []]
    cx_array = [[], []]
    cy_array = [[], []]
    k1_array = [[], []]
    k2_array = [[], []]
    k3_array = [[], []]
    k4_array = [[], []]
    k5_array = [[], []]
    RMS_array = []

    if k == max_k:
        samples = get_all_combinations(n_total, c_r)
    else:
        samples = []

    indices_to_average = None
    counter = 0
    doCalibration = True
    while doCalibration:
        if k != max_k:
            getting_new_sample = True
            while getting_new_sample:
                s = get_one_combination(n_total, c_r)
                if (s not in samples) or (len(samples) >= max_k):
                    samples.append(s)
                    getting_new_sample = False
        else:
            s = samples[counter]

        rms, c, d, R, T = run_single_calibration(
            objpoints, imgpoints, size, n_cameras, m_stereo,
            flags_parameters, s)

        C_array.append(c)
        D_array.append(d)
        RMS_array.append(rms)
        if m_stereo:
            R_array.append(R)
            T_array.append(T)
        indices_to_average = get_indices_to_average(RMS_array)
        counter = len(indices_to_average)

        c_percent = (counter + 1) / k
        elapsed_time = time_play.gettime()

        if progress_callback:
            progress_callback(counter, k, c_percent, elapsed_time)

        if counter >= k:
            break

    elapsed_time_1 = time_play.gettime()

    # get arrays according to indices to average
    C_array = np.array(C_array)[indices_to_average]
    D_array = np.array(D_array)[indices_to_average]
    for j in range(n_cameras):
        fx_array[j] = C_array[:, j][:, 0][:, 0]
        fy_array[j] = C_array[:, j][:, 1][:, 1]
        cx_array[j] = C_array[:, j][:, 0][:, 2]
        cy_array[j] = C_array[:, j][:, 1][:, 2]
        k1_array[j] = D_array[:, j][:, 0][:, 0]
        k2_array[j] = D_array[:, j][:, 1][:, 0]
        k3_array[j] = D_array[:, j][:, 2][:, 0]
        k4_array[j] = D_array[:, j][:, 3][:, 0]
        k5_array[j] = D_array[:, j][:, 4][:, 0]
    if m_stereo:
        R_array = np.array(R_array)[indices_to_average]
        T_array = np.array(T_array)[indices_to_average]
    RMS_array = np.array(RMS_array)[indices_to_average]
    samples = np.array(samples)[indices_to_average]

    # calculate mean parameters
    result = {'success': False}
    if len(C_array) > 0:
        camera_matrix = np.mean(C_array, axis=0)
        dist_coefs = np.mean(D_array, axis=0)
        dev_camera_matrix = np.std(C_array, axis=0)
        dev_dist_coefs = np.std(D_array, axis=0)
        R_stereo = np.zeros((3, 3), dtype=np.float32)
        T_stereo = np.zeros((3, 1), dtype=np.float32)
        if m_stereo:
            R_stereo = averageMatrix(R_array)
            T_stereo = np.mean(np.array(T_array), axis=0)
            # Correction for cx and cy parameters
            if size[0] != size[1]:
                index_min = size.index(min(size))
                w_max, h_max = size[size.index(max(size))]
                w_min, h_min = size[index_min]
                w_adj = (w_max - w_min) / 2
                h_adj = (h_max - h_min) / 2
                camera_matrix[index_min][0][2] -= h_adj
                camera_matrix[index_min][1][2] -= w_adj

        result = {
            'success': True,
            'camera_matrix': camera_matrix,
            'dev_camera_matrix': dev_camera_matrix,
            'dist_coefs': dist_coefs,
            'dev_dist_coefs': dev_dist_coefs,
            'R_stereo': R_stereo,
            'T_stereo': T_stereo,
            'fx_array': fx_array, 'fy_array': fy_array,
            'cx_array': cx_array, 'cy_array': cy_array,
            'k1_array': k1_array, 'k2_array': k2_array,
            'k3_array': k3_array, 'k4_array': k4_array,
            'k5_array': k5_array,
            'R_array': R_array, 'T_array': T_array,
            'RMS_array': RMS_array,
            'samples': samples,
            'elapsed_time_1': elapsed_time_1,
        }

    return result, k


def calculate_projection(objpoints, imgpoints, camera_matrix, dist_coefs,
                         n_cameras, m_stereo, R_stereo, T_stereo,
                         r=None, t=None):
    """Calculate projections for all cameras.

    Args:
        objpoints: Object points for all images.
        imgpoints: Image points per camera.
        camera_matrix: Camera matrices per camera.
        dist_coefs: Distortion coefficients per camera.
        n_cameras: Number of cameras.
        m_stereo: Whether stereo mode is enabled.
        R_stereo: Stereo rotation matrix.
        T_stereo: Stereo translation vector.
        r: Optional rotation vectors.
        t: Optional translation vectors.

    Returns:
        tuple: (projected, projected_stereo)
    """
    if t is None:
        t = []
    if r is None:
        r = []
    op = objpoints
    ip = imgpoints
    c = camera_matrix
    d = dist_coefs

    projected = [[], []]
    projected_stereo = [[], []]

    for j in range(n_cameras):
        projected[j] = []
        projected_stereo[(j + 1) % 2] = []
        for i, _ in enumerate(op):
            if not r:
                _, r1, t1, _ = cv2.solvePnPRansac(op[i], ip[j][i],
                                                   c[j], d[j])
            else:
                r1 = r[i][:]
                t1 = t[i][:]

            imgpoints2, _ = cv2.projectPoints(op[i], r1, t1, c[j], d[j])
            projected[j].append(imgpoints2)

            if m_stereo:
                r1 = cv2.Rodrigues(r1)[0]

                if j == 1:
                    r2 = np.dot(np.linalg.inv(R_stereo), r1)
                    t2 = np.dot(np.linalg.inv(R_stereo), t1) \
                        - np.dot(np.linalg.inv(R_stereo), T_stereo)
                else:
                    r2 = np.dot(R_stereo, r1)
                    t2 = np.dot(R_stereo, t1) + T_stereo

                imgpoints2, _ = cv2.projectPoints(op[i], r2, t2,
                                                  c[(j + 1) % 2],
                                                  d[(j + 1) % 2])
                projected_stereo[(j + 1) % 2].append(imgpoints2)

    return projected, projected_stereo


def calculate_error(imgpoints, projected, projected_stereo,
                    n_cameras, m_stereo, progress_callback=None):
    """Calculate reprojection errors for all cameras.

    Args:
        imgpoints: Image points per camera.
        projected: Projections per camera.
        projected_stereo: Stereo projections per camera.
        n_cameras: Number of cameras.
        m_stereo: Whether stereo mode is enabled.
        progress_callback: Optional callback(j, i, total) for progress.

    Returns:
        tuple: (r_error, r_error_p, rms) where rms is [rms_cam0, rms_cam1, rms_stereo]
    """
    r_error = [[], []]
    r_error_p = [[], []]
    rms = [0, 0, 0]

    for j in range(n_cameras):
        ip = imgpoints[j]
        r_error_p[j] = []
        r_error[j] = []
        for i, _ in enumerate(ip):
            if m_stereo:
                imgpoints2 = projected_stereo[j][i]
            else:
                imgpoints2 = projected[j][i]
            r_error[j].append(np.sqrt((
                np.power(np.linalg.norm(ip[i] - imgpoints2, axis=2), 2)
                .mean())))
            r_error_p[j].append(np.linalg.norm(ip[i] - imgpoints2, axis=2))

            if progress_callback:
                c_percent = (j * len(ip) + i + 1) \
                    / float(n_cameras * len(ip))
                progress_callback(c_percent)

            # update rms when the error for all the images is calculated
            if len(r_error[j]) == len(ip):
                logging.info('Updating RMS for camera %d', j + 1)
                rms[j] = np.sqrt(np.sum(np.square(r_error[j])) /
                                 len(r_error[j]))
                if j == 1:
                    rms[2] = np.sqrt(
                        np.sum(np.square(r_error[0] + r_error[1]))
                        / len(r_error[0] + r_error[1]))

    return r_error, r_error_p, rms
