# Py-ART 使用指南

> The Python ARM Radar Toolkit：国际通用的天气雷达读取、QC、退模糊、产品反演与绘图库。
> 本 skill 对应 9 月 15 日《Py-ART 基础应用介绍与实习》。
> 仓库：https://github.com/ARM-DOE/pyart

## 1. 适用场景

当用户的任务涉及以下任一情况时，调用本 skill：

- 把 PyCINRAD 读出的中国雷达基数据（SA/SB/CA/CB、相控阵 AR2/YLD）转换成 Py-ART `Radar` 对象
- 画极坐标 PPI（`RadarDisplay`）和地图 PPI（`RadarMapDisplay`）
- 多普勒速度退模糊（`dealias_region_based`）
- 双偏振质量控制（`GateFilter`）与衰减订正（`calculate_attenuation`）
- 雷达定量估测降水（Z-R、Kdp-R 关系）
- 计算速度纹理、组合反射率、回波顶、VIL 等产品

## 2. 安装与导入

```bash
pip install arm-pyart
# Windows 上若 dealias 报错，需要 MSVC 编译器或用预编译 wheel
```

```python
import pyart
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import cartopy.crs as ccrs
from cinrad.io import StandardData
from cinrad.io.export import standard_data_to_pyart

mpl.rcParams['font.family'] = 'SimHei'
mpl.rcParams['font.size'] = 15
mpl.rcParams['axes.unicode_minus'] = False
```

## 3. 数据导入：中国基数据 → Py-ART

Py-ART 原生不读中国 `.bin/.bz2` 标准格式，统一走 PyCINRAD 桥接：

```python
# S 波段双偏振
f = StandardData("D:/Py-ART实习/data/Z_RADR_I_Z9731_20210510070930_O_DOR_SAD_CAP_FMT.BIN.bz2")
# X 波段相控阵 AR2
f = StandardData("D:/Py-ART实习/data/NUIST.20150627.002438.AR2.bz2")
# X 波段双偏振相控阵 YLD2-D
f = StandardData("D:/Py-ART实习/data/Z_RADR_I_ZT002_20230727233114_O_DOR_YLD2-D_CAP_FMT.bin.bz2")

radar = standard_data_to_pyart(f)
print(radar.fields.keys())          # dict_keys(['reflectivity','velocity','cross_correlation_ratio',...])
print(radar.fields['reflectivity']['data'].shape)
```

字段命名约定（Py-ART 英文名，与 PyCINRAD/PyCWR 不同）：

| Py-ART                      | 含义           |
|-----------------------------|----------------|
| `reflectivity`              | 反射率 dBZ     |
| `velocity`                  | 径向速度 m/s   |
| `spectrum_width`            | 谱宽           |
| `differential_reflectivity` | ZDR            |
| `differential_phase`        | PhiDP          |
| `cross_correlation_ratio`   | CC / RHO       |
| `specific_differential_phase`| KDP           |

## 4. 绘图

### 4.1 极坐标 PPI（`RadarDisplay`）

```python
display = pyart.graph.RadarDisplay(radar)

fig = plt.figure(figsize=(12, 9), dpi=200)
ax = fig.add_subplot(221)
display.plot_ppi(
    field='reflectivity', sweep=0, ax=ax,
    title='(a) Reflectivity el=0.5°',
    colorbar_label='dBZ',
    axislabels=('', '南北向雷达径向距离/km'),
)
display.set_limits((-150, 150), (-150, 150), ax=ax)
display.plot_range_rings([50, 150], ax=ax, col='k', ls='--', lw=0.5)

# 只画 >=40 dBZ：mask_tuple
display.plot_ppi('reflectivity', sweep=2, ax=ax,
                 mask_tuple=['reflectivity', 40],
                 title=r'(c) Reflectivity$\geq$40 el=1.5°')
```

### 4.2 地图 PPI（`RadarMapDisplay`）

```python
display = pyart.graph.RadarMapDisplay(radar)
fig = plt.figure(figsize=(6, 4), dpi=200)
ax = fig.add_subplot(111, projection=ccrs.PlateCarree())
display.plot_ppi_map(
    'reflectivity', 2, ax=ax,
    vmin=-5, vmax=75,
    lat_lines=[25, 27, 29, 31],
    lon_lines=[110, 112, 114, 116],
    resolution='10m',                       # 10m / 50m / 110m
    colorbar_label='反射率因子/dBZ',
    projection=ccrs.PlateCarree(),
)
display.plot_point(lon=112, lat=30, symbol='ro', label_text='标点')
```

### 4.3 地图范围用经纬度裁剪

```python
display.plot_ppi_map('est_rain_z', sweep=2, ax=ax,
                     min_lon=117, max_lon=120,
                     min_lat=31.5, max_lat=33.5,
                     resolution='10m')
```

## 5. 速度退模糊

```python
# 1) 读 Nyquist 速度
nyq = radar.instrument_parameters['nyquist_velocity']['data']

# 2) 算速度纹理（异常值检测）
vel_texture = pyart.retrieve.calculate_velocity_texture(
    radar, vel_field='velocity', nyq=nyq[-1])
radar.add_field('texture', vel_texture, replace_existing=True)

# 3) GateFilter：纹理 >2 的门滤掉
gf = pyart.filters.GateFilter(radar)
gf.exclude_above('texture', 2)

# 4) 区域法退模糊
dealiased = pyart.correct.dealias_region_based(
    radar, vel_field='velocity',
    nyquist_vel=nyq, centered=True, gatefilter=gf)
radar.add_field('corrected_velocity', dealiased, replace_existing=True)
```

## 6. QC 与衰减订正

```python
gf = pyart.filters.GateFilter(radar)
gf.exclude_below('reflectivity', 10)          # 去弱噪声
gf.exclude_below('cross_correlation_ratio', 0.7)  # 去地物/生物回波

# C/X 波段衰减订正（需要 normalized_coherent_power 字段，没有就造假字段）
if 'normalized_coherent_power' not in radar.fields:
    ncp = np.ones((radar.nrays, radar.ngates), dtype=np.float32)
    radar.add_field('normalized_coherent_power', {
        'data': ncp, 'units': 'ratio',
        'long_name': 'Normalized Coherent Power (Dummy)',
        'standard_name': 'normalized_coherent_power'})

if 'differential_phase' in radar.fields:
    spec_at, cor_z = pyart.correct.calculate_attenuation(
        radar, z_offset=0.0,
        refl_field='reflectivity',
        phidp_field='differential_phase',
        rhv_field='cross_correlation_ratio',
        gatefilter=gf)
    radar.add_field('corrected_reflectivity', cor_z, replace_existing=True)
```

## 7. 雷达估测降水

```python
# Z-R 关系
rain_z = pyart.retrieve.est_rain_rate_z(
    radar, alpha=0.0376, beta=0.6112,
    refl_field='corrected_reflectivity')
radar.add_field('est_rain_z', rain_z, replace_existing=True)

# Kdp-R 关系
rain_kdp = pyart.retrieve.est_rain_rate_kdp(radar)
radar.add_field('est_rain_kdp', rain_kdp, replace_existing=True)
```

## 8. 常见陷阱

1. **字段名是 Py-ART 英文名**：`reflectivity` 不是 `REF`，`cross_correlation_ratio` 不是 `RHO`。
2. **数据在 `['data']` 里**：`radar.fields['reflectivity']['data']` 才是二维数组。
3. **`sweep` 是序号不是角度**：`sweep=0` 通常对应 0.5°，`sweep=2` 对应 1.5°，先 `radar.sweep_number['data']` 查。
4. **`dealias_region_based` 需要 C 编译器**：Windows 上失败就换预编译 wheel，或直接用 PyCINRAD 的 `cinrad.correct.dealias`。
5. **衰减订正必须有 `differential_phase`**：没有就跳过；`normalized_coherent_power` 缺失要造假字段。
6. **估雨要在零度层以下**：`sweep` 选低仰角，别选 6° 以上。
7. **`set_limits` 单位是 km**：`(-150,150)` 不是像素。
8. **中文字体**：先 `SimHei`/`Microsoft YaHei`，否则 colorbar 标签乱码。

## 9. 推荐工作流

```python
# 1) 桥接导入
f = StandardData(fp)
radar = standard_data_to_pyart(f)

# 2) QC
gf = GateFilter(radar)
gf.exclude_below('reflectivity', 10)
gf.exclude_below('cross_correlation_ratio', 0.7)

# 3) 退模糊（可选）
# 4) 衰减订正 + 估雨（可选）

# 5) 画图
display = pyart.graph.RadarMapDisplay(radar)
display.plot_ppi_map('reflectivity', sweep=0, resolution='10m',
                     vmin=-5, vmax=75)
```

## 10. 详细参考

- GitHub: https://github.com/ARM-DOE/pyart
- 文档: https://arm-doe.github.io/pyart/
- 本地讲义：`H:\hn\一、Py-ART实习\`
  - `pyart case 01.py` —— PPI 多仰角多产品 + mask_tuple
  - `pyart case 02.py` —— 地图 PPI + plot_point
  - `pyart case 03.py` —— 速度纹理 + dealias_region_based
  - `pyart case 04.py` —— GateFilter + 衰减订正 + Z-R / Kdp-R 估雨
- 示例数据：`H:\hn\一、Py-ART实习\data\`
