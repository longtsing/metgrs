---
layout: default
title: metgrs API 参考文档
description: metgrs 库的完整 API 参考文档，包含风廓线仪、云雷达、激光雷达、微波辐射计等设备的数据读取和处理函数
---

# metgrs API 参考文档

## 概述

metgrs 是一个用于读取和处理中国地基遥感垂直观测系统数据的 Python 库，支持风廓线仪、毫米波测云仪、微波辐射计、气溶胶激光观测仪等设备的数据。

**版本**: 0.5.3

**核心特性**:
- 所有数据读取函数返回标准 `xarray.Dataset` 对象
- 通过 xarray accessor 提供领域特定方法
- 支持多进程批量读取
- 完全兼容 xarray 生态系统

---

## 模块结构

```
metgrs/
├── WindProfileRadar.py  # 风廓线雷达数据处理
├── CloudRadar.py        # 云雷达数据处理
├── Lidar.py             # 激光雷达数据处理
├── MicroWaveRadiometer.py # 微波辐射计数据处理
├── Utils.py             # 工具函数
└── base.py              # 基础工具
```

---

## 1. WindProfileRadar 模块

### 1.1 数据读取函数

#### `readSingleL1file(fp: str) -> xr.Dataset`

读取风廓线雷达 L1 功率谱数据文件。

**参数**:
- `fp`: 文件路径，格式为 `Z_RADA_I_IIiii_yyyyMMddhhmmss_O_WPRD_雷达型号_FFT.BIN`

**返回值**: `xr.Dataset`，包含:
- `FFT_data`: 功率谱数据，维度为 `(time, Beam, height, Fft)`
- 坐标: `time`, `Beam`, `height`, `Fft`
- 属性: `FileTag`, `SiteInfo`, `PerformanceInfo`, `ObservationInfo`, `Speed_per_FFT_point`

**示例**:
```python
import metgrs

ds = metgrs.WindProfileRadar.readSingleL1file('path/to/FFT.BIN')
print(ds['FFT_data'].shape)  # (n_times, 5, n_heights, n_fft)
```

---

#### `readSingleL2file(fp: str) -> xr.Dataset`

读取风廓线雷达 L2 径向数据文件。

**参数**:
- `fp`: 文件路径，格式为 `Z_RADA_I_IIiii_yyyyMMddhhmmss_O_WPRD_雷达型号_RAD.TXT`

**返回值**: `xr.Dataset`，包含:
- 数据变量: `Sampling_Height`, `{Beam}_Radial_Velocity`, `{Beam}_Velocity_Spectrum_Width`, `{Beam}_Signal_To_Noise_Ratio`
- 坐标: `level` (low/middle/high), `height_bin`
- 属性: `Station_Id`, `Longitude`, `Latitude`, `Altitude`, `Beam_Order_Flags`, `level_metas`

---

#### `readSingleL3file(fp: str) -> xr.Dataset`

读取风廓线雷达 L3 产品数据文件。

**参数**:
- `fp`: 文件路径，格式为 `Z_RADA_I_IIiii_yyyyMMddhhmmss_P_WPRD_雷达型号_OBS.TXT`

**返回值**: `xr.Dataset`，包含:
- 数据变量: `Wind_Direction`, `Wind_Speed`, `Vertical_Wind_Speed`, `Horizontal_Confidence`, `Vertical_Confidence`, `Cn2`, `U_Wind_Speed`, `V_Wind_Speed`
- 坐标: `height`
- 属性: `Station_Id`, `Longitude`, `Latitude`, `Observation_Time`

---

#### `readSingleROBSfile(fp: str) -> xr.Dataset`

读取风廓线雷达实时产品数据文件。

**参数**:
- `fp`: 文件路径，格式为 `Z_RADA_I_IIiii_yyyyMMddhhmmss_P_WPRD_雷达型号_ROBS.TXT`

**返回值**: 与 `readSingleL3file` 格式相同

---

#### `readSingleHOBSfile(fp: str) -> xr.Dataset`

读取风廓线雷达半小时平均产品数据文件。

**参数**:
- `fp`: 文件路径，格式为 `Z_RADA_I_IIiii_yyyyMMddhhmmss_P_WPRD_雷达型号_HOBS.TXT`

**返回值**: 与 `readSingleL3file` 格式相同

---

#### `readSingleOOBSfile(fp: str) -> xr.Dataset`

读取风廓线雷达一小时平均产品数据文件。

**参数**:
- `fp`: 文件路径，格式为 `Z_RADA_I_IIiii_yyyyMMddhhmmss_P_WPRD_雷达型号_OOBS.TXT`

**返回值**: 与 `readSingleL3file` 格式相同

---

#### `readL3files(fps: list, use_multiprocess=False, multiproces_corenum=-1) -> xr.Dataset`

批量读取 L3 产品数据文件。

**参数**:
- `fps`: 文件路径列表
- `use_multiprocess`: 是否使用多进程，默认为 False
- `multiproces_corenum`: 多进程核心数，默认为 -1（使用全部核心）

**返回值**: 合并后的 `xr.Dataset`，按 `time` 维度拼接

---

#### `readSingleCalibrationXMLfile(fp: str) -> dict`

读取风廓线雷达标校数据 XML 文件。

**参数**:
- `fp`: 文件路径

**返回值**: `dict`，包含标校数据

---

#### `readSingleStatuXMLfile(fp: str) -> dict`

读取风廓线雷达状态数据 XML 文件。

**参数**:
- `fp`: 文件路径

**返回值**: `dict`，包含状态数据

---

### 1.2 数据处理函数

#### `CalcL1toL2(ds_l1, clutter_filter=True, clutter_width=0.5, snr_threshold=-20, n_noise_bins=10) -> xr.Dataset`

将 L1 功率谱数据处理为 L2 径向数据（谱矩法）。

**参数**:
- `ds_l1`: L1 数据集
- `clutter_filter`: 是否启用杂波过滤，默认为 True
- `clutter_width`: 杂波过滤宽度（m/s），默认为 0.5
- `snr_threshold`: 信噪比阈值（dB），默认为 -20
- `n_noise_bins`: 噪声估计使用的频谱 bins 数，默认为 10

**返回值**: `xr.Dataset`，包含:
- 数据变量: `{Beam}_Radial_Velocity`, `{Beam}_Velocity_Spectrum_Width`, `{Beam}_Signal_To_Noise_Ratio`
- 坐标: `time`, `height`
- 属性: `processing_params`（处理参数）

**算法说明**:
1. **噪声估计**: 使用排序法估计噪声底
2. **杂波抑制**: 滤除零速度附近的信号
3. **谱矩计算**:
   - 零阶矩: 总功率
   - 一阶矩: 平均多普勒速度（径向速度）
   - 二阶矩: 速度谱宽
4. **信噪比计算**: 信号功率与噪声功率之比

**示例**:
```python
ds_l1 = metgrs.WindProfileRadar.readSingleL1file('FFT.BIN')
ds_l2 = metgrs.WindProfileRadar.CalcL1toL2(ds_l1)
# 或使用 accessor
ds_l2 = ds_l1.wpr.calc_l1_to_l2()
```

---

#### `CalcL2toL3(ds_l2, qcw=3, interp=False, rollmean=True, rollmeancout=5) -> xr.Dataset`

将 L2 径向数据处理为 L3 产品数据。

**参数**:
- `ds_l2`: L2 数据集
- `qcw`: 质量控制阈值（m/s），默认为 3
- `interp`: 是否插值，默认为 False
- `rollmean`: 是否滚动平均，默认为 True
- `rollmeancout`: 滚动平均窗口大小，默认为 5

**返回值**: `xr.Dataset`，包含:
- 数据变量: `Wind_Direction`, `Wind_Speed`, `Vertical_Wind_Speed`, `U_Wind_Speed`, `V_Wind_Speed`
- 坐标: `height`
- 属性: `Station_Id`, `Longitude`, `Latitude`, `Observation_Time`

**算法说明**:
1. **质量控制**: 检测和剔除异常值
2. **风分量计算**: 从径向速度分解 U/V/W 分量
3. **多波束融合**: 加权平均多个波束的观测
4. **数据平滑**: 可选的插值和滚动平均

**示例**:
```python
ds_l2 = metgrs.WindProfileRadar.readSingleL2file('RAD.TXT')
ds_l3 = metgrs.WindProfileRadar.CalcL2toL3(ds_l2)
# 或使用 accessor
ds_l3 = ds_l2.wpr.calc_l2_to_l3()
```

---

### 1.3 Accessor: `ds.wpr`

所有风廓线雷达数据集都可以通过 `.wpr` 访问器调用领域方法。

#### `ds.wpr.calc_l1_to_l2(...)`

等同于 `CalcL1toL2(ds, ...)`

#### `ds.wpr.calc_l2_to_l3(...)`

等同于 `CalcL2toL3(ds, ...)`

#### `ds.wpr.plot_l3_wind(figsize=(18, 12), show=True, savepath=None)`

绘制 L3 风场数据。

---

## 2. CloudRadar 模块

### 2.1 数据读取函数

#### `readSingleFFTData(fp: str) -> xr.Dataset`

读取云雷达 FFT 谱数据文件。

**参数**:
- `fp`: 文件路径，格式为 `Z_RADA_I_IIiii_yyyyMMddhhmmss_O_YCCR_设备型号_FFT_MM.BIN`

**返回值**: `xr.Dataset`，包含:
- 数据变量: `FFT0`, `FFT1`, ... (FFT 数据)
- 坐标: `time`, `height`, `FFT_index`, `dtype`
- 属性: `GenericHeader`, `SiteConfig`, `RadarConfig`, `TaskConfig`, `CutConfigs`, `RadialHeader`

---

#### `readSingleBaseData(fp: str) -> xr.Dataset`

读取云雷达基数据文件。

**参数**:
- `fp`: 文件路径，格式为 `Z_RADA_I_IIiii_yyyyMMddhhmmss_O_YCCR_设备型号_RAW_MM.BIN`

**返回值**: `xr.Dataset`，包含:
- 数据变量: `Z1`, `V1`, `W1`, `SNR1`, `Z2`, `V2`, `W2`, `SNR2` 等（反射率、速度、谱宽、信噪比）
- 坐标: `time`, `height`
- 属性: `GenericHeader`, `SiteConfig`, `RadarConfig`, `TaskConfig`

---

#### `readFFTDatas(fps: list, use_multiprocess=False, multiproces_corenum=-1) -> xr.Dataset`

批量读取 FFT 谱数据文件。

**参数**:
- `fps`: 文件路径列表
- `use_multiprocess`: 是否使用多进程，默认为 False
- `multiproces_corenum`: 多进程核心数，默认为 -1

**返回值**: 合并后的 `xr.Dataset`，按 `time` 维度拼接

---

#### `readBaseDatas(fps: list, use_multiprocess=False, multiproces_corenum=-1, fixData_Length='max') -> xr.Dataset`

批量读取基数据文件。

**参数**:
- `fps`: 文件路径列表
- `use_multiprocess`: 是否使用多进程，默认为 False
- `multiproces_corenum`: 多进程核心数，默认为 -1
- `fixData_Length`: 数据对齐方式，'max'（最大长度）/ 'min'（最小长度）/ 指定长度

**返回值**: 合并后的 `xr.Dataset`

---

#### `readSingleProductFile(fp: str) -> xr.Dataset`

读取云雷达产品数据文件。

**参数**:
- `fp`: 文件路径，格式为 `Z_RADA_I_IIiii_yyyyMMddhhmmss_P_YCCR_设备型号_CP_M.TXT`

**返回值**: `xr.Dataset`，包含:
- 数据变量: 气象产品数据（如温度、湿度、降水等）
- 坐标: `time`

---

#### `readStatuXMLfile(fp: str) -> dict`

读取云雷达状态数据 XML 文件。

**参数**:
- `fp`: 文件路径

**返回值**: `dict`，包含状态数据

---

#### `readSingleCalibrationXMLfile(fp: str) -> dict`

读取云雷达标校数据 XML 文件。

**参数**:
- `fp`: 文件路径

**返回值**: `dict`，包含标校数据

---

### 2.2 Accessor: `ds.cld`

所有云雷达数据集都可以通过 `.cld` 访问器调用领域方法。

#### `ds.cld.plot(data_name='Z1', figsize=(18, 12), cmap=None, norm=None, show=True, savepath=None)`

绘制云雷达数据。

**参数**:
- `data_name`: 数据变量名，如 'Z1', 'V1', 'W1', 'SNR1' 等
- `figsize`: 图像尺寸
- `cmap`: 颜色映射
- `norm`: 归一化
- `show`: 是否显示图像
- `savepath`: 保存路径

**示例**:
```python
ds = metgrs.CloudRadar.readSingleBaseData('RAW.BIN')
ds.cld.plot(data_name='Z1', savepath='reflectivity.png')
```

---

## 3. Lidar 模块

### 3.1 数据读取函数

#### `readSingleL0File(l0file: str) -> xr.Dataset`

读取激光雷达 L0 原始数据文件。

**参数**:
- `l0file`: 文件路径，格式为 `Z_RADR_I_IIiii_yyyyMMddhhmmss_O_LIDAR_设备型号_L0.BIN`

**返回值**: `xr.Dataset`，包含:
- 数据变量: `c1`, `c2`, ... (各通道数据)
- 坐标: `time`, `range_bin`
- 属性: `Observe_Time`, `Channel_Count`, `Channel_Metas`

---

#### `readSingleCDWLBinFile(binfile: str) -> xr.Dataset`

读取激光雷达 CDWL 二进制数据文件。

**参数**:
- `binfile`: 文件路径

**返回值**: `xr.Dataset`，包含:
- 数据变量: `WindDirection`, `HorizontalWindSpeed`, `VerticalWindSpeed`
- 坐标: `height`
- 属性: `Station_Code`, `Station_Name`, `Latitude_deg`, `Longitude_deg`, `Observe_Time`

---

#### `readSingleL1ProductFile(binfile: str) -> xr.Dataset`

读取激光雷达 1 级产品数据文件。

**参数**:
- `binfile`: 文件路径，格式为 `Z_RADR_I_IIiii_yyyyMMddhhmmss_P_LIDAR_设备型号_L1_产品类型_波长.BIN`

**返回值**: `xr.Dataset`，包含:
- 数据变量: `extinction_coefficient` / `backscatter_coefficient` / `depolarization_ratio`
- 坐标: `height`
- 属性: `Product_Type`, `Wavelength`, `Height_Resolution`

---

#### `readSingleL2ProductFile(txtfile: str) -> xr.Dataset`

读取激光雷达 2 级产品数据文件。

**参数**:
- `txtfile`: 文件路径，格式为 `Z_RADR_I_IIiii_yyyyMMddhhmmss_P_LIDAR_设备型号_L2_AVMPC.TXT`

**返回值**: `xr.Dataset`，包含:
- 数据变量: `Surface_Temperature`, `Surface_Humidity`, `Surface_Pressure`, `TIR`, `Rain`, 云信息, 颗粒物浓度等
- 坐标: `time`

---

#### `readL0Files(fps: list, use_multiprocess=False, multiproces_corenum=-1) -> xr.Dataset`

批量读取 L0 原始数据文件。

**参数**:
- `fps`: 文件路径列表
- `use_multiprocess`: 是否使用多进程
- `multiproces_corenum`: 多进程核心数

**返回值**: 合并后的 `xr.Dataset`

---

#### `readCDWLBinFiles(fps: list, use_multiprocess=False, multiproces_corenum=-1) -> xr.Dataset`

批量读取 CDWL 数据文件。

**参数**:
- `fps`: 文件路径列表
- `use_multiprocess`: 是否使用多进程
- `multiproces_corenum`: 多进程核心数

**返回值**: 合并后的 `xr.Dataset`

---

#### `readL1ProductFiles(fps: list, use_multiprocess=False, multiproces_corenum=-1) -> xr.Dataset`

批量读取 1 级产品数据文件。

**参数**:
- `fps`: 文件路径列表
- `use_multiprocess`: 是否使用多进程
- `multiproces_corenum`: 多进程核心数

**返回值**: 合并后的 `xr.Dataset`

---

#### `readL2ProductFiles(fps: list, use_multiprocess=False, multiproces_corenum=-1) -> xr.Dataset`

批量读取 2 级产品数据文件。

**参数**:
- `fps`: 文件路径列表
- `use_multiprocess`: 是否使用多进程
- `multiproces_corenum`: 多进程核心数

**返回值**: 合并后的 `xr.Dataset`

---

#### `readSingleStatusXMLFile(fp: str) -> dict`

读取激光雷达状态数据 XML 文件。

**参数**:
- `fp`: 文件路径

**返回值**: `dict`，包含状态数据

---

#### `readSingleCalibrationXMLFile(fp: str) -> dict`

读取激光雷达标校数据 XML 文件。

**参数**:
- `fp`: 文件路径

**返回值**: `dict`，包含标校数据

---

### 3.2 Accessor: `ds.lidar`

所有激光雷达数据集都可以通过 `.lidar` 访问器调用领域方法。

#### `ds.lidar.channel_metas`

获取通道元数据。

**返回值**: `pd.DataFrame`，包含通道信息

**示例**:
```python
ds = metgrs.Lidar.readSingleL0File('L0.BIN')
print(ds.lidar.channel_metas)
```

---

## 4. MicroWaveRadiometer 模块

### 4.1 数据读取函数

#### `readMWRFile(filename, encoding='gbk') -> pd.DataFrame`

读取微波辐射计数据文件，返回 pandas DataFrame。

**参数**:
- `filename`: 文件路径
- `encoding`: 文件编码，默认为 'gbk'

**返回值**: `pd.DataFrame`

---

#### `readMWRFileAsDataset(filename, encoding='gbk') -> xr.Dataset`

读取微波辐射计数据文件，返回 xarray Dataset。

**参数**:
- `filename`: 文件路径
- `encoding`: 文件编码，默认为 'gbk'

**返回值**: `xr.Dataset`，包含:
- 数据变量: 各观测参数
- 坐标: `time`
- 属性: `File_Path`, `columns`

---

#### `readMWRFilesAsDataset(fps: list, use_multiprocess=False, multiproces_corenum=-1) -> xr.Dataset`

批量读取微波辐射计数据文件。

**参数**:
- `fps`: 文件路径列表
- `use_multiprocess`: 是否使用多进程
- `multiproces_corenum`: 多进程核心数

**返回值**: 合并后的 `xr.Dataset`

---

## 5. Utils 模块

### 5.1 工具函数

#### `parse_element(element) -> dict`

解析 XML 元素为字典。

**参数**:
- `element`: XML 元素

**返回值**: `dict`

---

#### `vuv2w(u, v) -> tuple`

将 U/V 风分量转换为风向和风速。

**参数**:
- `u`: U 风分量
- `v`: V 风分量

**返回值**: `(wind_direction, wind_speed)`

---

#### `vw2uv(wdir, wspd) -> tuple`

将风向和风速转换为 U/V 风分量。

**参数**:
- `wdir`: 风向（度）
- `wspd`: 风速（m/s）

**返回值**: `(u, v)`

---

#### `isInt(s) -> bool`

检查字符串是否为整数。

**参数**:
- `s`: 字符串

**返回值**: `bool`

---

## 6. 数据结构说明

### 6.1 风廓线雷达数据层次

```
L1 (原始数据): FFT 功率谱
    ↓ CalcL1toL2() - 谱矩法
L2 (径向数据): 径向速度、谱宽、信噪比
    ↓ CalcL2toL3() - 风分量合成
L3 (产品数据): 水平风向、风速、垂直风速
```

### 6.2 云雷达数据类型

- **FFT 数据**: 多普勒谱数据
- **基数据**: 反射率 (Z)、径向速度 (V)、谱宽 (W)、信噪比 (SNR)
- **产品数据**: 气象产品（温度、湿度、降水等）

### 6.3 激光雷达数据层次

```
L0 (原始数据): 各通道回波信号
    ↓ 处理算法
L1 (1级产品): 消光系数、后向散射系数、退偏振比
    ↓ 反演算法
L2 (2级产品): 光学厚度、能见度、混合层高度、云信息、颗粒物浓度
```

---

## 7. 常见用法示例

### 7.1 风廓线雷达数据处理

```python
import metgrs

# 读取 L1 数据
ds_l1 = metgrs.WindProfileRadar.readSingleL1file('FFT.BIN')

# L1 → L2 处理
ds_l2 = ds_l1.wpr.calc_l1_to_l2(clutter_filter=True)

# L2 → L3 处理
ds_l3 = ds_l2.wpr.calc_l2_to_l3(qcw=3, rollmean=True)

# 绘制风场
ds_l3.wpr.plot_l3_wind(savepath='wind_profile.png')
```

### 7.2 云雷达数据可视化

```python
import metgrs

# 读取基数据
ds = metgrs.CloudRadar.readSingleBaseData('RAW.BIN')

# 绘制反射率
ds.cld.plot(data_name='Z1', savepath='reflectivity.png')

# 绘制径向速度
ds.cld.plot(data_name='V1', savepath='velocity.png')
```

### 7.3 批量数据读取

```python
import glob
import metgrs

# 获取文件列表
files = sorted(glob.glob('data/*.BIN'))

# 批量读取（多进程）
ds = metgrs.CloudRadar.readBaseDatas(files, use_multiprocess=True)

# 绘制时间序列
ds.cld.plot(data_name='Z1')
```

### 7.4 激光雷达产品数据

```python
import metgrs

# 读取 1 级产品
ds_l1 = metgrs.Lidar.readSingleL1ProductFile('L1_EXT.BIN')

# 读取 2 级产品
ds_l2 = metgrs.Lidar.readSingleL2ProductFile('L2_AVMPC.TXT')

# 获取通道元数据
print(ds_l1.lidar.channel_metas)
```

---

## 8. 依赖项

- numpy
- pandas
- xarray
- matplotlib
- joblib
- python-dateutil

---

## 9. 版本历史

- **0.5.3**: 
  - 重构为 xarray accessor 架构
  - 移除自定义 originData 对象
  - 添加 L1→L2 谱矩法处理
  - 补充所有设备的产品数据读取
  - 完善文档

---

## 10. 许可证

MIT License
