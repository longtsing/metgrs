import numpy as np
import math

def isInt(istr:str)->bool:
    try:
        int(istr)
        return True
    except Exception as e:
        return False

def isFloat(istr:str)->bool:
    try:
        isFloat(istr)
        return True
    except Exception as e:
        return False


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

def parse_element(element):
    if(len(element)>0):
        tags=list(map(lambda x:x.tag,element))
        # print(len(set(tags))==len(element))
        if(len(set(tags))==len(element)):
            parsed_data = {}
            for child in element:
                parsed_data[child.tag]=parse_element(child)
        else:
            parsed_data = []
            for child in element:
                parsed_data.append(parse_element(child))
    else:
        if(len(element.keys())>0):
            parsed_data= {attr: element.get(attr) for attr in element.keys()}
        else:
            parsed_data= element.text.strip()
    return parsed_data

vdtryfloat=np.vectorize(dtryfloat)
vw2uv=np.vectorize(w2uv)
vuv2w=np.vectorize(uv2w)