# Handling arrays to string
import numpy as np


def instrinsic2string(c, d):
    s_decimals = '%0.10f'
    if c[0][0] == 0:
        A = 'Camera Matrix \n' + '\n'.join('\t'.join('???.???' for x in y) for y in np.eye(3))
        B = 'Distortion Coefficients \n' + '\n'.join('\t'.join('???.???' for x in y) for y in np.zeros((5, 1)))
    else:
        A = 'Camera Matrix \n' + '\n'.join('\t'.join(s_decimals % x for x in y) for y in c)
        B = 'Distortion Coefficients \n' + '\n'.join('\t'.join(s_decimals % x for x in y) for y in d)
    return A + '\n\n' + B


def extrinsic2string(R, T):
    s_decimals = '%0.10f'
    if R is None:
        A = 'Rotation Matrix between Cameras \n' + '\n'.join('\t'.join('???.???' for x in y) for y in np.eye(3))
        B = 'Translational Vector between Cameras \n' + '\n'.join(
            '\t'.join('???.???' for x in y) for y in np.zeros((3, 1)))
    else:
        A = 'Rotation Matrix between Cameras \n' + '\n'.join('\t'.join(s_decimals % x for x in y) for y in R)
        B = 'Translational Vector between Cameras \n' + '\n'.join('\t'.join(s_decimals % x for x in y) for y in T)
    return A + '\n\n' + B


def string2intrinsic(text):
    text = text.split('\n')
    c = np.zeros((3, 3), dtype=np.float32)
    d = np.zeros((5, 1), dtype=np.float32)
    for i in range(3):
        c[i] = np.array(text[i + 1].split('\t'), dtype=np.float32)
    for i in range(5):
        d[i] = text[i + 6]
    return c, d


def string2extrinsic(text):
    text = text.split('\n')
    R = np.zeros((3, 3), dtype=np.float32)
    T = np.zeros((3, 1), dtype=np.float32)
    for i in range(3):
        R[i] = np.array(text[i + 1].split('\t'), dtype=np.float32)
    for i in range(3):
        T[i] = text[i + 5 + 1]
    return R, T
