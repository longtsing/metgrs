from datetime import datetime,timedelta
import dateutil.parser
import dateutil.rrule
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib as mpl
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
from joblib import Parallel, delayed
from . import base,Utils

isInt=Utils.isInt
parse_element=Utils.parse_element

def _decode_bytes(val, encoding='gbk'):
    if isinstance(val, bytes):
        return val.split(b'\x00')[0].decode(encoding, errors='ignore')
    return val

def _dict_from_struct(data, dtype, encoding='ascii'):
    result = {}
    for name in dtype.names:
        val = data[name][0]
        result[name] = _decode_bytes(val, encoding)
    return result

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
ref_cmap = (colors.ListedColormap(ref_colors[1:-1]).with_extremes(over=ref_colors[-1], under=ref_colors[0]))
ref_norm = colors.BoundaryNorm(ref_levels, ref_cmap.N)

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
velocity_cmap = (colors.ListedColormap(velocity_colors[1:-1]).with_extremes(over=velocity_colors[-1], under=velocity_colors[0]))
velocity_norm = colors.BoundaryNorm(velocity_levels, velocity_cmap.N)

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
spectrumwith_cmap = (colors.ListedColormap(spectrumwith_colors[1:-1]).with_extremes(over=spectrumwith_colors[-1], under=spectrumwith_colors[0]))
spectrumwith_norm = colors.BoundaryNorm(spectrumwith_levels, spectrumwith_cmap.N)

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
snr_cmap = (colors.ListedColormap(snr_colors[1:-1]).with_extremes(over=snr_colors[-1], under=snr_colors[0]))
snr_norm = colors.BoundaryNorm(snr_levels, snr_cmap.N)

#endregion

#region 元数据配置
GenericHeader=np.dtype(
     [
         ('MagicNumber', 'i4'),
         ('MajorVersion', 'i2'),
         ('MinorVersion', 'i2'),
         ('GenericType', 'i4'),
         ('Reserved', 'S20'),
     
     ]
)
SiteConfig=np.dtype(
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
RadarConfig=np.dtype(
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
TaskConfig=np.dtype(
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
CutConfig=np.dtype([
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
RadialHeader=np.dtype([
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
FFT_extra_unit_header = [
    ['FFT_Count', 'u2', [1024,]],  # SHORT* L
    ['Number_of_coherent_accumulation', 'u1', [1024,]],  # CHAR* L
    ['Waveform_Number', 'u1', [1024,]],  # CHAR* L
    ['Accumulation_of_power_spectrum', 'u1', [1024,]]  # CHAR* L
]
#endregion

unobdata=999999
nodata=np.nan

def readSingleFFTData(fp:str):
    FFTScale=100.0
    FFTOffset=32002.0
    with open(fp,'rb') as f:
        bs=f.read()
    bsoffset_left=0
    bsoffset_right=bsoffset_left+GenericHeader.itemsize
    data=np.frombuffer(bs[bsoffset_left:bsoffset_right], GenericHeader)
    generic_header=_dict_from_struct(data, GenericHeader)
    bsoffset_left=bsoffset_right
    bsoffset_right=bsoffset_left+SiteConfig.itemsize
    data=np.frombuffer(bs[bsoffset_left:bsoffset_right], SiteConfig)
    site_config=_dict_from_struct(data, SiteConfig)
    bsoffset_left=bsoffset_right
    bsoffset_right=bsoffset_left+RadarConfig.itemsize
    data=np.frombuffer(bs[bsoffset_left:bsoffset_right], RadarConfig)
    radar_config=_dict_from_struct(data, RadarConfig)
    bsoffset_left=bsoffset_right
    bsoffset_right=bsoffset_left+TaskConfig.itemsize
    data=np.frombuffer(bs[bsoffset_left:bsoffset_right], TaskConfig)
    task_config=_dict_from_struct(data, TaskConfig)
    task_config['Scan_Start_Time']=task_config['Scan_Start_Time'].astype('datetime64[s]')
    Cut_Number=task_config['Cut_Number']
    cut_configs=[]
    for i in range(Cut_Number):
        bsoffset_left = bsoffset_right
        bsoffset_right = bsoffset_left + CutConfig.itemsize
        data=np.frombuffer(bs[bsoffset_left:bsoffset_right], CutConfig)
        cut_configs.append(_dict_from_struct(data, CutConfig))
    bsoffset_left = bsoffset_right
    bsoffset_right = bsoffset_left + RadialHeader.itemsize
    data=np.frombuffer(bs[bsoffset_left:bsoffset_right], RadialHeader)
    radial_header=_dict_from_struct(data, RadialHeader)
    data_infos=[]
    raw_data=[]
    for i in range(radial_header['Moment_Number']):
        bsoffset_left = bsoffset_right
        bsoffset_right = bsoffset_left + data_unit_header.itemsize
        data=np.frombuffer(bs[bsoffset_left:bsoffset_right], data_unit_header)
        datainfo=_dict_from_struct(data, data_unit_header)
        FFT_extra_unit_headeri=FFT_extra_unit_header.copy()
        for k in range(len(FFT_extra_unit_headeri)):
            FFT_extra_unit_headeri[k][2]=datainfo['Bin_Number']
            FFT_extra_unit_headeri[k]=tuple(FFT_extra_unit_headeri[k])
        FFT_extra_unit_headeri=np.dtype(FFT_extra_unit_headeri)
        bsoffset_left = bsoffset_right
        bsoffset_right = bsoffset_left + FFT_extra_unit_headeri.itemsize
        data=np.frombuffer(bs[bsoffset_left:bsoffset_right], FFT_extra_unit_headeri)
        datainfo.update({name: data[name][0] for name in data.dtype.names})
        data_infos.append(datainfo)
        bsoffset_left = bsoffset_right
        bsoffset_right = bsoffset_left +int(datainfo['Bin_Bytes'])*int(datainfo['Bin_Number'])
        raw_data.append((np.frombuffer(
            bs[bsoffset_left:bsoffset_right],
            dtype='u2',count=2*int(radial_header['Max_FFT_Count'])*int(datainfo['Bin_Number'])
        ).reshape((int(datainfo['Bin_Number']),int(radial_header['Max_FFT_Count']),2))-FFTOffset)/FFTScale)
    arr=np.array(raw_data)
    arr=np.expand_dims(arr,1)
    heights = np.arange(
        cut_configs[0]['Start_Range'],
        cut_configs[0]['Start_Range'] + cut_configs[0]['Doppler_Resolution'] * data_infos[0]['Bin_Number'],
        cut_configs[0]['Log_Resolution']
    )
    ds=xr.Dataset(
        data_vars={f'FFT{i}':(['time','height','FFT_index','dtype'],arr[i]) for i in range(radial_header['Moment_Number'])},
        coords={
            'time':[task_config['Scan_Start_Time'].astype(datetime)],
            'height': heights,
            'index':range(radial_header['Max_FFT_Count']),
            'dtype':['flag','value']
        },
        attrs={
            'GenericHeader': generic_header,
            'SiteConfig': site_config,
            'RadarConfig': radar_config,
            'TaskConfig': task_config,
            'CutConfigs': cut_configs,
            'RadialHeader': radial_header,
            'DataInfos': data_infos,
            'time_count':1,
            'height_count': len(heights),
            'time_reference': 'UTC',
            'height_unit': 'meter',
        }
    )
    return ds

def readFFTDatas(fps:list, use_multiprocess=False, multiproces_corenum=-1):
    if use_multiprocess:
        datasets = Parallel(n_jobs=multiproces_corenum)(delayed(readSingleFFTData)(fp) for fp in fps)
    else:
        datasets = [readSingleFFTData(fp) for fp in fps]
    valid = [ds for ds in datasets if ds is not None]
    if not valid:
        return None
    return base.concat_datasets(valid, dim='time')


def _map_data_type(data_type_value):
    mapping = {
        1: 'Z1', 2: 'V1', 3: 'W1', 4: 'SNR1', 5: 'FFT1', 6: 'Zc1',
        17: 'Z2', 18: 'V2', 19: 'W2', 20: 'SNR2', 21: 'FFT2', 22: 'Zc2',
        33: 'ZDR', 34: 'LDR', 35: 'CC', 36: 'DP', 37: 'KDP',
        38: 'Re', 39: 'VIL', 40: 'HCL', 41: 'SQI', 42: 'CPA',
        43: 'CF', 44: 'CP', 45: 'BB', 46: 'Cn2', 50: 'IWC',
    }
    if data_type_value in mapping:
        return mapping[data_type_value]
    if 7 <= data_type_value <= 16 or 23 <= data_type_value <= 32 or 47 <= data_type_value <= 49 or 51 <= data_type_value <= 64:
        return 'Reserved'
    return 'Other'


def readSingleBaseData(fp:str):
    with open(fp,'rb') as f:
        bs=f.read()
    bsoffset_left=0
    bsoffset_right=bsoffset_left+GenericHeader.itemsize
    data=np.frombuffer(bs[bsoffset_left:bsoffset_right], GenericHeader)
    generic_header=_dict_from_struct(data, GenericHeader)
    bsoffset_left=bsoffset_right
    bsoffset_right=bsoffset_left+SiteConfig.itemsize
    data=np.frombuffer(bs[bsoffset_left:bsoffset_right], SiteConfig)
    site_config=_dict_from_struct(data, SiteConfig)
    bsoffset_left=bsoffset_right
    bsoffset_right=bsoffset_left+RadarConfig.itemsize
    data=np.frombuffer(bs[bsoffset_left:bsoffset_right], RadarConfig)
    radar_config=_dict_from_struct(data, RadarConfig)
    bsoffset_left=bsoffset_right
    bsoffset_right=bsoffset_left+TaskConfig.itemsize
    data=np.frombuffer(bs[bsoffset_left:bsoffset_right], TaskConfig)
    task_config=_dict_from_struct(data, TaskConfig)
    task_config['Scan_Start_Time']=task_config['Scan_Start_Time'].astype('datetime64[s]')
    Cut_Number=task_config['Cut_Number']
    cut_configs=[]
    for i in range(Cut_Number):
        bsoffset_left = bsoffset_right
        bsoffset_right = bsoffset_left + CutConfig.itemsize
        data=np.frombuffer(bs[bsoffset_left:bsoffset_right], CutConfig)
        cut_configs.append(_dict_from_struct(data, CutConfig))
    bsoffset_left = bsoffset_right
    bsoffset_right = bsoffset_left + RadialHeader.itemsize
    data=np.frombuffer(bs[bsoffset_left:bsoffset_right], RadialHeader)
    radial_header=_dict_from_struct(data, RadialHeader)
    data_arrays=[]
    data_infos=[]
    for i in range(radial_header['Moment_Number']):
        bsoffset_left = bsoffset_right
        bsoffset_right = bsoffset_left + data_unit_header.itemsize
        data=np.frombuffer(bs[bsoffset_left:bsoffset_right], data_unit_header)
        datainfo=_dict_from_struct(data, data_unit_header)
        datainfo['Data_Name'] = _map_data_type(datainfo['Data_Type'])
        data_infos.append(datainfo)
        if datainfo['Data_Type'] > 0:
            bsoffset_left = bsoffset_right
            bsoffset_right = bsoffset_left + datainfo['Data_Length']
            raw=np.frombuffer(bs[bsoffset_left:bsoffset_right],'i'+str(datainfo['Bin_Bytes']))
            data_arrays.append(np.where(raw==0, nodata, (raw-datainfo['Offset'])/datainfo['Scale']))
        else:
            data_arrays.append(None)
    varnames=[di['Data_Name'] for di in data_infos]
    dvar = {k: v for k, v in zip(varnames, data_arrays) if v is not None}
    Doppler_Resolution=cut_configs[0]['Doppler_Resolution']
    if Doppler_Resolution<=0:
        Doppler_Resolution=1
    heights = np.arange(
        cut_configs[0]['Start_Range'],
        cut_configs[0]['Start_Range'] + Doppler_Resolution * data_infos[0]['Bin_Number'],
        Doppler_Resolution
    )
    ds = xr.Dataset(
        data_vars={key: (['time','height'], dvar[key][np.newaxis,:]) for key in dvar.keys()},
        coords={
            'time':[task_config['Scan_Start_Time'].astype(datetime)],
            'height': heights
        },
        attrs={
            'GenericHeader': generic_header,
            'SiteConfig': site_config,
            'RadarConfig': radar_config,
            'TaskConfig': task_config,
            'CutConfigs': cut_configs,
            'RadialHeader': radial_header,
            'DataInfos': data_infos,
            'time_count':1,
            'height_count': len(heights),
            'time_reference': 'UTC',
            'height_unit': 'meter',
        }
    )
    return ds


def readBaseDatas(fps:list, use_multiprocess=False, multiproces_corenum=-1, fixData_Length='max'):
    if use_multiprocess:
        datasets = Parallel(n_jobs=multiproces_corenum)(delayed(readSingleBaseData)(fp) for fp in fps)
    else:
        datasets = [readSingleBaseData(fp) for fp in fps]
    valid = [ds for ds in datasets if ds is not None]
    if not valid:
        return None
    if fixData_Length == 'max':
        maxlendatas = max(ds.height_count for ds in valid)
    elif fixData_Length == 'min':
        maxlendatas = min(ds.height_count for ds in valid)
    elif isInt(fixData_Length):
        maxlendatas = int(fixData_Length)
    else:
        maxlendatas = max(ds.height_count for ds in valid)
    Doppler_Resolution = valid[0].attrs['CutConfigs'][0]['Log_Resolution']
    if Doppler_Resolution <= 0:
        Doppler_Resolution = 1
    heights = np.arange(
        valid[0].attrs['CutConfigs'][0]['Start_Range'],
        valid[0].attrs['CutConfigs'][0]['Start_Range'] + Doppler_Resolution * maxlendatas,
        Doppler_Resolution
    )
    varnames = list(set(vn for ds in valid for vn in ds.data_vars))
    times = [ds.coords['time'].values[0] for ds in valid]
    datavars = {}
    for key in varnames:
        dds = [np.squeeze(ds[key].values).tolist() if key in ds else [unobdata]*valid[0].attrs['height_count'] for ds in valid]
        ddas = [list(d)[:maxlendatas] if len(d) > maxlendatas else list(d) + [unobdata] * (maxlendatas - len(d)) for d in dds]
        datavars[key] = (['time', 'height'], np.array(ddas))
    merged = xr.Dataset(
        data_vars=datavars,
        coords={'time': times, 'height': heights},
        attrs={
            'time_count': len(times),
            'height_count': maxlendatas,
            'time_reference': 'UTC',
            'height_unit': 'meter',
        }
    )
    return merged


def readStatuXMLfile(fp:str):
    try:
        with open(fp, 'r', encoding='utf8') as f:
            xml_data = f.read()
        xmld = ET.fromstring(xml_data)
        return parse_element(xmld)
    except Exception as ex:
        print(ex)
        return None


def readSingleStatuXMLfile(fp:str):
    try:
        with open(fp, 'r', encoding='utf8') as f:
            xml_data = f.read()
        xmld = ET.fromstring(xml_data)
        return parse_element(xmld)
    except Exception as ex:
        print(ex)
        return None


def readSingleCalibrationXMLfile(fp:str):
    try:
        with open(fp, 'r', encoding='utf8') as f:
            xml_data = f.read()
        xmld = ET.fromstring(xml_data)
        return parse_element(xmld)
    except Exception as ex:
        print(ex)
        return None


def readSingleProductFile(fp: str):
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f]

        header_line = None
        data_start = None
        for i, line in enumerate(lines):
            if line.startswith('Record,') or line.startswith('DateTime,'):
                header_line = i
                data_start = i + 1
                break

        if header_line is None:
            for i, line in enumerate(lines):
                if ',' in line and any(c.isdigit() for c in line):
                    data_start = i
                    break

        if data_start is None:
            return None

        columns = lines[header_line].split(',') if header_line is not None else None
        data_lines = lines[data_start:]
        data_list = []
        for line in data_lines:
            if line == '' or line == 'NNNN':
                continue
            parts = line.split(',')
            if len(parts) >= 3:
                data_list.append(parts)

        if not data_list:
            return None

        if columns and len(columns) >= len(data_list[0]):
            columns = columns[:len(data_list[0])]
        else:
            columns = [f'col_{i}' for i in range(len(data_list[0]))]

        df = pd.DataFrame(data_list, columns=columns)
        for col in df.columns:
            if col not in ('DateTime', 'DataType'):
                df[col] = pd.to_numeric(df[col], errors='coerce')

        time_col = None
        for col in ['DateTime', 'datetime', 'Time', 'time']:
            if col in df.columns:
                time_col = col
                break

        if time_col:
            try:
                times = pd.to_datetime(df[time_col])
            except:
                times = pd.to_datetime(df[time_col], format='%Y%m%d%H%M%S', errors='coerce')
        else:
            times = pd.date_range(start='2000-01-01', periods=len(df), freq='1min')

        numeric_cols = [col for col in df.columns if col not in (time_col, 'DataType', 'Record')]
        data_vars = {}
        for col in numeric_cols:
            data_vars[col] = (['time'], df[col].values)

        ds = xr.Dataset(
            data_vars=data_vars,
            coords={'time': times},
            attrs={
                'File_Path': fp,
                'columns': numeric_cols,
            }
        )
        return ds
    except Exception as ex:
        print(ex)
        return None


def readProductFiles(fps: list, use_multiprocess=False, multiproces_corenum=-1):
    if use_multiprocess:
        datasets = Parallel(n_jobs=multiproces_corenum)(delayed(readSingleProductFile)(fp) for fp in fps)
    else:
        datasets = [readSingleProductFile(fp) for fp in fps]
    valid = [ds for ds in datasets if ds is not None]
    if not valid:
        return None
    return base.concat_datasets(valid, dim='time')


@xr.register_dataset_accessor("cld")
class CLDDatasetAccessor:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def plot(self, data_name='Z1', figsize=(18,12), cmap=None, norm=None, show=True, savepath=None):
        if data_name not in self._obj.data_vars:
            raise ValueError(f'{data_name} not in dataset')
        if data_name in ('Z1', 'Z2'):
            if cmap is None: cmap = ref_cmap
            if norm is None: norm = ref_norm
        elif data_name in ('V1', 'V2'):
            if cmap is None: cmap = velocity_cmap
            if norm is None: norm = velocity_norm
        elif data_name in ('W1', 'W2'):
            if cmap is None: cmap = spectrumwith_cmap
            if norm is None: norm = spectrumwith_norm
        elif data_name in ('SNR1', 'SNR2'):
            if cmap is None: cmap = snr_cmap
            if norm is None: norm = snr_norm
        else:
            if cmap is None: cmap = ref_cmap
            if norm is None: norm = ref_norm
        fig, ax = plt.subplots(figsize=figsize)
        self._obj[data_name].plot(
            ax=ax, x='time', cmap=cmap, norm=norm,
            cbar_kwargs=dict(
                orientation='horizontal', extend='max',
                extendrect=True, extendfrac='auto', pad=0.08, aspect=35
            )
        )
        ax.set_ylabel("Height (m)")
        ax.set_xlabel("Time (UTC)")
        if show:
            plt.show()
        else:
            plt.close(fig)
        if savepath is not None:
            fig.savefig(savepath, bbox_inches='tight')
