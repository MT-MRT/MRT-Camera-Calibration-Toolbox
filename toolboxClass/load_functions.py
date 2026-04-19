import logging
import os
import cv2
import numpy as np
import toolboxClass.miscTools.datastring as datastring

logging.basicConfig(level=logging.ERROR)


def load_3d_points(filepath):
    """Load 3D points from a text file.

    Args:
        filepath: Path to the text file.

    Returns:
        numpy.ndarray or None: 3D points array, or None if invalid.
    """
    set_3D_points = np.fromfile(filepath, dtype=np.float32, sep=',')
    if len(set_3D_points) % 3 != 0:
        return None
    return set_3D_points


def detect_features(image, pattern_type, pattern_height, pattern_width,
                    is_chessboard=False, is_asymmetric=False,
                    is_symmetric=False):
    """Detect features in an image for various pattern types.

    Args:
        image: Grayscale image.
        pattern_type: Pattern type string identifier.
        pattern_height: Number of pattern rows.
        pattern_width: Number of pattern columns.
        is_chessboard: Whether pattern is a chessboard.
        is_asymmetric: Whether pattern is an asymmetric circle grid.
        is_symmetric: Whether pattern is a symmetric circle grid.

    Returns:
        tuple: (success, features) where success is bool.
    """
    pre_processing = 4
    if is_symmetric:
        pre_processing = 8

    for process in range(pre_processing):
        if process == 0:
            logging.debug('Original image (Gray scale)')
            im2 = image * 1
        elif process == 1:
            logging.debug('Original image + Inverting image')
            im2 = 255 - im2
        elif process == 2:
            logging.debug('Normalized image (only)')
            im2 = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
        elif process == 3:
            logging.debug('Normalized image + Inverting image')
            im2 = 255 - im2
        elif process == 4:
            logging.debug('Normalized image + Gaussian Blur')
            im2 = cv2.GaussianBlur(image * 1, (11, 11), 0)
        elif process == 5:
            logging.debug('Normalized image + Gaussian Blur + Inverting image')
            im2 = 255 - im2
        elif process == 6:
            logging.debug('Normalized image + Dilate')
            L = 3
            grid_circle = np.zeros((L * 2 + 1, L * 2 + 1))
            for k in range(L):
                for ii in range(L - k, L + k + 1):
                    for jj in range(L - k, L + k + 1):
                        r = ((ii - L) ** 2 + (jj - L) ** 2) ** 0.5
                        if r <= k:
                            grid_circle[ii, jj] = 1
            kernel = grid_circle.astype(np.uint8)
            im2 = cv2.dilate(image * 1, kernel, iterations=1)
        elif process == 7:
            logging.debug('Normalized image + Dilate + Inverting image')
            im2 = 255 - im2

        # find features for chessboard pattern type
        if is_chessboard:
            ret, features = cv2.findChessboardCorners(
                im2, (pattern_height, pattern_width))
            if ret:
                criteria = (cv2.TERM_CRITERIA_EPS
                            + cv2.TERM_CRITERIA_MAX_ITER, 130, 0.25)
                cv2.cornerSubPix(im2, features, (3, 3), (-1, -1), criteria)
                return True, features
        elif is_asymmetric:
            features = np.array([], np.float32)
            ret, features = cv2.findCirclesGrid(
                im2, (pattern_height, pattern_width), features,
                cv2.CALIB_CB_ASYMMETRIC_GRID)
            if ret:
                return True, features
        elif is_symmetric:
            features = np.array([], np.float32)
            for inner_cycle in range(2):
                if inner_cycle == 0:
                    logging.debug('height - width')
                    ret, features = cv2.findCirclesGrid(
                        im2, (pattern_height, pattern_width), features,
                        cv2.CALIB_CB_SYMMETRIC_GRID)
                    if ret:
                        return True, features
                else:
                    logging.debug('width - height')
                    ret, features = cv2.findCirclesGrid(
                        im2, (pattern_width, pattern_height), features,
                        cv2.CALIB_CB_SYMMETRIC_GRID)
                    if ret:
                        features = features.reshape(
                            pattern_height, pattern_width, 1, 2)
                        features = np.transpose(features, (1, 0, 2, 3))
                        features = features.reshape(
                            pattern_width * pattern_height, 1, 2)
                        return True, features

    return False, None


def parse_intrinsics(text):
    """Parse intrinsic parameters from text.

    Args:
        text: Text content from intrinsics file.

    Returns:
        tuple: (camera_matrix, dist_coefs)
    """
    return datastring.string2intrinsic(text)


def parse_extrinsics(text):
    """Parse extrinsic parameters from text.

    Args:
        text: Text content from extrinsics file.

    Returns:
        tuple: (R, T)
    """
    return datastring.string2extrinsic(text)


def get_file_list(path, valid_extensions):
    """Get sorted list of valid files from a directory.

    Args:
        path: Directory path.
        valid_extensions: List of valid file extensions (e.g., ['.jpg', '.png']).

    Returns:
        list: Sorted list of full file paths.
    """
    file_no_path = []
    for f in os.listdir(path):
        ext = os.path.splitext(f)[1]
        if ext.lower() not in valid_extensions:
            continue
        file_no_path.append(f)
    try:
        file_no_path.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))
    except ValueError:
        logging.warning('non-indexable filenames')
    return [os.path.join(path, f) for f in file_no_path]


def process_image_file(filepath, size, pattern_type, pattern_height,
                       pattern_width, is_chessboard, is_asymmetric,
                       is_symmetric):
    """Process a single image file for feature detection.

    Args:
        filepath: Path to the image file.
        size: Expected image size tuple (height, width) or None.
        pattern_type: Pattern type string.
        pattern_height: Number of pattern rows.
        pattern_width: Number of pattern columns.
        is_chessboard: Whether pattern is chessboard.
        is_asymmetric: Whether pattern is asymmetric circle grid.
        is_symmetric: Whether pattern is symmetric circle grid.

    Returns:
        dict: Result with keys:
            - 'status': 'ok', 'rejected', 'invalid_size', 'repeated'
            - 'image': grayscale image (if status is 'ok' or needs size check)
            - 'features': detected features (if status is 'ok')
            - 'size': image size tuple
    """
    im = cv2.imread(filepath, 0)
    if im is None:
        return {'status': 'rejected'}

    im_size = im.shape

    if size is not None:
        if im_size != size:
            return {'status': 'invalid_size', 'image': None, 'features': None}

    ret, features = detect_features(im, pattern_type, pattern_height,
                                    pattern_width, is_chessboard,
                                    is_asymmetric, is_symmetric)

    if ret:
        return {'status': 'ok', 'image': im, 'features': features,
                'size': im_size}
    else:
        return {'status': 'rejected', 'image': None, 'features': None}
