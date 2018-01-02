import math
import random

def dist(v1, v2):
    dx = v1[0] - v2[0]
    dy = v1[1] - v2[1]
    return math.sqrt(dx*dx + dy*dy)
    
def sub(v1, v2):
    """return v1 - v2"""
    return (v1[0] - v2[0], v1[1] - v2[1])

def add(v1, v2):
    return (v1[0] + v2[0], v1[1] + v2[1])
    
def dot(v1, v2):
    return v1[0]*v2[0] + v1[1]*v2[1]
    
def neg(v):
    return (-v[0], -v[1])
    
def mag(v1):
    return math.sqrt(v1[0]*v1[0] + v1[1]*v1[1])
    
def normalize(v):
    if is_zero(v):
        return v
    else:
        m = mag(v)
        return (v[0] / m, v[1] / m)
        
def mult(v, a):
    return (v[0]*a, v[1]*a)
        
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
    res_x = cos*v[0] - sin*v[1]
    res_y = sin*v[0] + cos*v[1]
    return (res_x, res_y)
    
def rand_direction():
    rads = random.random() * 2 * math.pi
    return (math.cos(rads), math.sin(rads))
    
def tend_towards(target, current, increment, only_if_increasing=False):
    if only_if_increasing and target*current > 0 and abs(target) < abs(current):
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
    
def sliver_adjacent(rect, direction):
    if direction[0] < 0:
        return (rect.x-1, rect.y, 1, rect.height)
    elif direction[0] > 0:
        return (rect.x+rect.width, rect.y, 1, rect.height)
    elif direction[1] < 0:
        return (rect.x, rect.y-1, rect.width, 1)
    else:
        return (rect.x, rect.y+rect.height, rect.width, 1)
        
        
    
        
    
    
     
