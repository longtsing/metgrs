import os
import json
from datetime import datetime, timedelta
import dateutil.parser
import dateutil.rrule
import numpy as np
import pandas as pd
import xarray as xr
from . import Utils
import io
import math
import matplotlib as mpl
from joblib import Parallel, delayed
import xml.etree.ElementTree as ET
from . import base, Utils

parse_element = Utils.parse_element

#region 绘图参数
velocity_colors = [
    '#951262', '#ED2226', '#EB3E22', '#EF6A26', '#F58324',
    '#F3A122', '#FDB52A', '#FDD31E', '#F9EF1A', '#F7FD1C',
    '#D9E9F1', '#C7D7F1', '#B1C7EB', '#99B5E7', '#83A5DD',
    '#6E93D3', '#6089CB', '#4C7CC3', '#4870BB', '#406AB9',
    '#2A42AB', '#242681', '#242074', '#22206A', '#1C622C',
    '#067E42', '#0C8B42', '#30BD4C', '#4EC14A', '#58C546', '#87742E'
]
velocity_levels = [-1, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.1, 0,
                   0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
                   2, 2.5, 3, 4, 5, 6, 7, 8, 9, 10]
velocity_cmap = mpl.colors.ListedColormap(velocity_colors).with_extremes(
    over=velocity_colors[-1], under=velocity_colors[0])
velocity_norm = mpl.colors.BoundaryNorm(velocity_levels, velocity_cmap.N)
#endregion

#region 风廓线雷达数据文件元数据
line0_variables = {
    'WNDRAD': '风廓线雷达数据文件标识',
    'File_version': '文件版本号'
}
line1_variables = {
    'Station_Id': '站号',
    'Longitude': '经度',
    'Latitude': '纬度',
    'Altitude': '海拔高度',
    'Machine_Type': '风廓线仪型号',
}
line2_variables = {
    'Antenna_Gain': '天线增益',
    'Feeder_Loss': '馈线损耗',
    'East_Beam_Angle': '东波束与铅垂线的夹角',
    'West_Beam_Angle': '西波束与铅垂线的夹角',
    'South_Beam_Angle': '南波束与铅垂线的夹角',
    'North_Beam_Angle': '北波束与铅垂线的夹角',
    'Center_Row_Beam_Angle': '中（行）波束与铅垂线的夹角（度）',
    'Center_Column_Beam_Angle': '中（列）波束与铅垂线的夹角（度）',
    'Number_Of_Beams': '波束数',
    'Sampling_Frequency': '采样频率',
    'Transmit_Wavelength': '发射波长',
    'Pulse_Repetition_Frequency': '脉冲重复频率',
    'Pulse_Width': '脉冲宽度',
    'Horizontal_Beam_Width': '水平波束宽度',
    'Vertical_Beam_Width': '垂直波束宽度',
    'Peak_Transmit_Power': '发射峰值功率',
    'Average_Transmit_Power': '发射平均功率',
    'Start_Sampling_Height': '起始采样高度',
    'End_Sampling_Height': '终止采样高度'
}
line3_variables = {
    'Time_Source': '时间来源',
    'Observation_Start_Time': '观测开始时间',
    'Observation_End_Time': '观测结束时间',
    'Calibration_Status': '标校状态',
    'Incoherent_Accumulation': '非相干积累',
    'Coherent_Accumulation': '相干积累',
    'FFT_Points': 'Fft点数',
    'Spectral_Averages': '谱平均数',
    'Beam_Order_Flag': '波束顺序标志',
    'East_Beam_Azimuth_Correction': '东波束方位角修正值',
    'West_Beam_Azimuth_Correction': '西波束方位角修正值',
    'South_Beam_Azimuth_Correction': '南波束方位角修正值',
    'North_Beam_Azimuth_Correction': '北波束方位角修正值'
}
L2data_variables = {
    'Sampling_Height': '采样高度',
    'Velocity_Spectrum_Width': '速度谱宽',
    'Signal_To_Noise_Ratio': '信噪比',
    'Radial_Velocity': '径向速度'
}
L3meta_variables = {
    "Station_Id": "区站号",
    "Longitude": "经度",
    "Latitude": "纬度",
    "Altitude": "观测场拔海高度",
    "Machine_Type": "风廓线仪型号",
    "Observation_Time": "观测时间"
}
L3data_variables = {
    "Sampling_Height": "采样高度",
    "Wind_Direction": "水平风向",
    "Wind_Speed": "水平风速",
    "Vertical_Wind_Speed": "垂直风速",
    "Horizontal_Confidence": "水平方向可信度",
    "Vertical_Confidence": "垂直方向可信度",
    "Cn2": "Cn2"
}
L1Struct_FileTag = np.dtype([
    ('FileID', 'S8'),
    ('VersionNo', 'f4'),
    ('FileHeaderLength', 'i4')
])
L1Struct_SiteInfo = np.dtype([
    ('Country', 'S16'),
    ('Province', 'S16'),
    ('StationNumber', 'S16'),
    ('Station', 'S16'),
    ('RadarType', 'S16'),
    ('Longitude', 'S16'),
    ('Latitude', 'S16'),
    ('Altitude', 'S16'),
    ('Temp', 'S40')
])
L1Struct_PerformanceInfo = np.dtype([
    ('Ae', 'i4'),
    ('AgcWast', 'f4'),
    ('AngleE', 'f4'),
    ('AngleW', 'f4'),
    ('AngleS', 'f4'),
    ('AngleN', 'f4'),
    ('AngleR', 'f4'),
    ('AngleL', 'f4'),
    ('ScanBeamN', 'u4'),
    ('SampleP', 'u4'),
    ('WaveLength', 'u4'),
    ('Prp', 'f4'),
    ('PusleW', 'f4'),
    ('HBeamW', 'u2'),
    ('VBeamW', 'u2'),
    ('TranPp', 'f4'),
    ('TranAp', 'f4'),
    ('StartSamplBin', 'u4'),
    ('EndSamplBin', 'u4'),
    ('BinLength', 'i2'),
    ('BinNum', 'i2'),
    ('Temp', 'S40')
])
L1Struct_ObservationInfo = np.dtype([
    ('SYear', 'u2'),
    ('SMonth', 'u1'),
    ('SDay', 'u1'),
    ('SHour', 'u1'),
    ('SMinute', 'u1'),
    ('SSecond', 'u1'),
    ('TimeP', 'u1'),
    ('SMillisecond', 'u4'),
    ('Calibration', 'u2'),
    ('BeamfxChange', 'i2'),
    ('EYear', 'u2'),
    ('EMonth', 'u1'),
    ('EDay', 'u1'),
    ('EHour', 'u1'),
    ('EMinute', 'u1'),
    ('ESecond', 'u1'),
    ('NNtr', 'i1'),
    ('Ntr', 'i2'),
    ('SpAver', 'u2'),
    ('Fft', 'u2'),
    ('unknow', 'u2'),
    ('BeamDir', 'S12'),
    ('AzimuthE', 'f4'),
    ('AzimuthW', 'f4'),
    ('AzimuthS', 'f4'),
    ('AzimuthN', 'f4'),
    ('Temp', 'S40')
])
#endregion


def _decode_bytes(val, encoding='gbk'):
    if isinstance(val, bytes):
        return val.split(b'\x00')[0].decode(encoding, errors='ignore')
    return val


def _dict_from_struct(data, dtype, encoding='gbk'):
    result = {}
    for name in dtype.names:
        val = data[name][0]
        result[name] = _decode_bytes(val, encoding)
    return result


def readSingleL1file(fp: str):
    try:
        with open(fp, 'rb') as f:
            bs = f.read()
        bsoffset = 0

        data = np.frombuffer(bs[bsoffset:bsoffset + L1Struct_FileTag.itemsize], L1Struct_FileTag)
        bsoffset += L1Struct_FileTag.itemsize
        file_tag = _dict_from_struct(data, L1Struct_FileTag)

        data = np.frombuffer(bs[bsoffset:bsoffset + L1Struct_SiteInfo.itemsize], L1Struct_SiteInfo)
        bsoffset += L1Struct_SiteInfo.itemsize
        site_info = _dict_from_struct(data, L1Struct_SiteInfo)

        obs_list = []
        perf_infos = []
        obs_infos = []
        speeds = []

        while bsoffset < len(bs):
            data = np.frombuffer(bs[bsoffset:bsoffset + L1Struct_PerformanceInfo.itemsize], L1Struct_PerformanceInfo)
            bsoffset += L1Struct_PerformanceInfo.itemsize
            perf_info = _dict_from_struct(data, L1Struct_PerformanceInfo)

            data = np.frombuffer(bs[bsoffset:bsoffset + L1Struct_ObservationInfo.itemsize], L1Struct_ObservationInfo)
            bsoffset += L1Struct_ObservationInfo.itemsize
            obs_info = _dict_from_struct(data, L1Struct_ObservationInfo)

            speed_per_fft = perf_info['Prp'] / 2 / obs_info['Fft'] * perf_info['WaveLength'] * 1e-5

            data_len = obs_info['Fft'] * perf_info['BinNum'] * perf_info['ScanBeamN']
            fft_data = np.frombuffer(
                bs[bsoffset:bsoffset + 4 * data_len], 'f4', count=data_len
            ).reshape(perf_info['ScanBeamN'], perf_info['BinNum'], obs_info['Fft'])
            bsoffset += 4 * data_len

            obs_list.append(fft_data)
            perf_infos.append(perf_info)
            obs_infos.append(obs_info)
            speeds.append(speed_per_fft)

        beam_dir = obs_infos[0]['BeamDir']
        heights = np.arange(perf_infos[0]['BinNum']) * perf_infos[0]['BinLength'] + perf_infos[0]['StartSamplBin']
        times = [
            datetime(oi['SYear'], oi['SMonth'], oi['SDay'], oi['SHour'], oi['SMinute'], oi['SSecond'])
            for oi in obs_infos
        ]

        ds = xr.Dataset(
            data_vars={
                'FFT_data': (['time', 'Beam', 'height', 'Fft'], np.array(obs_list))
            },
            coords={
                'time': times,
                'Beam': list(beam_dir),
                'height': heights,
                'Fft': np.arange(obs_infos[0]['Fft'])
            },
            attrs={
                'FileTag': file_tag,
                'SiteInfo': site_info,
                'PerformanceInfo': perf_infos,
                'ObservationInfo': obs_infos,
                'Speed_per_FFT_point': speeds,
                'WaveLength_unit': '1e-5 meter',
                'Prp_unit': 'Hz',
                'Speed_per_FFT_point_unit': 'm/s',
                'height_unit': 'meter',
            }
        )
        return ds
    except Exception as ex:
        print(ex)
        return None


def _estimate_noise_floor(spectrum, n_noise_bins=10):
    sorted_spec = np.sort(spectrum)
    noise = np.mean(sorted_spec[:n_noise_bins])
    return noise


def _clutter_filter(spectrum, velocity_axis, clutter_width=0.5):
    clutter_mask = np.abs(velocity_axis) < clutter_width
    filtered = spectrum.copy()
    filtered[clutter_mask] = 0
    return filtered


def _spectral_moments(spectrum, velocity_axis):
    total_power = np.sum(spectrum)
    if total_power <= 0:
        return np.nan, np.nan, np.nan
    
    mean_velocity = np.sum(velocity_axis * spectrum) / total_power
    
    velocity_deviation = velocity_axis - mean_velocity
    spectral_width = np.sqrt(np.sum(velocity_deviation**2 * spectrum) / total_power)
    
    return total_power, mean_velocity, spectral_width


def CalcL1toL2(ds_l1, clutter_filter=True, clutter_width=0.5, snr_threshold=-20, n_noise_bins=10):
    if ds_l1 is None:
        return None
    
    fft_data = ds_l1['FFT_data'].values
    beam_dirs = ds_l1.coords['Beam'].values
    heights = ds_l1.coords['height'].values
    times = ds_l1.coords['time'].values
    
    speed_per_fft = ds_l1.attrs['Speed_per_FFT_point'][0]
    n_fft = fft_data.shape[3]
    velocity_axis = (np.arange(n_fft) - n_fft/2) * speed_per_fft
    
    results = {}
    for beam_idx, beam_name in enumerate(beam_dirs):
        beam_results = {
            'Radial_Velocity': [],
            'Velocity_Spectrum_Width': [],
            'Signal_To_Noise_Ratio': [],
            'Sampling_Height': []
        }
        
        for time_idx in range(len(times)):
            rv_list = []
            sw_list = []
            snr_list = []
            
            for height_idx in range(len(heights)):
                spectrum = fft_data[time_idx, beam_idx, height_idx, :]
                
                noise_floor = _estimate_noise_floor(spectrum, n_noise_bins)
                
                signal_spectrum = spectrum - noise_floor
                signal_spectrum = np.maximum(signal_spectrum, 0)
                
                if clutter_filter:
                    signal_spectrum = _clutter_filter(signal_spectrum, velocity_axis, clutter_width)
                
                total_power, mean_vel, spec_width = _spectral_moments(signal_spectrum, velocity_axis)
                
                if noise_floor > 0:
                    snr = 10 * np.log10(total_power / noise_floor) if total_power > 0 else -999
                else:
                    snr = -999
                
                rv_list.append(mean_vel)
                sw_list.append(spec_width)
                snr_list.append(snr)
            
            beam_results['Radial_Velocity'].append(rv_list)
            beam_results['Velocity_Spectrum_Width'].append(sw_list)
            beam_results['Signal_To_Noise_Ratio'].append(snr_list)
        
        beam_results['Radial_Velocity'] = np.array(beam_results['Radial_Velocity'])
        beam_results['Velocity_Spectrum_Width'] = np.array(beam_results['Velocity_Spectrum_Width'])
        beam_results['Signal_To_Noise_Ratio'] = np.array(beam_results['Signal_To_Noise_Ratio'])
        beam_results['Sampling_Height'] = heights
        
        results[beam_name] = beam_results
    
    data_vars = {}
    for beam_name in beam_dirs:
        beam_data = results[beam_name]
        prefix = beam_name
        data_vars[f'{prefix}_Radial_Velocity'] = (['time', 'height'], beam_data['Radial_Velocity'])
        data_vars[f'{prefix}_Velocity_Spectrum_Width'] = (['time', 'height'], beam_data['Velocity_Spectrum_Width'])
        data_vars[f'{prefix}_Signal_To_Noise_Ratio'] = (['time', 'height'], beam_data['Signal_To_Noise_Ratio'])
    
    data_vars['Sampling_Height'] = (['height'], heights)
    
    ds_l2 = xr.Dataset(
        data_vars=data_vars,
        coords={
            'time': times,
            'height': heights
        },
        attrs={
            'FileTag': ds_l1.attrs.get('FileTag'),
            'SiteInfo': ds_l1.attrs.get('SiteInfo'),
            'Beam_Order_Flags': list(beam_dirs),
            'Beam_Count': len(beam_dirs),
            'levels_count': 1,
            'level_metas': [{
                'Beam_Order_Flags': list(beam_dirs),
                'Beam_Count': len(beam_dirs),
                'Observation_Start_Time': pd.Timestamp(times[0]).to_pydatetime() if len(times) > 0 else None,
                'Observation_End_Time': pd.Timestamp(times[-1]).to_pydatetime() if len(times) > 0 else None,
            }],
            'processing_params': {
                'clutter_filter': clutter_filter,
                'clutter_width': clutter_width,
                'snr_threshold': snr_threshold,
                'n_noise_bins': n_noise_bins
            },
            'data_type': 'L2_radial'
        }
    )
    
    return ds_l2


def CalcL2toL3(ds_l2, qcw=3, interp=False, rollmean=True, rollmeancout=5):
    level_metas = ds_l2.attrs['level_metas']
    calc_data = []

    for j, level_name in enumerate(ds_l2.coords['level'].values):
        level_meta = level_metas[j]
        sh = ds_l2['Sampling_Height'].sel(level=level_name).values
        valid = ~np.isnan(sh)
        h = sh[valid]

        def _get(col):
            return ds_l2[col].sel(level=level_name).values[valid]

        Vre = _get('E_Radial_Velocity')
        Wre = 1 / np.exp(_get('E_Velocity_Spectrum_Width'))
        Vrn = _get('N_Radial_Velocity')
        Wrn = 1 / np.exp(_get('N_Velocity_Spectrum_Width'))
        Vw = _get('R_Radial_Velocity')
        Ww = 1 / np.exp(_get('R_Velocity_Spectrum_Width'))
        Vrw = _get('W_Radial_Velocity')
        Wrw = 1 / np.exp(_get('W_Velocity_Spectrum_Width'))
        Vrs = _get('S_Radial_Velocity')
        Wrs = 1 / np.exp(_get('S_Velocity_Spectrum_Width'))

        Ws = np.array([Wre, Wrw, Wrs, Wrn, Ww])

        qc_ew = np.abs(Vre + Vrw) > qcw
        Vre = np.where(qc_ew, np.nan, Vre)
        Vrw = np.where(qc_ew, np.nan, Vrw)
        qc_ns = np.abs(Vrn + Vrs) > qcw
        Vrn = np.where(qc_ns, np.nan, Vrn)
        Vrs = np.where(qc_ns, np.nan, Vrs)

        Vsw = np.array([
            np.where(np.isnan(Vrw), np.nan, Vre),
            np.where(np.isnan(Vre), np.nan, Vrw),
            np.where(np.isnan(Vrn), np.nan, Vrs),
            np.where(np.isnan(Vrs), np.nan, Vrn),
            Vw
        ])
        w = np.nansum(Vsw * Ws, axis=0) / np.nansum(Ws, axis=0)

        a_e = level_meta['East_Beam_Angle'] + level_meta['East_Beam_Azimuth_Correction']
        po_e = math.radians(90 - a_e)
        u_e = (w * math.sin(po_e) - Vre) / math.cos(po_e)
        a_w = level_meta['West_Beam_Angle'] + level_meta['West_Beam_Azimuth_Correction']
        po_w = math.radians(90 - a_w)
        u_w = (Vrw - w * math.sin(po_w)) / math.cos(po_w)
        u = np.nansum(np.array([u_e, u_w]) * Ws[:2], axis=0) / np.nansum(Ws[:2], axis=0)

        a_s = level_meta['South_Beam_Angle'] + level_meta['South_Beam_Azimuth_Correction']
        po_s = math.radians(90 - a_s)
        v_s = (Vrs - w * math.sin(po_s)) / math.cos(po_s)
        a_n = level_meta['North_Beam_Angle'] + level_meta['North_Beam_Azimuth_Correction']
        po_n = math.radians(90 - a_n)
        v_n = (w * math.sin(po_n) - Vrn) / math.cos(po_n)
        v = np.nansum(np.array([v_s, v_n]) * Ws[2:4], axis=0) / np.nansum(Ws[2:4], axis=0)

        calc_data.append(pd.DataFrame({
            'Sampling_Height': h,
            'Vertical_Wind_Speed': w,
            'U_Wind_Speed': u,
            'V_Wind_Speed': v,
        }))

    Calc_L3Data = pd.concat(calc_data).reset_index(drop=True).groupby('Sampling_Height').mean().reset_index()
    if interp:
        Calc_L3Data = Calc_L3Data.set_index('Sampling_Height').interpolate(method='linear').reset_index()
    if rollmean:
        Calc_L3Data = Calc_L3Data.set_index('Sampling_Height').sort_index().rolling(window=rollmeancout, min_periods=1).mean().reset_index()

    wdir, wspd = Utils.vuv2w(Calc_L3Data['U_Wind_Speed'].values, Calc_L3Data['V_Wind_Speed'].values)
    Calc_L3Data['Wind_Direction'] = wdir
    Calc_L3Data['Wind_Speed'] = wspd
    Calc_L3Data.dropna(inplace=True)

    obs_time = ds_l2.attrs['level_metas'][0].get('Observation_End_Time')

    ds_l3 = xr.Dataset(
        data_vars={
            'Wind_Direction': ('height', Calc_L3Data['Wind_Direction'].values),
            'Wind_Speed': ('height', Calc_L3Data['Wind_Speed'].values),
            'Vertical_Wind_Speed': ('height', Calc_L3Data['Vertical_Wind_Speed'].values),
            'U_Wind_Speed': ('height', Calc_L3Data['U_Wind_Speed'].values),
            'V_Wind_Speed': ('height', Calc_L3Data['V_Wind_Speed'].values),
        },
        coords={'height': Calc_L3Data['Sampling_Height'].values},
        attrs={
            'WNDRAD': ds_l2.attrs.get('WNDRAD'),
            'File_version': ds_l2.attrs.get('File_version'),
            'Station_Id': ds_l2.attrs.get('Station_Id'),
            'Longitude': ds_l2.attrs.get('Longitude'),
            'Latitude': ds_l2.attrs.get('Latitude'),
            'Altitude': ds_l2.attrs.get('Altitude'),
            'Machine_Type': ds_l2.attrs.get('Machine_Type'),
            'Observation_Time': obs_time,
            'height_unit': 'meter',
        }
    )
    return ds_l3


def readSingleL3file(fp: str):
    try:
        with open(fp, 'r') as f:
            lines = [line.strip() for line in f]

        lineds = lines[0].split(' ')
        keys = list(line0_variables.keys())
        attrs = {key: lineds[i] for i, key in enumerate(keys)}

        lineds = lines[1].split(' ')
        keys = list(L3meta_variables.keys())
        for i, key in enumerate(keys):
            if key in ('Station_Id', 'Machine_Type'):
                attrs[key] = lineds[i]
            elif key == 'Observation_Time':
                attrs[key] = dateutil.parser.parse(lineds[i])
            else:
                attrs[key] = float(lineds[i])

        da = pd.read_fwf(
            io.StringIO('\n'.join(lines[3:-1])),
            widths=[5, 6, 6, 7, 4, 4, 9],
            encoding='gbk',
            names=list(L3data_variables.keys()),
            dtype=str
        )
        da = da.apply(lambda x: pd.to_numeric(x, errors='coerce'))
        uvs = Utils.vw2uv(da['Wind_Direction'].values, da['Wind_Speed'].values)
        da['U_Wind_Speed'] = uvs[0]
        da['V_Wind_Speed'] = uvs[1]

        ds = xr.Dataset(
            data_vars={
                'Wind_Direction': ('height', da['Wind_Direction'].values),
                'Wind_Speed': ('height', da['Wind_Speed'].values),
                'Vertical_Wind_Speed': ('height', da['Vertical_Wind_Speed'].values),
                'Horizontal_Confidence': ('height', da['Horizontal_Confidence'].values),
                'Vertical_Confidence': ('height', da['Vertical_Confidence'].values),
                'Cn2': ('height', da['Cn2'].values),
                'U_Wind_Speed': ('height', da['U_Wind_Speed'].values),
                'V_Wind_Speed': ('height', da['V_Wind_Speed'].values),
            },
            coords={'height': da['Sampling_Height'].values},
            attrs=attrs
        )
        return ds
    except Exception as ex:
        print(ex)
        return None


def readL3files(fps: list, use_multiprocess=False, multiproces_corenum=-1):
    if use_multiprocess:
        datasets = Parallel(n_jobs=multiproces_corenum)(delayed(readSingleL3file)(fp) for fp in fps)
    else:
        datasets = [readSingleL3file(fp) for fp in fps]
    valid = [ds.expand_dims('time') for ds in datasets if ds is not None]
    if not valid:
        return None
    return xr.concat(valid, dim='time')


def readSingleProductFile(fp: str, product_type='ROBS'):
    try:
        with open(fp, 'r') as f:
            lines = [line.strip() for line in f]

        header_keys = {
            'ROBS': 'WNDROBS',
            'HOBS': 'WNDHOBS',
            'OOBS': 'WNDOOBS'
        }
        expected_header = header_keys.get(product_type, 'WNDROBS')

        if lines[0] != expected_header:
            pass

        lineds = lines[1].split(' ')
        keys = list(L3meta_variables.keys())
        attrs = {}
        for i, key in enumerate(keys):
            if key in ('Station_Id', 'Machine_Type'):
                attrs[key] = lineds[i] if i < len(lineds) else ''
            elif key == 'Observation_Time':
                attrs[key] = dateutil.parser.parse(lineds[i]) if i < len(lineds) else None
            else:
                attrs[key] = float(lineds[i]) if i < len(lineds) else np.nan

        data_start = None
        data_end = None
        for i, line in enumerate(lines):
            if line == product_type:
                data_start = i + 1
            elif line == 'NNNN' and data_start is not None:
                data_end = i
                break

        if data_start is None or data_end is None:
            return None

        data_lines = lines[data_start:data_end]
        data_list = []
        for line in data_lines:
            parts = line.split()
            if len(parts) >= 7:
                data_list.append({
                    'Sampling_Height': float(parts[0]),
                    'Wind_Direction': float(parts[1]) if '/' not in parts[1] else np.nan,
                    'Wind_Speed': float(parts[2]) if '/' not in parts[2] else np.nan,
                    'Vertical_Wind_Speed': float(parts[3]) if '/' not in parts[3] else np.nan,
                    'Horizontal_Confidence': float(parts[4]) if '/' not in parts[4] else np.nan,
                    'Vertical_Confidence': float(parts[5]) if '/' not in parts[5] else np.nan,
                    'Cn2': float(parts[6]) if '/' not in parts[6] else np.nan,
                })

        if not data_list:
            return None

        da = pd.DataFrame(data_list)
        uvs = Utils.vw2uv(da['Wind_Direction'].values, da['Wind_Speed'].values)
        da['U_Wind_Speed'] = uvs[0]
        da['V_Wind_Speed'] = uvs[1]

        attrs['product_type'] = product_type

        ds = xr.Dataset(
            data_vars={
                'Wind_Direction': ('height', da['Wind_Direction'].values),
                'Wind_Speed': ('height', da['Wind_Speed'].values),
                'Vertical_Wind_Speed': ('height', da['Vertical_Wind_Speed'].values),
                'Horizontal_Confidence': ('height', da['Horizontal_Confidence'].values),
                'Vertical_Confidence': ('height', da['Vertical_Confidence'].values),
                'Cn2': ('height', da['Cn2'].values),
                'U_Wind_Speed': ('height', da['U_Wind_Speed'].values),
                'V_Wind_Speed': ('height', da['V_Wind_Speed'].values),
            },
            coords={'height': da['Sampling_Height'].values},
            attrs=attrs
        )
        return ds
    except Exception as ex:
        print(ex)
        return None


def readSingleROBSfile(fp: str):
    return readSingleProductFile(fp, 'ROBS')


def readSingleHOBSfile(fp: str):
    return readSingleProductFile(fp, 'HOBS')


def readSingleOOBSfile(fp: str):
    return readSingleProductFile(fp, 'OOBS')


def readSingleCalibrationXMLfile(fp: str):
    try:
        with open(fp, 'r', encoding='utf8') as f:
            xml_data = f.read()
        xmld = ET.fromstring(xml_data)
        return parse_element(xmld)
    except Exception as ex:
        print(ex)
        return None


def readSingleStatuXMLfile(fp: str):
    try:
        with open(fp, 'r', encoding='utf8') as f:
            xml_data = f.read()
        xmld = ET.fromstring(xml_data)
        return parse_element(xmld)
    except Exception as ex:
        print(ex)
        return None


@xr.register_dataset_accessor("wpr")
class WPRDatasetAccessor:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def calc_l1_to_l2(self, clutter_filter=True, clutter_width=0.5, snr_threshold=-20, n_noise_bins=10):
        return CalcL1toL2(self._obj, clutter_filter, clutter_width, snr_threshold, n_noise_bins)

    def calc_l2_to_l3(self, qcw=3, interp=False, rollmean=True, rollmeancout=5):
        return CalcL2toL3(self._obj, qcw, interp, rollmean, rollmeancout)

    def plot_l3_wind(self, figsize=(18, 12), cmap=None, norm=None, show=True, savepath=None):
        import matplotlib.pyplot as plt
        if cmap is None:
            cmap = velocity_cmap
        if norm is None:
            norm = velocity_norm
        fig, ax = plt.subplots(figsize=figsize)
        if 'time' in self._obj.dims:
            data_var = self._obj['Wind_Speed'].isel(time=0)
            heights = self._obj.coords['height'].values
            if len(data_var.dims) == 1:
                ax.plot(data_var.values, heights)
                ax.set_xlabel('Wind Speed (m/s)')
                ax.set_ylabel('Height (m)')
            else:
                data_var.plot(ax=ax, cmap=cmap, norm=norm)
        else:
            data_var = self._obj['Wind_Speed']
            heights = self._obj.coords['height'].values
            ax.plot(data_var.values, heights)
            ax.set_xlabel('Wind Speed (m/s)')
            ax.set_ylabel('Height (m)')
        if show:
            plt.show()
        else:
            plt.close(fig)
        if savepath is not None:
            fig.savefig(savepath, bbox_inches='tight')


def readSingleL2file(fp: str):
    try:
        with open(fp, 'r') as f:
            lines = [line.strip() for line in f]

        lineds = lines[0].split(' ')
        keys = list(line0_variables.keys())
        header0 = {key: lineds[i] for i, key in enumerate(keys)}

        lineds = lines[1].split(' ')
        keys = list(line1_variables.keys())
        header1 = {}
        for i, key in enumerate(keys):
            header1[key] = lineds[i] if i == 0 or i == 4 else Utils.dtryfloat(lineds[i])

        tsplitlineis = [1] + [i for i in range(5, len(lines)) if lines[i] == 'NNNN']
        columnnames = list(L2data_variables.keys())

        level_metas = []
        level_dfs = []
        beam_count = 1

        for i in range(len(tsplitlineis) - 1):
            lineStart = tsplitlineis[i]
            lineEnd = tsplitlineis[i + 1]
            if i % beam_count == 0:
                level_meta = {}
                level_dfs_i = []
                beamj = 0
                lineStart += 1
                lineds = lines[lineStart].split(' ')
                keys = list(line2_variables.keys())
                for j, key in enumerate(keys):
                    level_meta[key] = Utils.dtryfloat(lineds[j])

                lineStart += 1
                lineds = lines[lineStart].split(' ')
                keys = list(line3_variables.keys())
                for j, key in enumerate(keys):
                    if key == 'Beam_Order_Flag':
                        level_meta[key] = lineds[j].replace('/', '')
                        level_meta['Beam_Order_Flags'] = list(level_meta[key])
                        level_meta['Beam_Count'] = len(level_meta['Beam_Order_Flags'])
                    elif key in ('Observation_Start_Time', 'Observation_End_Time'):
                        level_meta[key] = dateutil.parser.parse(lineds[j])
                    else:
                        level_meta[key] = Utils.dtryfloat(lineds[j])
                beam_count = level_meta['Beam_Count']

            level_dfs_i.append(lines[lineStart + 2:lineEnd])
            beamj += 1

            if beamj == beam_count:
                dlevelcolumnnames = [
                    f"{bof}_{key}" for bof in level_meta['Beam_Order_Flags'] for key in columnnames
                ]
                sscolumnnames = [dlevelcolumnnames[k] for k in range(0, len(dlevelcolumnnames), len(columnnames))]
                arr = np.array(level_dfs_i).T
                df = pd.read_csv(
                    io.StringIO('\n'.join([' '.join(x) for x in list(arr)])),
                    sep=' ', header=None, names=dlevelcolumnnames
                )
                df = df.rename(columns={sscolumnnames[0]: sscolumnnames[0][2:]}).drop(sscolumnnames[1:], axis=1)
                df = df.apply(lambda x: pd.to_numeric(x, errors='coerce'))
                level_meta_copy = {k: v for k, v in level_meta.items() if k != 'Data'}
                level_metas.append(level_meta_copy)
                level_dfs.append(df)

        beam_order_flags = level_metas[0]['Beam_Order_Flags']
        beam_count_val = level_metas[0]['Beam_Count']
        levels_count = len(level_dfs)
        if levels_count == 1:
            dlevels = ['low']
        elif levels_count == 2:
            dlevels = ['low', 'high']
        else:
            dlevels = ['low', 'middle', 'high']

        data_columns = [c for c in level_dfs[0].columns if c != 'Sampling_Height']
        max_bins = max(len(df) for df in level_dfs)

        sh_arr = np.full((levels_count, max_bins), np.nan)
        for idx, df in enumerate(level_dfs):
            sh_arr[idx, :len(df)] = df['Sampling_Height'].values

        data_vars = {'Sampling_Height': (['level', 'height_bin'], sh_arr)}
        for col in data_columns:
            arr = np.full((levels_count, max_bins), np.nan)
            for idx, df in enumerate(level_dfs):
                if col in df.columns:
                    arr[idx, :len(df)] = df[col].values
            data_vars[col] = (['level', 'height_bin'], arr)

        ds = xr.Dataset(
            data_vars=data_vars,
            coords={
                'level': dlevels,
                'height_bin': range(max_bins)
            },
            attrs={
                **header0,
                **header1,
                'Beam_Order_Flags': beam_order_flags,
                'Beam_Count': beam_count_val,
                'levels_count': levels_count,
                'level_metas': level_metas,
            }
        )
        return ds
    except Exception as ex:
        print(ex)
        return None
