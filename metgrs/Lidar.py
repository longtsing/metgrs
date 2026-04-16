import numpy as np
import pandas as pd
import xarray as xr
import os
import os.path
import glob
import math
import re
from datetime import datetime,timedelta
import dateutil.parser
import struct
import types
from joblib import Parallel, delayed
from . import base
originData=base.originData

L0Data=types.new_class('L0Data',(originData,))
L0Datas=types.new_class('L0Datas',(originData,))
CDWLData=types.new_class('CDWLData',(originData,))
CDWLDatas=types.new_class('CDWLDatas',(originData,))


def _decode_zero_terminated_ascii(buf:bytes)->str:
    return buf.split(b'\x00',1)[0].decode('ascii',errors='ignore').strip()


def _parse_cdwl_observe_time_from_filename(fp:str):
    m=re.search(r'_(\d{14})_[BP]_',os.path.basename(fp))
    if(m is None):
        return None
    return datetime.strptime(m.group(1),'%Y%m%d%H%M%S')


def _parse_cdwl_product_text_block(ds:bytes):
    m=re.search(rb'\r\n(\d{3})\r\n',ds)
    if(m is None):
        raise ValueError('无法在文件中找到产品号与数据体起始标记（\\r\\nNNN\\r\\n）。')
    product_number=int(m.group(1).decode('ascii'))
    rows=[]
    for line_b in ds[m.end():].splitlines():
        line=line_b.decode('ascii',errors='ignore').strip()
        if(line==''):
            continue
        if(line=='NNNN'):
            break
        parts=line.split()
        if(len(parts)<4):
            continue
        if(re.fullmatch(r'\d{5}',parts[0]) is None):
            continue

        def _to_float(v:str):
            if('/' in v):
                return np.nan
            return float(v)

        rows.append({
            'Height':float(parts[0]),
            'WindDirection':_to_float(parts[1]),
            'HorizontalWindSpeed':_to_float(parts[2]),
            'VerticalWindSpeed':_to_float(parts[3]),
        })
    data=pd.DataFrame(rows,columns=['Height','WindDirection','HorizontalWindSpeed','VerticalWindSpeed'])
    return product_number,m.start(),data


def readSingleCDWLBinFile(binfile:str):
    '''
    读取单个相干多普勒测风激光雷达 BIN 文件（当前支持产品体为文本表格的文件，如 MR_096）。
    Args:
        binfile: CDWL BIN 文件路径

    Returns:
        CDWLData: 包含基础头信息与解析后的产品数据表
    '''
    cda=CDWLData()
    with open(binfile,'rb') as f:
        ds=f.read()
    if(ds[:4]!=b'CDWL'):
        raise ValueError(f'文件头标识不是 CDWL: {binfile}')

    cda['File_Path']=binfile
    cda['File_Size']=len(ds)
    cda['Magic']='CDWL'
    cda['Version_Raw']=ds[4:8].hex()
    cda['Station_Code']=_decode_zero_terminated_ascii(ds[32:40])
    cda['Station_Name']=_decode_zero_terminated_ascii(ds[48:80])
    cda['Latitude_deg']=struct.unpack('<f',ds[72:76])[0]
    cda['Longitude_deg']=struct.unpack('<f',ds[76:80])[0]
    cda['Station_Height_m']=struct.unpack('<f',ds[80:84])[0]
    cda['Observe_Time']=_parse_cdwl_observe_time_from_filename(binfile)

    product_number,text_offset,data=_parse_cdwl_product_text_block(ds)
    cda['Product_Number']=product_number
    cda['Text_Block_Offset']=text_offset
    cda['Data']=data
    cda.__datas__=data
    return cda


def readCDWLBinFiles(fps:list,use_multiprocess=False,multiproces_corenum=-1):
    '''
    批量读取相干多普勒测风激光雷达 BIN 文件（文本产品体）。
    Args:
        fps: 文件路径列表
        use_multiprocess: 是否使用多进程读取
        multiproces_corenum: 多进程核心数（-1 为全部核心）
    Returns:
        CDWLDatas: CDWL 解析结果列表对象
    '''
    rbds=CDWLDatas()
    if(use_multiprocess):
        rbds['CDWLDatas']=Parallel(n_jobs=multiproces_corenum)(delayed(readSingleCDWLBinFile)(fp) for fp in fps)
    else:
        rbds['CDWLDatas']=[readSingleCDWLBinFile(fp) for fp in fps]
    rbds.__datas__=rbds['CDWLDatas']
    return rbds

def readSingleL0File(l0file:str)->L0Data:
    '''
    读取单个L0激光雷达文件
    Args:
        l0file: L0激光雷达文件路径

    Returns:
        L0Data: 激光雷达L0产品对象
    '''
    l0da=L0Data()
    dts=dateutil.parser.parse(l0file[-34:-20])    
    # dt=dts-timedelta(hours=8)
    l0da['Observe_Time']=dts
    dd=open(l0file,'rb')
    ds=dd.read()
    dd.close()
    pa=0
    channel_count=struct.unpack('H',ds[52:54])[0]
    if(channel_count!=8):
        pa=6
        channel_count=8
    l0da['Channel_Count']=channel_count
    channelmetas=[]
    for i in range(channel_count):
        channelmetas.append(struct.unpack('HHHHHHHH',ds[54+16*i+pa:70+16*i+pa]))
    params=pd.DataFrame(channelmetas,columns=['ID','WaveLength','type','Ratio','BHeight','PTR','CMethod','Count'])
    params['Ratio']=params['Ratio']/100
    params['BHeight']=params['BHeight']/10
    l0da['Channel_Metas']=params
    data=pd.DataFrame()
    for i in range(channel_count):
        data['c'+str(i+1)]=struct.unpack('f'*channelmetas[i][7],ds[channelmetas[i][5]:channelmetas[i][5]+4*channelmetas[i][7]])
    l0da['Data']=data
    return l0da

def readL0Files(fps:list,use_multiprocess=False,multiproces_corenum=-1)->L0Datas:
    '''    
    读取激光雷达文件列表    
    Args:
        fps:文件路径列表
        use_multiprocess:是否使用多进程读取（速度较快但默认不使用）
        multiproces_corenum:多进程核心数（默认为-1，使用全部核心）
    Returns:
        L0Datas:激光雷达对象列表    
    '''
    rbds=L0Datas()
    if(use_multiprocess):
        rbds['L0Datas']=Parallel(n_jobs=multiproces_corenum)(delayed(readSingleL0File)(fp) for fp in fps)
    else:
        rbds['L0Datas']=[readSingleL0File(fp) for fp in fps]
    rbds.__datas__=rbds['L0Datas']
    return rbds


#region 导出成厂家的DAT格式
def L0DataFileToManufactoryDat(l0file,outPath=None):
    l0da=readSingleL0File(l0file)
    data=l0da['Data']
    dts=l0da['Observe_Time']
    params=l0da['Channel_Metas']
    dt=dts-timedelta(hours=8)
    if(outPath==None):
        outPath='./'
    outf=outPath+dts.strftime('%Y/%Y%m%d/')+'S001-SLB001-Standard-'+str(int((dts-datetime(2023,1,1,0)).total_seconds()*2/3600+4275))\
        +'-'+dt.strftime('%y%m%d-%H%M%S')+'.dat'
    outp=open(outf,'w')
    outp.writelines(f'''File version 1.2
Local Time start:{dts.strftime('%H:%M:%S.000')}
Universal Time start:{dt.strftime('%Y-%m-%d %H:%M:%S.000')}
Various data: az=0.00;el=90.00;POWER=ALL_ON,,;Laser=Fire_ON,;LaserFreq=1000;StorageTimeUTC={dts.strftime('%H:%M:%S.000')};az_real=missing;el_real=missing;Servo=,,
Measure type = Standard
Scheduling = Sing=60;AzEnd=0;AzStart=0;ElEnd=90;ElStart=90;GlobScan=900;GlobRep=30;Chan=E355P,E355S,E532P,E532S,R386,R407,R607,E1064;RepRest=30;StepsAzim=1;StepsElev=1;PreTrig=10;T0_UT=102700.000;
Nota schedule =
Positioning = 0,0; 12; SLB001
Params: T=21; H=20; P=1002; R=15
Serie=12 Cycle=3
#######################################
     CHANNELS   PARAMS
E355P	E355S	R386	R407	E532P	E532S	R607	E1064	
''')
    outp.writelines('\t'.join(['%4d'%x for x in list(params['Count'].values)]))
    outp.writelines('''
100	100	100	100	100	100	100	100	
55000	55000	55000	55000	55000	55000	55000	55000	
DIG	DIG	DIG	DIG	DIG	DIG	DIG	DIG	
1000	1000	1000	1000	1000	1000	1000	1000	
-------------------------------------------
''')
    outp.writelines('''
'''.join(['\t'.join(['%d'%d for d in row]) for row in data.values]))
    outp.writelines('''
''')
    outp.close()
#endregion
