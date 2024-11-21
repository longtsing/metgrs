from datetime import datetime,timedelta
import dateutil.parser
import dateutil.rrule
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import types
from joblib import Parallel, delayed
from . import base
originData=base.originData

#region 绘图参数
ref_colors=[
    '#FFFFFF',
    '#000080',
    '#042AC9',
    '#0852D1',
    '#0C7AD5',
    '#01A0F6',
    '#00ECEC',
    '#00D800',
    '#019000',
    '#FFFF00',
    '#E7C000',
    '#FF9000',
    '#FF0000',
    '#D60000',
    '#FFFFFF'
]
ref_levels=[-30,-20,-10,-5,0,5,10,15,20,25,30,35,40]
ref_cmap = (mpl.colors.ListedColormap(ref_colors[1:-1]).with_extremes(over=ref_colors[-1], under=ref_colors[0]))
ref_norm = mpl.colors.BoundaryNorm(ref_levels, ref_cmap.N)

velocity_colors=[
    '#FFFFFF',
    '#042948',
    '#053761',
    '#064275',
    '#094C85',
    '#0A5797',
    '#0B62AB',
    '#0B6EBF',
    '#0C7AD5',
    '#01A0F6',
    '#80E3FF',
    '#00E0FE',
    '#00B0B0',
    '#00FE00',
    '#00C400',
    '#008000',
    '#D8D2D8',
    '#E7E3E8',
    '#FE0000',
    '#FE5858',
    '#FEB0B0',
    '#FE7C00',
    '#FED200',
    '#FEFE00',
    '#9B0CE2',
    '#8B0CCB',
    '#7E0BB7',
    '#6F0AA2',
    '#620A8F',
    '#57087F',
    '#4A076C',
    '#3D0758',
    '#2E0543',
    "#FFFFFF",
]
velocity_levels=[-18,-16,-15,-14,-13,-12,-11,-9,-8,-7,-6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
velocity_cmap = (mpl.colors.ListedColormap(velocity_colors[1:-1]).with_extremes(over=velocity_colors[-1], under=velocity_colors[0]))
velocity_norm = mpl.colors.BoundaryNorm(velocity_levels, velocity_cmap.N)

spectrumwith_colors=[
    "#FFFFFF",
    "#E7E3E7",
    "#7BE3E7",
    "#00E3E7",
    "#00B2B5",
    "#00FFFF",
    "#00C700",
    "#008200",
    "#FFFF00",
    "#FFD300",
    "#FF7D00",
    "#FFB2B5",
    "#AD595A",
    "#75005F",
    "#FFFFFF",
]
spectrumwith_levels=[0,0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6]
spectrumwith_cmap = (mpl.colors.ListedColormap(spectrumwith_colors[1:-1]).with_extremes(over=spectrumwith_colors[-1], under=spectrumwith_colors[0]))
spectrumwith_norm = mpl.colors.BoundaryNorm(spectrumwith_levels, spectrumwith_cmap.N)

snr_colors=[
    "#FFFFFF",
    "#0535CD",
    "#0A67D3",
    "#109AD8",
    "#15CCDE",
    "#1AFFE3",
    "#48FFB6",
    "#76FF88",
    "#A3FF5B",
    "#D1FF2D",
    "#FFFF00",
    "#F5CC00",
    "#EC9900",
    "#E26601",
    "#D93301",
    "#FFFFFF",
]
snr_levels=[-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,35,40]
snr_cmap = (mpl.colors.ListedColormap(snr_colors[1:-1]).with_extremes(over=snr_colors[-1], under=snr_colors[0]))
snr_norm = mpl.colors.BoundaryNorm(snr_levels, snr_cmap.N)

#endregion

#region 元数据配置
generic_header=np.dtype(
     [
         ('MagicNumber', 'i4'),
         ('MajorVersion', 'i2'),
         ('MinorVersion', 'i2'),
         ('GenericType', 'i4'),
         ('Reserved', 'S20'),
     
     ]
)
site_config=np.dtype(
     [
         ('Site_Code', 'S8'),
         ('Site_Name', 'S24'),
         ('Latitude', 'f4'),
         ('Longitude', 'f4'),
         ('Antenna_Height', 'f4'),
         ('Ground_Height', 'f4'),
         ('Amend_North', 'f4'),
         ('RDA_Version', 'i2'),
         ('Radar_Type', 'i2'),
         ('Manufacturers', 'S6'),
         ('Reserved', 'S10'),
     
     ]
)
radar_config=np.dtype(
     [
         ('Frequency', 'f4'),
         ('Wavelength', 'f4'),
         ('Beam_Width_Hori', 'f4'),
         ('Beam_Width_Vert', 'f4'),
         ('Transmitter_peak_power', 'f4'),
         ('Antenna_gain', 'f4'),
         ('Total_loss', 'f4'),
         ('Receiver_gain', 'f4'),
         ('First_side', 'f4'),
         ('Receiver_dynamic_Range', 'f4'),
         ('Receiver_Sensitivity', 'f4'),
         ('Band_Width', 'f4'),
         ('Max_Explore_Range', 'u4'),
         ('Distance_solution', 'u2'),
         ('Polarization_Type', 'u2'),
         ('Reserved', 'S96')
     
     ]
)
task_config=np.dtype(
     [
         ('Task_Name', 'S16'),
         ('Task_Description', 'S96'),
         ('Polarization_Way', 'i2'),
         ('Scan_Type', 'i2'),
         ('Pulse_Width_1', 'i4'),
         ('Pulse_Width_2', 'i4'),
         ('Pulse_Width_3', 'i4'),
         ('Pulse_Width_4', 'i4'),
         ('Scan_Start_Time', 'u8'),
         ('Cut_Number', 'i4'),
         ('Horizontal_Noise', 'f4'),
         ('Vertical_Noise', 'f4'),
         ('Horizontal_Calibration1', 'f4'),
         ('Horizontal_Calibration2', 'f4'),
         ('Horizontal_Calibration3', 'f4'),
         ('Horizontal_Calibration4', 'f4'),
         ('Vertical_Calibration1', 'f4'),
         ('Vertical_Calibration2', 'f4'),
         ('Vertical_Calibration3', 'f4'),
         ('Vertical_Calibration4', 'f4'),
         ('Horizontal_Noise_Temperature', 'f4'),
         ('Vertical_Noise_Temperature', 'f4'),
         ('ZDR_Calibration', 'f4'),
         ('PHIDP_Calibration', 'f4'),
         ('LDR_Calibration', 'f4'),
         ('Number_of_coherent_accumulation_1', 'S1'),
         ('Number_of_coherent_accumulation_2', 'S1'),
         ('Number_of_coherent_accumulation_3', 'S1'),
         ('Number_of_coherent_accumulation_4', 'S1'),
         ('FFT_Count_1', 'u2'),
         ('FFT_Count_2', 'u2'),
         ('FFT_Count_3', 'u2'),
         ('FFT_Count_4', 'u2'),
         ('Accumulation_of_power_spectrum_1', 'S1'),
         ('Accumulation_of_power_spectrum_2', 'S1'),
         ('Accumulation_of_power_spectrum_3', 'S1'),
         ('Accumulation_of_power_spectrum_4', 'S1'),
         ('Pulse_width_1_starting_position', 'u4'),
         ('Pulse_width_2_starting_position', 'u4'),
         ('Pulse_width_3_starting_position', 'u4'),
         ('Pulse_width_4_starting_position', 'u4'),
         ('Reserved', 'S20'),
     ]
)
cut_config=np.dtype([
    ('Process_Mode', 'i2'),  # SHORT
    ('Wave_Form', 'i2'),  # SHORT
    ('PRF_1', 'f4'),  # FLOAT
    ('PRF_2', 'f4'),  # FLOAT
    ('PRF_3', 'f4'),  # FLOAT
    ('PRF_4', 'f4'),  # FLOAT
    ('PRF_Mode', 'i2'),  # SHORT
    ('Pulse_width_combination_mode', 'i2'),  # SHORT
    ('Azimuth', 'f4'),  # FLOAT
    ('Elevation', 'f4'),  # FLOAT
    ('Start_Angle', 'f4'),  # FLOAT
    ('End_Angle', 'f4'),  # FLOAT
    ('Angular_Resolution', 'f4'),  # FLOAT
    ('Scan_Speed', 'f4'),  # FLOAT
    ('Log_Resolution', 'i4'),  # INT
    ('Doppler_Resolution', 'i4'),  # INT
    ('Start_Range', 'i4'),  # INT
    ('Phase_Mode', 'i4'),  # INT
    ('Atmospheric_Loss', 'f4'),  # FLOAT
    ('Nyquist_Speed', 'f4'),  # FLOAT
    ('Misc_Filter_Mask', 'i4'),  # INT
    ('SQI_Threshold', 'f4'),  # FLOAT
    ('SIG_Threshold', 'f4'),  # FLOAT
    ('CSR_Threshold', 'f4'),  # FLOAT
    ('LOG_Threshold', 'f4'),  # FLOAT
    ('CPA_Threshold', 'f4'),  # FLOAT
    ('PMI_Threshold', 'f4'),  # FLOAT
    ('DPLOG_Threshold', 'f4'),  # FLOAT
    ('Thresholds_r', 'S12'),  # CAHR*12 (12 Bytes)
    ('dBT_Mask', 'i4'),  # INT
    ('dBZ_Mask', 'i4'),  # INT
    ('Velocity_Mask', 'i4'),  # INT
    ('Spectrum_Width_Mask', 'i4'),  # INT
    ('DP_Mask', 'i4'),  # INT
    ('Mask_Reserved', 'S12'),  # 12 Bytes
    ('Scan_Sync', 'i4'),  # INT
    ('Direction', 'i4'),  # INT
    ('Ground_Clutter_Classifier_Type', 'i2'),  # SHORT
    ('Ground_Clutter_Filter_Type', 'i2'),  # SHORT
    ('Ground_Clutter_Filter_Notch_Width', 'i2'),  # SHORT (0.1 m/s)
    ('Ground_Clutter_Filter_Window', 'i2'),  # SHORT
    ('Reserved', 'S92')  # 92 Bytes
])
radial_header=np.dtype([
    ('Radial_State', 'i2'),  # SHORT
    ('Spot_Blank', 'i2'),  # SHORT
    ('Sequence_Number', 'u2'),  # USHORT
    ('Radial_Number', 'u2'),  # USHORT
    ('Moment_Number', 'u2'),  # USHORT
    ('Elevation_Number', 'u2'),  # USHORT
    ('Azimuth', 'f4'),  # FLOAT
    ('Elevation', 'f4'),  # FLOAT
    ('Seconds', 'u8'),  # ULONG
    ('Microseconds', 'u4'),  # UINT
    ('Length_of_data', 'u4'),  # UINT
    ('Duration_Seconds', 'u2'),  # USHORT
    ('Max_FFT_Count', 'u2'),  # USHORT
    ('Reserved', 'S24')  # 24 Bytes
])
data_unit_header=np.dtype([
    ('Data_Type', 'u2'),  # USHORT
    ('Scale', 'u2'),  # USHORT
    ('Offset', 'u2'),  # USHORT
    ('Bin_Bytes', 'u2'),  # USHORT
    ('Bin_Number', 'u2'),  # USHORT
    ('Flags', 'i2'),  # SHORT
    ('Data_Length', 'i4'),  # INT
    ('Reserved', 'S16')  # 16 Bytes
])

#endregion

SingleBaseData=types.new_class('SingleBaseData',(originData,))

BaseDatas=types.new_class('BaseDatas',(originData,))

unobdata=999999
nodata=999999

def isInt(istr):
    try:
        int(istr)
        return True
    except Exception as e:
        return False

def readSingleBaseData(fp:str)->SingleBaseData:
    '''    
    读取云雷达文件    
    Args:
        fp:文件路径
    Returns:
        dict:云雷达对象    
    '''
    with open(fp,'rb') as f:
        bs=f.read()
    ylddo=SingleBaseData()
    data=np.frombuffer(bs[:32],generic_header)
    ylddo['generic_header'] = {name: data[name][0] for name in data.dtype.names}
    data=np.frombuffer(bs[32:104],site_config)
    ylddo['site_config']  = {name: data[name][0] for name in data.dtype.names}
    data=np.frombuffer(bs[104:256],radar_config)
    ylddo['radar_config'] = {name: data[name][0] for name in data.dtype.names}
    data=np.frombuffer(bs[256:512],task_config)
    ylddo['task_config'] = {name: data[name][0] for name in data.dtype.names}
    ylddo['task_config']['Scan_Start_Time']=ylddo['task_config']['Scan_Start_Time'].astype('datetime64[s]')
    Cut_Number=ylddo['task_config']['Cut_Number']
    ylddo['cut_configs']=[]
    readed_point=512
    for i in range(Cut_Number):
        data=np.frombuffer(bs[readed_point:readed_point+cut_config.itemsize],cut_config)
        ylddo['cut_configs'].append({name: data[name][0] for name in data.dtype.names})
        readed_point=readed_point+cut_config.itemsize
    data=np.frombuffer(bs[readed_point:readed_point+radial_header.itemsize],radial_header)
    ylddo['radial_header'] = {name: data[name][0] for name in data.dtype.names}
    readed_point=readed_point+radial_header.itemsize
    ylddo['datas']=[]
    ylddo['data_infos']=[]
    for i in range(ylddo['radial_header']['Moment_Number']):
        data=np.frombuffer(bs[readed_point:readed_point+data_unit_header.itemsize],data_unit_header)
        datainfo={name: data[name][0] for name in data.dtype.names}
        data_type_value = datainfo['Data_Type']
        if data_type_value == 1:
            datainfo['Data_Name'] = 'Z1'
        elif data_type_value == 2:
            datainfo['Data_Name'] = 'V1'
        elif data_type_value == 3:
            datainfo['Data_Name'] = 'W1'
        elif data_type_value == 4:
            datainfo['Data_Name'] = 'SNR1'
        elif data_type_value == 5:
            datainfo['Data_Name'] = 'FFT1'
        elif data_type_value == 6:
            datainfo['Data_Name'] = 'Zc1'
        elif 6 <= data_type_value <= 16:
            datainfo['Data_Name'] = 'Reserved'
        elif data_type_value == 17:
            datainfo['Data_Name'] = 'Z2'
        elif data_type_value == 18:
            datainfo['Data_Name'] = 'V2'
        elif data_type_value == 19:
            datainfo['Data_Name'] = 'W2'
        elif data_type_value == 20:
            datainfo['Data_Name'] = 'SNR2'
        elif data_type_value == 21:
            datainfo['Data_Name'] = 'FFT2'
        elif data_type_value == 22:
            datainfo['Data_Name'] = 'Zc2'
        elif 22 <= data_type_value <= 32:
            datainfo['Data_Name'] = 'Reserved'
        elif data_type_value == 33:
            datainfo['Data_Name'] = 'ZDR'
        elif data_type_value == 34:
            datainfo['Data_Name'] = 'LDR'
        elif data_type_value == 35:
            datainfo['Data_Name'] = 'CC'
        elif data_type_value == 36:
            datainfo['Data_Name'] = 'DP'# ΦDP
        elif data_type_value == 37:
            datainfo['Data_Name'] = 'KDP'
        elif data_type_value == 38:
            datainfo['Data_Name'] = 'Re'
        elif data_type_value == 39:
            datainfo['Data_Name'] = 'VIL'
        elif data_type_value == 40:
            datainfo['Data_Name'] = 'HCL'
        elif data_type_value == 41:
            datainfo['Data_Name'] = 'SQI'
        elif data_type_value == 42:
            datainfo['Data_Name'] = 'CPA'
        elif data_type_value == 43:
            datainfo['Data_Name'] = 'CF'
        elif data_type_value == 44:
            datainfo['Data_Name'] = 'CP'
        elif data_type_value == 45:
            datainfo['Data_Name'] = 'BB'
        elif data_type_value == 46:
            datainfo['Data_Name'] = 'Cn2'
        elif 47 <= data_type_value <= 49:
            datainfo['Data_Name'] = 'Reserved'
        elif data_type_value == 50:
            datainfo['Data_Name'] = 'IWC'
        elif 51 <= data_type_value <= 64:
            datainfo['Data_Name'] = 'Reserved'
        # print(datainfo)
        ylddo['data_infos'].append(datainfo)
        if(datainfo['Data_Type']>0):
            readed_point=readed_point+data_unit_header.itemsize
            data=np.frombuffer(bs[readed_point:readed_point+datainfo['Bin_Bytes']*datainfo['Data_Length']],'i'+str(datainfo['Bin_Bytes']))
            data=np.where(data==0,nodata,(data-datainfo['Offset'])/datainfo['Scale'])
            ylddo['datas'].append(data)
            readed_point=readed_point+datainfo['Bin_Bytes']*datainfo['Data_Length']
        else:
            ylddo['datas'].append(None)
    ylddo['datas']=np.array(ylddo['datas'])
    return ylddo

def readBaseDatas(fps:list,use_multiprocess=False,multiproces_corenum=-1)->BaseDatas:
    '''    
    读取云雷达文件列表    
    Args:
        fps:文件路径列表
        use_multiprocess:是否使用多进程读取（速度较快但默认不使用）
        multiproces_corenum:多进程核心数（默认为-1，使用全部核心）
    Returns:
        list:云雷达对象列表    
    '''
    rbds=BaseDatas()
    if(use_multiprocess):
        rbds['BaseDatas']=Parallel(n_jobs=multiproces_corenum)(delayed(readSingleBaseData)(fp) for fp in fps)
    else:
        rbds['BaseDatas']=[readSingleBaseData(fp) for fp in fps]
    for i,ld in enumerate(rbds['BaseDatas']):
        rbds.append(ld)    
    return rbds

def BaseDatasgetDatas(self, data_name='Z1',fixData_Length='max',unobdata=unobdata):
    '''    
    获取云雷达数据    
    Args:
        data_name:数据名称
    Returns:
        list:数据列表    
    '''
    # 使用列表推导式获取符合条件的数据索引和数据    
    dataindexs, datas = zip(*[(j, bd['datas'][j]) for bd in self.BaseDatas for j, dis in enumerate(bd['data_infos']) if dis['Data_Name'] == data_name])

    # 直接计算最大长度并在合适的数据结构上扩展数据
    if(fixData_Length=='max'):
        maxlendatas = max(map(len, datas))
        datas = [list(d) + [unobdata] * (maxlendatas - len(d)) for d in datas]
    else:
        if(fixData_Length=='min'):
            maxlendatas = min(map(len, datas))
            datas = [list(d)[:maxlendatas] for d in datas]
        else:
            if(isInt(fixData_Length)):
                maxlendatas = int(fixData_Length)
                datas = [list(d)[:maxlendatas] if(len(d)>maxlendatas) else list(d) + [unobdata] * (maxlendatas - len(d))  for d in datas]
    
    # 转换为numpy数组
    datas = np.array(datas)

    times=list(map(lambda x:x['task_config']['Scan_Start_Time'].astype(datetime)+timedelta(hours=8),self.BaseDatas))
    heights=np.arange(
        self.BaseDatas[0]['cut_configs'][0]['Start_Range'],
        self.BaseDatas[0]['cut_configs'][0]['Start_Range']+self.BaseDatas[0]['cut_configs'][0]['Log_Resolution']*maxlendatas,
        self.BaseDatas[0]['cut_configs'][0]['Log_Resolution']
    )/1000


    return times,heights,datas

BaseDatas.getDatas=BaseDatasgetDatas

def BaseDatasplot(self, plot_type='ref', figsize=(18,12), cmap=None, norm=None,show=True,savepath=None):
    '''    
    绘制云雷达数据    
    Args:
        plot_type:绘图类型,ref:反射率,velocity:速度,spectrumwith:谱宽,snr:信噪比
        figsize:图像尺寸
        cmap:颜色映射
        norm:归一化    
    '''
    if plot_type.lower()=='ref':
        data_name='Z1'
        unitstr='dbZ'
        if(cmap is None):
            cmap=ref_cmap
        if(norm is None):
            norm=ref_norm
    elif plot_type.lower()=='velocity':
        data_name='V1'
        unitstr='m/s'
        if(cmap is None):
            cmap=velocity_cmap
        if(norm is None):
            norm=velocity_norm
    elif plot_type.lower()=='spectrumwith':
        data_name='W1'
        unitstr='m/s'
        if(cmap is None):
            cmap=spectrumwith_cmap
        if(norm is None):
            norm=spectrumwith_norm
    elif plot_type.lower()=='snr':
        data_name='SNR1'
        unitstr='db'
        if(cmap is None):
            cmap=snr_cmap
        if(norm is None):
            norm=snr_norm
    else:
        raise ValueError('plot_type must be ref,velocity,spectrumwith or snr')

    times,heights,datas=self.getDatas(data_name)

    fig,ax=plt.subplots(figsize=figsize)
    im = ax.pcolormesh(times, heights, datas.T, cmap=cmap,norm=norm)
    cbar = plt.colorbar(im, orientation='horizontal', extend='max', extendrect=True, extendfrac='auto', pad=0.08, aspect=35)
    cbar.set_label(plot_type+' ('+unitstr+')')
    ax.set_ylabel("Height (km)")
    ax.set_xlabel("Time (BJT)")
    if(show):
        plt.show()
    else:
        plt.close(fig)
    if(savepath is not None):
        fig.savefig(savepath,bbox_inches='tight')

BaseDatas.plot=BaseDatasplot
