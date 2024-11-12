import numpy as np
import pandas as pd
import xarray as xr
import os
import os.path
import glob
import math
from datetime import datetime,timedelta
import dateutil.parser
import struct
import types
from joblib import Parallel, delayed
from . import base
originData=base.originData

L0Data=types.new_class('L0Data',(originData,))
L0Datas=types.new_class('L0Datas',(originData,))

def readSingleL0File(l0file:str)->L0Data:
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
    for i,ld in enumerate(rbds['L0Datas']):
        rbds.append(ld)
    return rbds


#region 导出成厂家的DAT格式
def L0DataFileToManufactoryDat(l0file,outPath=None):
    l0da=readL0File(l0file)
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
