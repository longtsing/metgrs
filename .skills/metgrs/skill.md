# metgrs 使用指南

> 地基遥感垂直观测数据读取与基础处理：风廓线雷达、云雷达、激光雷达、微波辐射计。

## 1. 适用场景

当用户的任务涉及以下任一情况时，调用本 skill：

- 读取中国气象局地基遥感垂直观测系统的二进制/文本文件
  - 风廓线雷达 L1（FFT 功率谱）/ L2（径向）/ L3（产品）
  - 云雷达 FFT / 基础数据
  - 激光雷达 L0（原始）/ L1（消光/后向散射/退偏振比）/ L2（地面气象）/ CDWL 风产品
  - 微波辐射计亮温通道（CH22.235 ~ CH58.800 GHz）
- 把上述数据接入 xarray 生态：绘图、切片、重采样、concat
- 在 TLogP / 廓线 / 风羽图等场景做基础二次计算（露点、气压高度换算、风分量等）

## 2. 安装与导入

```bash
# 推荐：conda
mamba install -c conda-forge numpy pandas xarray matplotlib joblib python-dateutil metpy cartopy
pip install metgrs
```

```python
import metgrs
from metgrs import WindProfileRadar, CloudRadar, Lidar, MicroWaveRadiometer, Utils
```

所有数据读取函数的返回值均为 `xarray.Dataset`；批量读取函数会沿 `time` 维 `concat`。

## 3. 子模块与典型调用

### 3.1 风廓线雷达 `WindProfileRadar`

```python
# L1 功率谱：维度 (time, Beam, height, Fft)
di = WindProfileRadar.readSingleL1file('Z_RADA_I_57461_..._FFT.BIN')
fft_data = di['FFT_data']                           # DataArray
spec = fft_data.isel(time=0, Beam=0, height=10)     # 单点功率谱

# L2 径向：维度 (level, height_bin)，level ∈ {low, middle, high}
l2d = WindProfileRadar.readSingleL2file('..._RAD.TXT')
rv_E = l2d['E_Radial_Velocity'].sel(level='low')

# L2 -> L3（垂直/水平风速风向）：维度 (height,)
ds_l3 = WindProfileRadar.CalcL2toL3(l2d)            # U/V_Wind_Speed, Wind_Direction, ...
obs_time = ds_l3.attrs['Observation_Time']         # 取观测时间

# L3 产品直接读取
ds_l3 = WindProfileRadar.readSingleL3file('..._ROBS.TXT')
ds_multi = WindProfileRadar.readL3files(sorted(glob.glob('..._ROBS/*.TXT')))  # (time, height)

# 批量 + 多进程
ds_all = WindProfileRadar.readL3files(fps, use_multiprocess=True, multiproces_corenum=8)
```

绘图色标：

```python
WindProfileRadar.velocity_cmap   # ListedColormap
WindProfileRadar.velocity_norm   # BoundaryNorm
```

### 3.2 云雷达 `CloudRadar`

```python
# FFT 单文件：维度 (time, height, FFT_index, dtype)
ds = CloudRadar.readSingleFFTData('..._CLOUD_FFT_M/...')

# 基础数据批量：维度 (time, height)，变量名 Z1/V1/W1/SNR1/ZDR/LDR/DP 等
ds = CloudRadar.readBaseDatas(sorted(glob.glob('..._CLOUD_RAW_M/*')),
                              fixData_Length='max')  # 'max' | 'min' | int

# 绘图：使用 cld accessor
ds.cld.plot('Z1')     # 反射率因子
ds.cld.plot('V1')     # 多普勒速度
ds.cld.plot('W1')     # 速度谱宽
ds.cld.plot('SNR1')   # 信噪比
```

色标内置在 `CloudRadar` 模块（`ref_cmap/ref_norm`、`velocity_cmap/velocity_norm`、`spectrumwith_cmap/...`、`snr_cmap/...`）。

### 3.3 激光雷达 `Lidar`

```python
# L0 原始：维度 (time, range_bin)，变量 c1~c8（各通道）
di = Lidar.readSingleL0File('LIDAR_RAW/...BIN')
ds = Lidar.readL0Files(sorted(glob.glob('LIDAR_RAW/*.BIN')))    # 合并 (time, range_bin)
rcs1064 = ds['c8'].values                                       # (time, range_bin)
meta = ds.lidar.channel_metas                                   # 通过 lidar accessor 取通道元数据

# L1 产品：单一变量 (height,)
ext = Lidar.readSingleL1ProductFile('...REXT.BIN')              # extinction_coefficient
bsc = Lidar.readSingleL1ProductFile('...RBAKSCAT.BIN')          # backscatter_coefficient
dep = Lidar.readSingleL1ProductFile('...DEP.BIN')               # depolarization_ratio
ds_l1 = Lidar.readL1ProductFiles(fps)

# L2 产品：地面/云底等 (time,)
ds_l2 = Lidar.readL2ProductFile('LIDAR_L2/...txt')

# CDWL 风产品 (height,)
cdwl = Lidar.readSingleCDWLBinFile('..._CDWL_MR_*.BIN')
df = cdwl.to_dataframe().reset_index()                          # 转成 pandas 便于后续
```

### 3.4 微波辐射计 `MicroWaveRadiometer`

```python
# 兼容两种数据格式：
#   (a) 长表 + dtype 数值列（旧）：列 '10' 取值 11/12/13/14 -> TEM/WVDen/RHU/WDen
#   (b) 宽表 + 亮温通道（新）：列 CH22.235 ~ CH58.800，每个时间点 1 行
df = MicroWaveRadiometer.readMWRFile('Z_UPAR_I_..._RAW_DD.TXT', encoding='gbk')

# 转 xarray.Dataset
ds = MicroWaveRadiometer.readMWRFileAsDataset(df_path)          # 沿用 readMWRFile 的解析
ds_multi = MicroWaveRadiometer.readMWRFilesAsDataset(fps)        # 多文件 concat

# 直接做 TLogP：取地表温/湿/压
T  = df['SurTem(℃)'].values
RH = df['SurHum(%)'].values
P  = df['SurPre(hPa)'].values
```

### 3.5 工具 `Utils`

```python
from metgrs import Utils

# 风分量互换（数组 -> 数组，返回 (u, v)）
u, v = Utils.vw2uv(wdir, wspd)
wdir, wspd = Utils.vuv2w(u, v)

# 元素解析（XML → dict）
parsed = Utils.parse_element(etree.fromstring(xml_bytes))

# 单值容错
x = Utils.dtryfloat('3.14')   # 3.14
x = Utils.dtryfloat('abc')    # np.nan

# 向量化版本
u, v = Utils.vw2uv(np.array(wdir_list), np.array(wspd_list))
```

## 4. 通用使用模式

### 4.1 批量读取 + 多进程

所有 `readXXXFiles` 系列函数签名一致：

```python
ds = Module.readXXXFiles(
    fps,
    use_multiprocess=True,            # 是否使用 joblib
    multiproces_corenum=-1,           # -1 = 全部核
)
# 失败的文件返回 None，被自动跳过
```

### 4.2 对齐不同高度做时间序列绘图

```python
# 取所有时间点的高度并集 / 最大集
heights = ds.coords['height'].values

# 对每个时间点 reindex 到统一高度（NaN 补缺）
u_aligned = ds['U_Wind_Speed'].reindex({'height': heights}).values  # (time, height)
v_aligned = ds['V_Wind_Speed'].reindex({'height': heights}).values
w_aligned = ds['Vertical_Wind_Speed'].reindex({'height': heights}).values
```

### 4.3 叠加探空 / 风羽的 TLogP

```python
import metpy.calc as mpcalc
from metpy.units import units

T  = show_data['TEM'].values * units.degC
Td = mpcalc.dewpoint_from_relative_humidity(T, show_data['RHU'].values * units.percent).to('degC')
P  = mpcalc.add_height_to_pressure(surf_p * units.hPa,
                                   show_data['height'].values * units.m).to('hPa')

from metpy.plots import SkewT
skew = SkewT(fig, rotation=0)
skew.plot(P, T, 'blue')        # 温度层结
skew.plot(P, Td, 'green')      # 露点层结
skew.plot_barbs(P2, u, v)      # 风羽
```

### 4.4 配色与色标（直接复用模块内置）

| 模块                  | 名称                          | 用途                       |
|-----------------------|-------------------------------|----------------------------|
| `WindProfileRadar`    | `velocity_cmap` / `velocity_norm` | 风廓线速度                 |
| `CloudRadar`          | `ref_cmap` / `ref_norm`       | 反射率因子 Z                |
| `CloudRadar`          | `velocity_cmap` / `velocity_norm` | 多普勒速度 V              |
| `CloudRadar`          | `spectrumwith_cmap` / `..._norm` | 速度谱宽 W               |
| `CloudRadar`          | `snr_cmap` / `snr_norm`       | 信噪比 SNR                  |

## 5. xarray Accessor 速查

| 数据集来源          | accessor   | 提供方法/属性                                |
|---------------------|------------|----------------------------------------------|
| 风廓线雷达          | `.wpr`     | `calc_l1_to_l2`, `calc_l2_to_l3`, `plot_l3_wind` |
| 云雷达              | `.cld`     | `plot(data_name='Z1')`                       |
| 激光雷达            | `.lidar`   | `channel_metas`（DataFrame 形式的通道元数据）  |

## 6. 常见陷阱

1. **依赖 joblib**：`metgrs` 在导入时即 `from joblib import Parallel, delayed`，缺少 `joblib` 会让 `import metgrs` 直接失败。环境里必须安装 `joblib`。
2. **维度对齐**：`WindProfileRadar.readSingleL1file` 单个文件里可能含多条 observation，库已自动按最大 `BinNum`/`ScanBeamN` 零填充对齐，再堆叠为 `(time, Beam, height, Fft)`。`height` 维长度取所有 observation 的最大值。
3. **L3 观测时间位置**：`CalcL2toL3` 返回的 Dataset 只含 `height` 维，观测时间需通过 `ds_l3.attrs['Observation_Time']` 取；批量绘图时按 `attrs` 拼 `dtlist`。
4. **CDWL `b'/x00'`**：当风向/风速/垂直速度在文件中为 `/` 时，读入会变成 `np.nan`。
5. **微波辐射计列名乱码**：`SurTem(℃)` / `Tir(℃)` 等列名含中文括号 `()`，引用时要原样书写；CSV 编码为 `gbk`，不能换成 `utf-8`。
6. **新版 MWR 无 `dtype` 长表列**：`readMWRFile` 内部已做兼容（无 `'10'` 列时不再抛 `KeyError`）；每个时间点对应 1 行宽表，亮温分布在 `CH22.235 ~ CH58.800` 等 24 列中。
7. **`readMWRFileAsDataset` / `readMWRFilesAsDataset`** 内部使用 `xr.concat(..., dim='time')`，要求各文件时间可对齐；不能保证时序连续时建议用 `pd.concat` 自己处理。

## 7. 推荐工作流

```python
import metgrs
from metgrs import WindProfileRadar, CloudRadar, Lidar, MicroWaveRadiometer, Utils
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 1) 批量读取 -> xarray.Dataset
ds = Module.readXXXFiles(fps, use_multiprocess=True)

# 2) 选变量 + 切片
da = ds['Variable'].sel(**{dim: ...})

# 3) 派生量（numpy/metpy）
arr = da.values * scale + offset

# 4) 绘图（直接 .plot / accessor / metpy）
da.plot.imshow(...)
```

## 8. 详细参考

- API 全表：[metgrs 接口参考文档](https://gitcode.com/longtsing/metgrs/blob/xarray/docs/metgrs%E6%8E%A5%E5%8F%A3%E5%8F%82%E8%80%83%E6%96%87%E6%A1%A3.md)
- 可运行示例：[examples/](../../examples/)
  - [1如何读取风廓线雷达数据.ipynb](../../examples/1如何读取风廓线雷达数据.ipynb)
  - [2如何读取云雷达数据并绘图.ipynb](../../examples/2如何读取云雷达数据并绘图.ipynb)
  - [3如何读取激光雷达数据并绘图.ipynb](../../examples/3如何读取激光雷达数据并绘图.ipynb)
  - [4如何读取微波辐射计数据并绘图.ipynb](../../examples/4如何读取微波辐射计数据并绘图.ipynb)
