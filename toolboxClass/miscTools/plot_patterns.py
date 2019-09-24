from random import SystemRandom


def plot_chessboard(c_pattern, p_width, p_height, w, h):
    p_width += 1
    p_height += 1
    w_step, w_down, w_limit, h_step, h_down, h_limit = pre_plot(p_width,
                                                                p_height,
                                                                w, h)

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


def plot_circle_grid(c_pattern, p_width, p_height, w, h, symmetric=True):
    w_step, w_down, _, h_step, h_down, _ = pre_plot(p_width, p_height, w, h)

    for i in range(0, p_width, 1):
        if symmetric is True:
            for j in range(0, p_height, 1):
                index_i = i * w_step + w_down
                index_j = j * h_step + h_down
                c_pattern.create_oval([(index_i + w_step / 2 - w_step / 5.0,
                                        index_j + h_step / 2 - h_step / 5.0),
                                       (index_i + w_step / 2 + w_step / 5.0,
                                        index_j + h_step / 2 + h_step / 5.0)],
                                      tag='grid_line')
        else:
            for j in range(int(i % 2 != 0), p_height, 2):
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


def pre_plot(p_width, p_height, w, h):
    w -= 2
    h -= 2

    w_step = int(w / p_width)
    w_down = w % p_width
    w_limit = w_step * p_width
    if w_down % 2 == 0:
        w_down = int(w_down / 2)
        w_limit += w_down
    else:
        w_down = int((w_down + 1) / 2)
        w_limit += w_down + 1

    h_step = int(h / p_height)
    h_down = h % p_height
    h_limit = h_step * p_height
    if h_down % 2 == 0:
        h_down = int(h_down / 2)
        h_limit += h_down
    else:
        h_down = int((h_down + 1) / 2)
        h_limit += h_down + 1

    return w_step, w_down, w_limit, h_step, h_down, h_limit


def plot_custom(c_pattern, all_points, w, h):
    w -= 2
    h -= 2
    randGenerator = SystemRandom()
    points = [(randGenerator.randint(0, w - 1),
               randGenerator.randint(0, h - 1)) for _ in range(all_points)]
    for p in points:
        c_pattern.create_oval([(p[0] - 2, p[1] - 2),
                               (p[0] + 2, p[1] + 2)],
                              tag='grid_line',
                              fill="red")
