import numpy as np
import math

def convert_bytes(size):
    power = 2**10
    n = 0
    units = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {units[n]}"

def dtryfloat(strf:str):
    try:
        return float(strf)
    except Exception as ex:
        return np.nan  
    
def uv2w(u, v):
    wdir = (180+math.atan2(u, v)/math.pi*180.0) % 360
    wspd = math.sqrt(u*u+v*v)
    return wdir, wspd

def w2uv(wdir, wspd):
    u = -wspd*math.sin(wdir/180*math.pi)
    v = -wspd*math.cos(wdir/180*math.pi)
    return u, v

vdtryfloat=np.vectorize(dtryfloat)
vw2uv=np.vectorize(w2uv)
vuv2w=np.vectorize(uv2w)