import os
import json
from datetime import datetime, timedelta
import dateutil.parser
import dateutil.rrule
import numpy as np
import pandas as pd
from . import Utils
import io
import math
import types
import functools
import matplotlib as mpl
import matplotlib.pyplot as plt


def readMWRFile(filename):
    ds = pd.read_csv(filename, encoding='gbk', skiprows=2)
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
