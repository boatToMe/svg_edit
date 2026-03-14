def point_to_canvas(point, scale, offset_x, offset_y):
    x, y = point
    return x * scale + offset_x, y * scale + offset_y


def canvas_to_point(x, y, scale, offset_x, offset_y):
    return (x - offset_x) / scale, (y - offset_y) / scale
