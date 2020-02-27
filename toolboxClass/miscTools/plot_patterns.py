from random import SystemRandom

color_pattern_width = '#aaaaf2'
color_pattern_mix = '#cb83cb'
color_pattern_height = '#f57dac'


def plot_chessboard(c_pattern, p_width, p_height, w, h):
    p_width += 1
    p_height += 1
    w_step, w_down, w_limit, h_step, h_down, h_limit = pre_plot(p_width,
                                                                p_height,
                                                                w, h)

    # Creates all vertical lines at intervals of 100
    for i in range(w_down, w_limit + 1, w_step):
        c_pattern.create_line([(i, h_down), (i, h_limit)], tag='grid_line')
        if i == w_down:
            c_pattern.create_oval([(i + w_step - w_step / 5.0,
                                    h_down + h_step - h_step / 5.0),
                                   (i + w_step + w_step / 5.0,
                                    h_down + h_step + h_step / 5.0)], fill=color_pattern_mix,
                                  tag='grid_oval')
        elif w_down < i < w_limit - 1 - w_step:
            c_pattern.create_oval([(i + w_step - w_step / 5.0,
                                    h_down + h_step - h_step / 5.0),
                                   (i + w_step + w_step / 5.0,
                                    h_down + h_step + h_step / 5.0)], fill=color_pattern_width,
                                  tag='grid_oval')

    # Creates all horizontal lines at intervals of 100
    for i in range(h_down, h_limit + 1, h_step):
        c_pattern.create_line([(w_down, i), (w_limit, i)], tag='grid_line')
        if h_down < i < h_limit - 1 - h_step:
            c_pattern.create_oval([(w_down + w_step - w_step / 5.0,
                                    i + h_step - h_step / 5.0),
                                   (w_down + w_step + w_step / 5.0,
                                    i + h_step + h_step / 5.0)],
                                  tag='grid_oval', fill=color_pattern_height)

    c_pattern.tag_raise('grid_oval')


def plot_circle_grid(c_pattern, p_width, p_height, w, h, symmetric=True):
    p_height += p_height * int(symmetric == False)
    w_step, w_down, _, h_step, h_down, _ = pre_plot(p_width, p_height, w, h)

    for i in range(0, p_width, 1):
        if symmetric is True:
            for j in range(0, p_height, 1):
                index_i = i * w_step + w_down
                index_j = j * h_step + h_down
                if j == 0:
                    if i == 0:
                        c_pattern.create_oval([(index_i + w_step / 2 - w_step / 5.0,
                                                index_j + h_step / 2 - h_step / 5.0),
                                               (index_i + w_step / 2 + w_step / 5.0,
                                                index_j + h_step / 2 + h_step / 5.0)], fill=color_pattern_mix,
                                              tag='grid_oval')
                    else:
                        c_pattern.create_oval([(index_i + w_step / 2 - w_step / 5.0,
                                                index_j + h_step / 2 - h_step / 5.0),
                                               (index_i + w_step / 2 + w_step / 5.0,
                                                index_j + h_step / 2 + h_step / 5.0)], fill=color_pattern_width,
                                              tag='grid_oval')
                elif i == 0:
                    c_pattern.create_oval([(index_i + w_step / 2 - w_step / 5.0,
                                            index_j + h_step / 2 - h_step / 5.0),
                                           (index_i + w_step / 2 + w_step / 5.0,
                                            index_j + h_step / 2 + h_step / 5.0)], fill=color_pattern_height,
                                          tag='grid_oval')
                else:
                    c_pattern.create_oval([(index_i + w_step / 2 - w_step / 5.0,
                                            index_j + h_step / 2 - h_step / 5.0),
                                           (index_i + w_step / 2 + w_step / 5.0,
                                            index_j + h_step / 2 + h_step / 5.0)], fill='white', tag='grid_oval')
        else:
            for j in range(int(i % 2 != 0), p_height, 2):
                index_i = i * w_step + w_down
                index_j = j * h_step + h_down
                if j == int(i % 2 != 0):
                    if i == 0:
                        c_pattern.create_oval([(index_i, index_j),
                                               (index_i + w_step, index_j + h_step)], fill=color_pattern_mix,
                                              tag='grid_oval')
                    else:
                        c_pattern.create_oval([(index_i, index_j),
                                               (index_i + w_step, index_j + h_step)], fill=color_pattern_width,
                                              tag='grid_oval')

                elif i == 0:
                    c_pattern.create_oval([(index_i, index_j),
                                           (index_i + w_step, index_j + h_step)], fill=color_pattern_height,
                                          tag='grid_line')
                else:
                    c_pattern.create_oval([(index_i, index_j),
                                           (index_i + w_step, index_j + h_step)], fill='white', tag='grid_oval')


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
                              fill='red')
