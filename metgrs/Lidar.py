import numpy as np
import pandas as pd
import xarray as xr
import os
import os.path
import glob
import math
import re
from datetime import datetime, timedelta
import dateutil.parser
import struct
from joblib import Parallel, delayed
from . import base


def _decode_zero_terminated_ascii(buf: bytes) -> str:
    return buf.split(b'\x00', 1)[0].decode('ascii', errors='ignore').strip()


def _parse_cdwl_observe_time_from_filename(fp: str):
    m = re.search(r'_(\d{14})_[BP]_', os.path.basename(fp))
    if m is None:
        return None
    return datetime.strptime(m.group(1), '%Y%m%d%H%M%S')


def _parse_cdwl_product_text_block(ds: bytes):
    m = re.search(rb'\r\n(\d{3})\r\n', ds)
    if m is None:
        raise ValueError('无法在文件中找到产品号与数据体起始标记（\\r\\nNNN\\r\\n）。')
    product_number = int(m.group(1).decode('ascii'))
    rows = []
    for line_b in ds[m.end():].splitlines():
        line = line_b.decode('ascii', errors='ignore').strip()
        if line == '':
            continue
        if line == 'NNNN':
            break
        parts = line.split()
        if len(parts) < 4:
            continue
        if re.fullmatch(r'\d{5}', parts[0]) is None:
            continue

        def _to_float(v: str):
            if '/' in v:
                return np.nan
            return float(v)

        rows.append({
            'Height': float(parts[0]),
            'WindDirection': _to_float(parts[1]),
            'HorizontalWindSpeed': _to_float(parts[2]),
            'VerticalWindSpeed': _to_float(parts[3]),
        })
    data = pd.DataFrame(rows, columns=['Height', 'WindDirection', 'HorizontalWindSpeed', 'VerticalWindSpeed'])
    return product_number, m.start(), data


def readSingleCDWLBinFile(binfile: str):
    with open(binfile, 'rb') as f:
        ds = f.read()
    if ds[:4] != b'CDWL':
        raise ValueError(f'文件头标识不是 CDWL: {binfile}')

    lat = struct.unpack('<f', ds[72:76])[0]
    lon = struct.unpack('<f', ds[76:80])[0]
    station_height = struct.unpack('<f', ds[80:84])[0]
    observe_time = _parse_cdwl_observe_time_from_filename(binfile)

    product_number, text_offset, data = _parse_cdwl_product_text_block(ds)

    xr_ds = xr.Dataset(
        data_vars={
            'WindDirection': ('height', data['WindDirection'].values),
            'HorizontalWindSpeed': ('height', data['HorizontalWindSpeed'].values),
            'VerticalWindSpeed': ('height', data['VerticalWindSpeed'].values),
        },
        coords={'height': data['Height'].values},
        attrs={
            'File_Path': binfile,
            'File_Size': len(ds),
            'Magic': 'CDWL',
            'Version_Raw': ds[4:8].hex(),
            'Station_Code': _decode_zero_terminated_ascii(ds[32:40]),
            'Station_Name': _decode_zero_terminated_ascii(ds[48:80]),
            'Latitude_deg': lat,
            'Longitude_deg': lon,
            'Station_Height_m': station_height,
            'Observe_Time': observe_time,
            'Product_Number': product_number,
            'Text_Block_Offset': text_offset,
            'height_unit': 'meter',
        }
    )
    return xr_ds


def readCDWLBinFiles(fps: list, use_multiprocess=False, multiproces_corenum=-1):
    if use_multiprocess:
        datasets = Parallel(n_jobs=multiproces_corenum)(delayed(readSingleCDWLBinFile)(fp) for fp in fps)
    else:
        datasets = [readSingleCDWLBinFile(fp) for fp in fps]
    valid = [ds for ds in datasets if ds is not None]
    if not valid:
        return None
    return base.concat_datasets(valid, dim='time')


def readSingleL0File(l0file: str):
    dts = dateutil.parser.parse(l0file[-34:-20])
    with open(l0file, 'rb') as f:
        ds = f.read()
    pa = 0
    channel_count = struct.unpack('H', ds[52:54])[0]
    if channel_count != 8:
        pa = 6
        channel_count = 8
    channel_metas = []
    for i in range(channel_count):
        channel_metas.append(struct.unpack('HHHHHHHH', ds[54 + 16 * i + pa:70 + 16 * i + pa]))
    params = pd.DataFrame(channel_metas, columns=['ID', 'WaveLength', 'type', 'Ratio', 'BHeight', 'PTR', 'CMethod', 'Count'])
    params['Ratio'] = params['Ratio'] / 100
    params['BHeight'] = params['BHeight'] / 10

    data_dict = {}
    for i in range(channel_count):
        data_dict[f'c{i+1}'] = struct.unpack('f' * channel_metas[i][7], ds[channel_metas[i][5]:channel_metas[i][5] + 4 * channel_metas[i][7]])

    max_count = max(ch[7] for ch in channel_metas)
    data_arrays = []
    for i in range(channel_count):
        arr = np.full(max_count, np.nan)
        raw = np.array(data_dict[f'c{i+1}'])
        arr[:len(raw)] = raw
        data_arrays.append(arr)

    data_vars = {}
    for i in range(channel_count):
        data_vars[f'c{i+1}'] = (['time', 'range_bin'], data_arrays[i][np.newaxis, :])

    xr_ds = xr.Dataset(
        data_vars=data_vars,
        coords={
            'time': [dts],
            'range_bin': range(max_count)
        },
        attrs={
            'Observe_Time': dts,
            'Channel_Count': channel_count,
            'Channel_Metas': params.to_dict(orient='list'),
            'height_unit': 'meter',
        }
    )
    return xr_ds


def readL0Files(fps: list, use_multiprocess=False, multiproces_corenum=-1):
    if use_multiprocess:
        datasets = Parallel(n_jobs=multiproces_corenum)(delayed(readSingleL0File)(fp) for fp in fps)
    else:
        datasets = [readSingleL0File(fp) for fp in fps]
    valid = [ds for ds in datasets if ds is not None]
    if not valid:
        return None
    return base.concat_datasets(valid, dim='time')


def L0DataFileToManufactoryDat(l0file, outPath=None):
    l0da = readSingleL0File(l0file)
    dts = l0da.attrs['Observe_Time']
    params = pd.DataFrame(l0da.attrs['Channel_Metas'])
    dt = dts - timedelta(hours=8)
    if outPath is None:
        outPath = './'
    outf = outPath + dts.strftime('%Y/%Y%m%d/') + 'S001-SLB001-Standard-' + str(int((dts - datetime(2023, 1, 1, 0)).total_seconds() * 2 / 3600 + 4275)) \
        + '-' + dt.strftime('%y%m%d-%H%M%S') + '.dat'
    with open(outf, 'w') as outp:
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
E355P\tE355S\tR386\tR407\tE532P\tE532S\tR607\tE1064\t
''')
        outp.writelines('\t'.join(['%4d' % x for x in list(params['Count'].values)]))
        outp.writelines('''
100\t100\t100\t100\t100\t100\t100\t100\t
55000\t55000\t55000\t55000\t55000\t55000\t55000\t55000\t
DIG\tDIG\tDIG\tDIG\tDIG\tDIG\tDIG\tDIG\t
1000\t1000\t1000\t1000\t1000\t1000\t1000\t1000\t
-------------------------------------------
''')
        outp.writelines('\n'.join(['\t'.join(['%d' % d for d in row]) for row in l0da['c1'].values]))
        outp.writelines('\n')


def readSingleL1ProductFile(binfile: str):
    try:
        with open(binfile, 'rb') as f:
            ds = f.read()

        product_type = 'unknown'
        if 'REXT' in binfile.upper():
            product_type = 'extinction_coefficient'
        elif 'RBAKSCAT' in binfile.upper():
            product_type = 'backscatter_coefficient'
        elif 'DEP' in binfile.upper():
            product_type = 'depolarization_ratio'

        header_size = 64
        if len(ds) < header_size:
            return None

        height_resolution = struct.unpack('<f', ds[16:20])[0] if len(ds) >= 20 else 30.0
        n_bins = struct.unpack('<I', ds[20:24])[0] if len(ds) >= 24 else 0
        wavelength = struct.unpack('<f', ds[24:28])[0] if len(ds) >= 28 else 0.0

        if n_bins == 0:
            n_bins = (len(ds) - header_size) // 4

        data = np.frombuffer(ds[header_size:header_size + n_bins * 4], dtype='<f4')
        heights = np.arange(n_bins) * height_resolution

        xr_ds = xr.Dataset(
            data_vars={
                product_type: ('height', data),
            },
            coords={'height': heights},
            attrs={
                'File_Path': binfile,
                'Product_Type': product_type,
                'Wavelength': wavelength,
                'Height_Resolution': height_resolution,
                'height_unit': 'meter',
            }
        )
        return xr_ds
    except Exception as ex:
        print(ex)
        return None


def readSingleL2ProductFile(txtfile: str):
    try:
        with open(txtfile, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f]

        data_list = []
        for line in lines:
            if line == '' or line.startswith('#'):
                continue
            parts = line.split(',')
            if len(parts) >= 7:
                try:
                    data_list.append({
                        'DateTime': parts[0],
                        'DataType': parts[1],
                        'Surface_Temperature': float(parts[2]) if parts[2] != '' else np.nan,
                        'Surface_Humidity': float(parts[3]) if parts[3] != '' else np.nan,
                        'Surface_Pressure': float(parts[4]) if parts[4] != '' else np.nan,
                        'TIR': float(parts[5]) if parts[5] != '' else np.nan,
                        'Rain': float(parts[6]) if parts[6] != '' else np.nan,
                    })
                except:
                    continue

        if not data_list:
            return None

        df = pd.DataFrame(data_list)
        times = pd.to_datetime(df['DateTime'], errors='coerce')

        data_vars = {
            'Surface_Temperature': ('time', df['Surface_Temperature'].values),
            'Surface_Humidity': ('time', df['Surface_Humidity'].values),
            'Surface_Pressure': ('time', df['Surface_Pressure'].values),
            'TIR': ('time', df['TIR'].values),
            'Rain': ('time', df['Rain'].values),
        }

        cloud_cols = [col for col in df.columns if col.startswith('Cloud')]
        for col in cloud_cols:
            data_vars[col] = ('time', df[col].values)

        pm_cols = [col for col in df.columns if col.startswith('PM')]
        for col in pm_cols:
            data_vars[col] = ('time', df[col].values)

        visibility_cols = [col for col in df.columns if 'Visibility' in col or 'VIS' in col]
        for col in visibility_cols:
            data_vars[col] = ('time', df[col].values)

        height_cols = [col for col in df.columns if col.startswith('H') and col[1:].isdigit()]
        if height_cols:
            heights = [float(col[1:]) for col in height_cols]
            for col in height_cols:
                data_vars[col] = ('time', df[col].values)

        xr_ds = xr.Dataset(
            data_vars=data_vars,
            coords={'time': times},
            attrs={
                'File_Path': txtfile,
                'columns': list(df.columns),
                'data_type': 'L2_product',
            }
        )
        return xr_ds
    except Exception as ex:
        print(ex)
        return None


def readL1ProductFiles(fps: list, use_multiprocess=False, multiproces_corenum=-1):
    if use_multiprocess:
        datasets = Parallel(n_jobs=multiproces_corenum)(delayed(readSingleL1ProductFile)(fp) for fp in fps)
    else:
        datasets = [readSingleL1ProductFile(fp) for fp in fps]
    valid = [ds for ds in datasets if ds is not None]
    if not valid:
        return None
    return base.concat_datasets(valid, dim='time')


def readL2ProductFiles(fps: list, use_multiprocess=False, multiproces_corenum=-1):
    if use_multiprocess:
        datasets = Parallel(n_jobs=multiproces_corenum)(delayed(readSingleL2ProductFile)(fp) for fp in fps)
    else:
        datasets = [readSingleL2ProductFile(fp) for fp in fps]
    valid = [ds for ds in datasets if ds is not None]
    if not valid:
        return None
    return base.concat_datasets(valid, dim='time')


def readSingleStatusXMLFile(fp: str):
    try:
        import xml.etree.ElementTree as ET
        with open(fp, 'r', encoding='utf8') as f:
            xml_data = f.read()
        xmld = ET.fromstring(xml_data)
        return Utils.parse_element(xmld)
    except Exception as ex:
        print(ex)
        return None


def readSingleCalibrationXMLFile(fp: str):
    try:
        import xml.etree.ElementTree as ET
        with open(fp, 'r', encoding='utf8') as f:
            xml_data = f.read()
        xmld = ET.fromstring(xml_data)
        return Utils.parse_element(xmld)
    except Exception as ex:
        print(ex)
        return None


@xr.register_dataset_accessor("lidar")
class LidarDatasetAccessor:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    @property
    def channel_metas(self):
        return pd.DataFrame(self._obj.attrs.get('Channel_Metas', {}))
