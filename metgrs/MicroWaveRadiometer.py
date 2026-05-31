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
import types
import functools
import matplotlib as mpl
import matplotlib.pyplot as plt


def readMWRFile(filename, encoding='gbk'):
    ds = pd.read_csv(filename, encoding=encoding, skiprows=2)
    ds['DateTime'] = pd.to_datetime(ds['DateTime'])
    ds['10'] = ds['10'].astype(str).replace(
        '11',
        'TEM').replace(
        '12',
        'WVDen').replace(
        '13',
        'RHU').replace(
        '14',
        'WDen')
    ds = ds.rename(columns={'10': 'dtype'})
    return ds


def readMWRFileAsDataset(filename, encoding='gbk'):
    try:
        df = readMWRFile(filename, encoding=encoding)
        times = df['DateTime'].values

        dtype_col = 'dtype'
        if dtype_col not in df.columns:
            dtype_col = df.columns[1] if len(df.columns) > 1 else None

        numeric_cols = [col for col in df.columns if col not in ('DateTime', dtype_col)]

        data_vars = {}
        for col in numeric_cols:
            data_vars[col] = (['time'], df[col].values)

        if dtype_col and dtype_col in df.columns:
            data_vars['dtype'] = (['time'], df[dtype_col].values)

        ds = xr.Dataset(
            data_vars=data_vars,
            coords={'time': times},
            attrs={
                'File_Path': filename,
                'columns': numeric_cols,
            }
        )
        return ds
    except Exception as ex:
        print(ex)
        return None


def readMWRFilesAsDataset(fps: list, use_multiprocess=False, multiproces_corenum=-1):
    if use_multiprocess:
        from joblib import Parallel, delayed
        datasets = Parallel(n_jobs=multiproces_corenum)(delayed(readMWRFileAsDataset)(fp) for fp in fps)
    else:
        datasets = [readMWRFileAsDataset(fp) for fp in fps]
    valid = [ds for ds in datasets if ds is not None]
    if not valid:
        return None
    return xr.concat(valid, dim='time')
