import cv2
import numpy as np
from matplotlib import cm


def create_feature_image(image, features, pattern_height, pattern_width):
    """Create an image with the original one and its detected features with markers.

    Args:
        image: Grayscale original image.
        features: Detected features array.
        pattern_height: Number of pattern rows.
        pattern_width: Number of pattern columns.

    Returns:
        numpy.ndarray: RGB image with drawn features.
    """
    if features.any():
        im2 = np.uint8(np.zeros(image.shape + (3,)))
        im2[:, :, 0] = image
        im2[:, :, 1] = image
        im2[:, :, 2] = image
        cv2.drawChessboardCorners(im2, (pattern_height, pattern_width),
                                  features, True)
    else:
        im2 = image
    return im2


def create_heat_map(size, detected_features):
    """Calculate a density cloud heat map of all the images using detected features.

    Args:
        size: Tuple of (height, width) of the images.
        detected_features: List of feature arrays for one camera.

    Returns:
        numpy.ndarray: RGBA heat map image.
    """
    width = size[1]
    height = size[0]
    grid = np.zeros((height, width))
    list_features = detected_features

    # create circle matrix for each pattern
    L = int(round(0.006 * width + 8))
    step = 1.0 / L
    grid_circle = np.zeros((L * 2 + 1, L * 2 + 1))
    for k in range(L):
        for i in range(L - k, L + k + 1):
            for j in range(L - k, L + k + 1):
                r = ((i - L) ** 2 + (j - L) ** 2) ** 0.5
                if r <= k:
                    grid_circle[i, j] += step

    for k in list_features:
        for c in k:
            x = int(c[0][1])
            y = int(c[0][0])
            x_min = 0
            x_max = height
            y_min = 0
            y_max = width
            x_min_g = 0
            x_max_g = L * 2 + 1
            y_min_g = 0
            y_max_g = L * 2 + 1

            if x - L < 0:
                x_min_g -= x - L
            else:
                x_min += x - L
            if x + L + 1 > height:
                x_max_g = x_max - x_min
            else:
                x_max = x + L + 1
            if y - L < 0:
                y_min_g -= y - L
            else:
                y_min += y - L
            if y + L + 1 > width:
                y_max_g = y_max - y_min
            else:
                y_max = y + L + 1

            grid[x_min:x_max, y_min:y_max] += grid_circle[x_min_g:x_max_g,
                                                           y_min_g:y_max_g]

    # normalize the picture
    grid = ((grid - grid.min()) / (grid.max() - grid.min()))
    im = np.uint8(cm.jet(grid) * 255)
    return im


def create_moving_features_image(image, size, detected_features, index,
                                 index_corner, new_coord_feature):
    """Create image showing feature positions with optional new position.

    Args:
        image: Grayscale original image.
        size: Tuple of (height, width).
        detected_features: Feature array for the current image.
        index: Image index.
        index_corner: Selected corner index.
        new_coord_feature: New coordinate for the selected feature, or [].

    Returns:
        numpy.ndarray: RGB image with drawn features.
    """
    im3 = np.uint8(np.zeros(size + (3,)))
    im3[:, :, 0] = image
    im3[:, :, 1] = image
    im3[:, :, 2] = image

    for index_f in range(len(detected_features[index])):
        a = detected_features[index][index_f]
        a = a.astype(int)
        if index_f == index_corner:
            color = (154, 12, 70)
            if new_coord_feature:
                if (abs(a[0][0] - new_coord_feature[0][0]) < 10**-3
                        and abs(a[0][1] - new_coord_feature[0][1]) < 10**-3):
                    color = (80, 149, 200)
                a = [[round(x) for x in new_coord_feature[0]]]
            cv2.circle(im3, (a[0][0], a[0][1]), 5, color)
        else:
            cv2.circle(im3, (a[0][0], a[0][1]), 3, (80, 149, 200))

    return im3


def create_projection_image(image, size, detected_features, projections,
                            index, index_corner, pattern_height, pattern_width):
    """Create image comparing original features (green) and projections (red).

    The current selected feature index is represented by a circle over the point.

    Args:
        image: Grayscale original image.
        size: Tuple of (height, width).
        detected_features: Feature array for one camera.
        projections: Projection data for one camera (or empty list).
        index: Image index.
        index_corner: Selected corner index.
        pattern_height: Number of pattern rows.
        pattern_width: Number of pattern columns.

    Returns:
        numpy.ndarray: RGB image with drawn projection mesh.
    """
    im3 = np.uint8(np.zeros(size + (3,)))
    im3[:, :, 0] = image
    im3[:, :, 1] = image
    im3[:, :, 2] = image

    # plot projection mesh of features using red lines
    if projections:
        for i in range(pattern_height):
            for j in range(pattern_width):
                a = projections[index][j * pattern_height + i]
                a = a.astype(int)
                if j * pattern_height + i == index_corner:
                    cv2.circle(im3, (a[0][0], a[0][1]), 5, (154, 12, 70))
                if i < pattern_height - 1:
                    b = projections[index][j * pattern_height + i + 1]
                    b = b.astype(int)
                    cv2.line(im3, (a[0][0], a[0][1]),
                             (b[0][0], b[0][1]), (154, 12, 70))
                if j < pattern_width - 1:
                    c = projections[index][(j + 1) * pattern_height + i]
                    c = c.astype(int)
                    cv2.line(im3, (a[0][0], a[0][1]),
                             (c[0][0], c[0][1]), (154, 12, 70))

    # plot original mesh of features using green lines
    for i in range(pattern_height):
        for j in range(pattern_width):
            a = detected_features[index][j * pattern_height + i]
            a = a.astype(int)
            if j * pattern_height + i == index_corner:
                cv2.circle(im3, (a[0][0], a[0][1]), 5, (80, 149, 200))
            if i < pattern_height - 1:
                b = detected_features[index][j * pattern_height + i + 1]
                b = b.astype(int)
                cv2.line(im3, (a[0][0], a[0][1]),
                         (b[0][0], b[0][1]), (80, 149, 200))
            if j < pattern_width - 1:
                c = detected_features[index][(j + 1) * pattern_height + i]
                c = c.astype(int)
                cv2.line(im3, (a[0][0], a[0][1]),
                         (c[0][0], c[0][1]), (80, 149, 200))

    return im3
