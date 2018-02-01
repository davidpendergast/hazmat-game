import math
import random


def dist(v1, v2):
    dx = v1[0] - v2[0]
    dy = v1[1] - v2[1]
    return math.sqrt(dx * dx + dy * dy)


def sub(v1, v2):
    """return v1 - v2"""
    return (v1[0] - v2[0], v1[1] - v2[1])


def add(v1, v2):
    return (v1[0] + v2[0], v1[1] + v2[1])


def dot(v1, v2):
    return v1[0] * v2[0] + v1[1] * v2[1]


def neg(v):
    return (-v[0], -v[1])


def mag(v1):
    return math.sqrt(v1[0] * v1[0] + v1[1] * v1[1])


def normalize(v):
    if is_zero(v):
        return v
    else:
        m = mag(v)
        return (v[0] / m, v[1] / m)


def mult(v, a):
    return (v[0] * a, v[1] * a)


def is_zero(v):
    return mag(v) < 0.00001


def set_length(v, length):
    return mult(normalize(v), length)


def extend(v, length):
    return set_length(v, mag(v) + length)


def intify(v):
    return (round(v[0]), round(v[1]))


def rotate(v, rads):
    cos = math.cos(rads)
    sin = math.sin(rads)
    res_x = cos * v[0] - sin * v[1]
    res_y = sin * v[0] + cos * v[1]
    return (res_x, res_y)


def rand_direction():
    rads = random.random() * 2 * math.pi
    return (math.cos(rads), math.sin(rads))


def tend_towards(target, current, increment, only_if_increasing=False):
    if only_if_increasing and target * current > 0 and abs(target) < abs(current):
        return current
    elif abs(target - current) < abs(increment):
        return target
    elif current < target:
        return current + abs(increment)
    else:
        return current - abs(increment)


def projection(v1, v2):
    """returns: projection of v1 onto v2"""
    if is_zero(v2):
        return (0, 0)
    return sub(v1, component(v1, v2))


def component(v1, v2):
    """returns: component of v1 onto v2"""
    if is_zero(v2):
        return (0, 0)
    length = dot(v1, v2) / mag(v2)
    return set_length(v2, length)


def angle_between(v1, v2):
    if is_zero(v1) or is_zero(v2):
        return 0
    else:
        return abs(math.atan2(*v1) - math.atan2(*v2))


def same_direction(v1, v2):
    if is_zero(v1) or is_zero(v2):
        return False
    else:
        return angle_between(v1, v2) <= math.pi / 2


def sliver_adjacent(rect, direction, thickness=1):
    if direction[0] < 0:
        return (rect.x - thickness, rect.y, thickness, rect.height)
    elif direction[0] > 0:
        return (rect.x + rect.width, rect.y, thickness, rect.height)
    elif direction[1] < 0:
        return (rect.x, rect.y - thickness, rect.width, thickness)
    else:
        return (rect.x, rect.y + rect.height, rect.width, thickness)


def recenter_rect_in(rect1, rect2):
    """
    returns: a rectangle (in integer list form: [x, y, w, h]) with the size of
    rect1 that has the same center as rect2. Does not change rect1 or rect2.
    """
    c1 = (rect1[0] + rect1[2]/2, rect1[1] + rect1[3]/2)
    c2 = (rect2[0] + rect2[2]/2, rect2[1] + rect2[3]/2)
    diff = sub(c2, c1)
    return [int(rect1[0] + diff[0]),
            int(rect1[1] + diff[1]),
            rect1[2],
            rect1[3]]


def corner_snap_rects(to_move, target, outside=True):
    """
    Moves to_move such that one of its corners is snapped to target's corner. If outside=False, there will be at least
    two edges that become overlapped. If false, no edges will overlap. The distance moved will be the minimum possible.
    """
    X = to_move
    x1 = (X[0], X[1])
    x2 = (X[0] + X[2], X[1])
    x3 = (X[0] + X[2], X[1] + X[3])
    x4 = (X[0], X[1] + X[3])

    Y = target
    y1 = (Y[0], Y[1])
    y2 = (Y[0] + Y[2], Y[1])
    y3 = (Y[0] + Y[2], Y[1] + Y[3])
    y4 = (Y[0], Y[1] + Y[3])

    if outside:
        pairings = [(x1, y3), (x2, y4), (x3, y1), (x4, y2)]
    else:
        pairings = [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]

    i_min = 0
    for i in range(1, 4):
        p = pairings[i]
        if dist(p[0], p[1]) < dist(pairings[i_min][0], pairings[i_min][1]):
            i_min = i

    dxy = sub(pairings[i_min][1], pairings[i_min][0])

    return [X[0] + dxy[0], X[1] + dxy[1], X[2], X[3]]


def closest_rect_by_center(pt, rects):
    rects = list(rects)
    best_dist = None
    best_r = None
    for r in rects:
        if best_r is None:
            best_r = r
            best_dist = dist(pt, (r[0] + r[2]/2, r[1] + r[3]/2))
        else:
            cur_dist = dist(pt, (r[0] + r[2]/2, r[1] + r[3]/2))
            if cur_dist < best_dist:
                best_r = r
    return best_r

