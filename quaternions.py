import numpy as np
import numpy.matlib as npm


# https://github.com/christophhagen/averaging-quaternions/blob/master/averageQuaternions.py
# Q is a Nx4 numpy matrix and contains the quaternions to average in the rows.
# The quaternions are arranged as (w,x,y,z), with w being the scalar
# The result will be the average quaternion of the input. Note that the signs
# of the output quaternion can be reversed, since q and -q describe the same orientation
def averageQuaternions(Q):
    # Number of quaternions to average
    M = Q.shape[0]
    A = npm.zeros(shape=(4, 4))

    for q in Q:
        # multiply q with its transposed version q' and add A
        A += np.outer(q, q)

    # scale
    A = A / float(M)
    # compute eigenvalues and -vectors
    eigenValues, eigenVectors = np.linalg.eig(A)
    # Sort by largest eigenvalue
    eigenVectors = eigenVectors[:, eigenValues.argsort()[::-1]]
    # return the real part of the largest eigenvector (has only real part)
    return np.real(eigenVectors[:, 0].A1)


def q_to_R(q):
    R = np.array([
        [1 - 2 * q[1] ** 2 - 2 * q[2] ** 2, 2 * (q[0] * q[1] - q[2] * q[3]), 2 * (q[0] * q[2] + q[1] * q[3])],
        [2 * (q[0] * q[1] + q[2] * q[3]), 1 - 2 * q[0] ** 2 - 2 * q[2] ** 2, 2 * (q[1] * q[2] - q[0] * q[3])],
        [2 * (q[0] * q[2] - q[1] * q[3]), 2 * (q[0] * q[3] + q[1] * q[2]), 1 - 2 * q[0] ** 2 - 2 * q[1] ** 2]])
    return R


def R_to_q(R):
    q_r = np.sqrt(R[0, 0] + R[1, 1] + R[2, 2] + 1) / 2
    q_v = np.array([[R[2, 1] - R[1, 2]], [R[0, 2] - R[2, 0]], [R[1, 0] - R[0, 1]]]) / (4 * q_r)
    q = np.append(q_v, q_r)
    return q


def averageMatrix(R):
    Q = []
    for r in R:
        Q.append(R_to_q(r))

    q_mean = averageQuaternions(np.array(Q))
    return q_to_R(q_mean)
