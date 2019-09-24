from random import SystemRandom


def plot_chessboard(c_pattern, p_width, p_height, w, h):
    w -= 2
    h -= 2

    p_w = p_width + 1
    w_step = int(w / p_w)
    w_down = w % p_w
    w_limit = w_step * p_w
    if w_down % 2 == 0:
        w_down = int(w_down / 2)
        w_limit += w_down
    else:
        w_down = int((w_down + 1) / 2)
        w_limit += w_down + 1

    p_h = p_height + 1
    h_step = int(h / p_h)
    h_down = h % p_h
    h_limit = h_step * p_h
    if h_down % 2 == 0:
        h_down = int(h_down / 2)
        h_limit += h_down
    else:
        h_down = int((h_down + 1) / 2)
        h_limit += h_down + 1

    # Creates all vertical lines at intervals of 100
    for i in range(w_down, w_limit + 1, w_step):
        c_pattern.create_line([(i, h_down), (i, h_limit)], tag='grid_line')

    # Creates all horizontal lines at intervals of 100
    for i in range(h_down, h_limit + 1, h_step):
        c_pattern.create_line([(w_down, i), (w_limit, i)], tag='grid_line')

    c_pattern.create_oval([(w_down + w_step - w_step / 3,
                            h_down + h_step - h_step / 3),
                           (w_down + w_step + w_step / 3,
                            h_down + h_step + h_step / 3)],
                          tag='grid_line', fill="red")


def plot_asymmetric_grid(c_pattern, p_width, p_height, w, h):
    w -= 2
    h -= 2

    p_w = p_width
    w_step = int(w / p_w)
    w_down = w % p_w
    w_limit = w_step * p_w
    if w_down % 2 == 0:
        w_down = w_down / 2
        w_limit += w_down
    else:
        w_down = (w_down + 1) / 2
        w_limit += w_down + 1

    p_h = p_height
    h_step = int(h / p_h)
    h_down = h % p_h
    h_limit = h_step * p_h
    if h_down % 2 == 0:
        h_down = h_down / 2
        h_limit += h_down
    else:
        h_down = (h_down + 1) / 2
        h_limit += h_down + 1

    for i in range(0, p_w, 1):
        for j in range(int(i % 2 != 0), p_h, 2):
            index_i = i * w_step + w_down
            index_j = j * h_step + h_down
            c_pattern.create_oval([(index_i, index_j),
                                   (index_i + w_step, index_j + h_step)],
                                  tag='grid_line')

    c_pattern.create_oval([(w_down + w_step / 2 - w_step / 5.0,
                            h_down + h_step / 2 - h_step / 5.0),
                           (w_down + w_step / 2 + w_step / 5.0,
                            h_down + h_step / 2 + h_step / 5.0)],
                          tag='grid_line',
                          fill="red")


def plot_symmetric_grid(c_pattern, p_width, p_height, w, h):
    w -= 2
    h -= 2

    p_w = p_width
    w_step = int(w / p_w)
    w_down = w % p_w
    w_limit = w_step * p_w
    if w_down % 2 == 0:
        w_down = w_down / 2
        w_limit += w_down
    else:
        w_down = (w_down + 1) / 2
        w_limit += w_down + 1

    p_h = p_height
    h_step = int(h / p_h)
    h_down = h % p_h
    h_limit = h_step * p_h
    if h_down % 2 == 0:
        h_down = h_down / 2
        h_limit += h_down
    else:
        h_down = (h_down + 1) / 2
        h_limit += h_down + 1

    for i in range(0, p_w, 1):
        for j in range(0, p_h, 1):
            index_i = i * w_step + w_down
            index_j = j * h_step + h_down
            c_pattern.create_oval([(index_i + w_step / 2 - w_step / 5.0,
                                    index_j + h_step / 2 - h_step / 5.0),
                                   (index_i + w_step / 2 + w_step / 5.0,
                                    index_j + h_step / 2 + h_step / 5.0)],
                                  tag='grid_line')

    c_pattern.create_oval([(w_down + w_step / 2 - w_step / 5.0,
                            h_down + h_step / 2 - h_step / 5.0),
                           (w_down + w_step / 2 + w_step / 5.0,
                            h_down + h_step / 2 + h_step / 5.0)],
                          tag='grid_line',
                          fill="red")


def plot_custom(c_pattern, all_points, w, h):
    w -= 2
    h -= 2
    points = [(SystemRandom.randint(0, w - 1),
               SystemRandom.randint(0, h - 1)) for _ in range(all_points)]
    for p in points:
        c_pattern.create_oval([(p[0] - 2, p[1] - 2),
                               (p[0] + 2, p[1] + 2)],
                              tag='grid_line',
                              fill="red")
