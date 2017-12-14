import math

def dist(v1, v2):
    dx = v1[0] - v2[0]
    dy = v1[1] - v2[1]
    return math.sqrt(dx*dx + dy*dy)
    
def sub(v1, v2):
    """return v1 - v2"""
    return (v1[0] - v2[0], v1[1] - v2[1])

def add(v1, v2):
    return (v1[0] + v2[0], v1[1] + v2[1])
    
def mag(v1):
    return math.sqrt(v1[0]*v1[0] + v1[1]*v1[1])
    
def normalize(v):
    if is_zero(v):
        raise ValueError("can't normalize a vector of length 0")
    else:
        m = mag(v)
        return (v[0] / m, v[1] / m)
        
def mult(v, a):
    return (v[0]*a, v[1]*a)
        
def is_zero(v):
    return mag(v) < 0.00001
        
def set_length(v, length):
    return mult(normalize(v), length)
   
def intify(v):
    return (round(v[0]), round(v[1]))
    
    
     
