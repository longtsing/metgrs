# pycwr 使用指南

> 中国新一代天气雷达（CINRAD SA/SB、相控阵 AR2/YLD 等）基数据解码、几何、绘图、QC、水凝物分类、单雷达风场反演、多雷达拼图的 Python 工具库。
> 仓库：https://github.com/YvZheng/pycwr

## 1. 适用场景

当用户的任务涉及以下任一情况时，调用本 skill：

- 解码中国雷达基数据 `.bin`/`.bz2`（SA/SB/CB/SC/CC、相控阵 AR2 / YLD2-D 等），返回 `PRD` 数据模型
- 检查/汇总雷达扫描：`summary()`、`available_fields()`、`sweep_summary()`
- 提取单仰角单变量：`get_sweep_field(sweep, "dBZ" | "V" | "ZDR" | "RHO" | "KDP" | ...)`
- 画 PPI / 地图 PPI / 剖面图（RHI / VCS）/ 任意网格产品
- 双偏振 QC：`apply_dualpol_qc`
- 水凝物分类 HCL（`classify_hydrometeors`）
- 单雷达风场反演：`retrieve_vad` / `retrieve_vvp` / `retrieve_vwp` / `retrieve_wind_volume_xy|lonlat`
- 雷达产品计算：`add_product_CR_xy` / `add_product_CAPPI_xy` / `add_product_VIL_xy` / `add_product_ET_xy` / `add_product_VWP`
- 多雷达拼图（`pycwr.interp.run_radar_network_3d`）
- 导出到 Py-ART / xradar / NetCDF

## 2. 安装与导入

```bash
# 基线安装（足够做读取 + PRD + 几何 + 导出）
pip install pycwr
# 完整安装（绘图、QC、Py-ART/xradar 互操作、Web viewer 等可选依赖）
pip install "pycwr[full]"
# Python 3.9 ~ 3.12，pandas<3
```

```python
from pycwr.io import read_auto
from pycwr.draw import plot_ppi, plot_ppi_map, plot_section, plot_section_lonlat
from pycwr.draw.RadarPlot import Graph, GraphMap, plot_xy
from pycwr.qc import apply_dualpol_qc
from pycwr.retrieve import classify_hydrometeors, retrieve_vad, retrieve_vvp, retrieve_vwp, retrieve_wind_volume_xy
import numpy as np
import matplotlib.pyplot as plt
```

中文字体：

```python
plt.rcParams['font.family'] = 'SimHei'
plt.rcParams['font.size'] = 15
plt.rcParams['axes.unicode_minus'] = False
```

数据通常放在一个固定路径下（实习用 `C:/pycwr实习/data/`），常见文件名形如：

```
Z_RADR_I_Z9731_20210510070930_O_DOR_SAD_CAP_FMT.BIN.bz2
Z_RADR_I_Z9736_20170731004600_O_DOR_SB_CAP.bin.bz2
NUIST.20150627.002438.AR2.bz2
Z_RADR_I_ZT002_20230727233114_O_DOR_YLD2-D_CAP_FMT.bin.bz2
```

## 3. 核心对象 `PRD`

`pycwr.io.read_auto(...)` 一律返回 [`PRD`](file:///e:/study/metgrs/.skills/pycwr/skill.md) 对象，它代表一个完整体扫。

常用属性：

| 属性 / 方法                 | 含义                                                       |
|-----------------------------|------------------------------------------------------------|
| `fields`                    | list[xarray.Dataset]，每个元素对应一个仰角                 |
| `scan_info`                 | 站点、扫描元信息                                           |
| `extended_fields`           | 对齐与原始距离不同时，附加的"原始侧车"字段                |
| `product`                   | `add_product_*` 写入的派生产品 `xarray.Dataset`            |
| `summary()`                 | 体扫整体摘要                                               |
| `available_fields(sweep=…)` | 当前可用变量（`dBZ`/`V`/`W`/`ZDR`/`RHO`/`KDP`/…）          |
| `sweep_summary()`           | 各仰角的仰角/库长等                                        |
| `get_sweep_field(s, f)`     | 取第 s 个仰角、变量 f（`range_mode="aligned"` / `"native"`） |
| `get_native_sweep_field`    | 强制取原生距离库                                            |
| `ordered_az(inplace=False)` | 按方位角排序                                                |

### 3.1 读取

```python
from pycwr.io import read_auto
file = r"C:/pycwr实习/data/Z_RADR_I_Z9731_20210510070930_O_DOR_SAD_CAP_FMT.BIN.bz2"
radar = read_auto(file)
print(radar.summary())
print(radar.available_fields())
print(radar.sweep_summary()[0])
```

### 3.2 取单仰角单变量

```python
dBZ0      = radar.get_sweep_field(0, "dBZ")          # 默认 aligned
velocity0 = radar.get_sweep_field(0, "V")

# aligned vs native（低仰角反射率有时比 Doppler 库长）
aligned = radar.get_sweep_field(0, "dBZ", range_mode="aligned")
native  = radar.get_sweep_field(0, "dBZ", range_mode="native")
```

## 4. 绘图（`pycwr.draw`）

### 4.1 PPI 与地图 PPI

```python
from pycwr.draw import plot_ppi, plot_ppi_map

plot_ppi(radar, field="dBZ", sweep=0, show=True)
plot_ppi_map(radar, field="dBZ", sweep=0, show=True)
```

`plot_ppi` 支持 `ax=`、`title=`、`clabel=` 等参数，组合 matplotlib 子图：

```python
import matplotlib.pyplot as plt
fig = plt.figure(figsize=(12, 4))
ax1 = fig.add_subplot(1, 2, 1)
plot_ppi(radar, field="dBZ", sweep=0, show=False, ax=ax1,
         title="(a) 质控前", clabel='基本反射率因子/dBZ')
ax1.set_xlabel('东西向雷达径向距离/km')
ax1.set_ylabel('南北向雷达径向距离/km')
ax1.set_xlim(-230, 230)
ax1.set_ylim(-230, 230)
plt.show()
```

显式色标覆盖：

```python
plot_ppi_map(radar, field="V", sweep=0, cmap="CN_vel", min_max=(-27.0, 27.0), show=True)
```

### 4.2 剖面 / VCS

```python
from pycwr.draw import plot_section, plot_section_lonlat

# 极坐标: start=(起始方位角°, 起始径向距离km), end=(终点方位角°, 终点径向距离km)
plot_section(radar, start=(30, 60), end=(90, 60), field="dBZ",
             show=True, title="section")
# 经纬度版
plot_section_lonlat(radar, start=(lon0, lat0), end=(lon1, lat1), field="dBZ")
```

### 4.3 自定义网格 / `Graph`、`GraphMap`、`plot_xy`

```python
from pycwr.draw.RadarPlot import GraphMap, plot_xy
import cartopy.crs as ccrs
import numpy as np

# 自定义 xy 网格
x1d = np.arange(-150000, 150001, 1000)
y1d = np.arange(-150000, 150001, 1000)

PRD = read_auto(filename)
PRD.add_product_CAPPI_xy(XRange=x1d, YRange=y1d, level_height=3000)

grid_x, grid_y = np.meshgrid(x1d, y1d, indexing="ij")
fig, ax = plt.subplots()
plot_xy(ax, grid_x, grid_y, PRD.product.CAPPI_3000_native)
ax.set_xlabel("东西向距离 (km)"); ax.set_ylabel("南北向距离 (km)")
plt.show()
```

经纬度版 + 地图投影：

```python
lon1d = np.arange(117, 120.001, 0.01)
lat1d = np.arange(31, 34.001, 0.01)
radar.add_product_CAPPI_lonlat(XLon=lon1d, YLat=lat1d, level_height=3000)

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
graph = GraphMap(radar, transform=ccrs.PlateCarree())
graph.plot_cappi_map(ax, level_height=3000, extend=[117, 120, 31, 34])
plt.show()
```

### 4.4 风廓线

```python
from pycwr.draw.RadarPlot import Graph

graph = Graph(None)
graph.plot_wind_profile(ax=ax, profile=vwp, title="Vertical Wind Profile",
                        color="#1f77b4", show_barbs=True, annotate_samples=True)
```

## 5. 质量控制（`pycwr.qc`）

```python
from pycwr.qc import apply_dualpol_qc

qc_radar = apply_dualpol_qc(radar, inplace=False, clear_air_mode="mask", band='S')
```

- `inplace=False` 不破坏原 `radar`，返回新的 `PRD`
- `clear_air_mode`：`"mask"` / 其它
- `band`：`"S"` / `"C"` / `"X"`
- 校正后变量：`Zc`、`ZDRc`、`PhiDPc`、`KDPc`；掩码字段 `QC_MASK`、`CLEAR_AIR_MASK` 等

## 6. 水凝物分类 HCL（`pycwr.retrieve`）

```python
hcl_radar = radar.classify_hydrometeors(
    inplace=False,
    band="X",                                              # S/C/X
    profile_height=[0.0, 2000.0, 4000.0, 8000.0, 12000.0],
    profile_temperature=[24.0, 12.0, 2.0, -16.0, -40.0],
    confidence_field="HCL_CONF",
    temperature_field="HCL_T",
)
print(hcl_radar.fields[0]['HCL'])                          # 第 0 仰角 HCL 数组
plot_ppi(hcl_radar, field='HCL', sweep=1)
```

也可直接 `classify_hydrometeors(...)` 对 ndarray 进行分类。

## 7. 单雷达风场反演（`pycwr.retrieve`）

四个内置工作流：

| 方法                                       | 输出                          | 用途                       |
|--------------------------------------------|-------------------------------|----------------------------|
| `radar.retrieve_vad(sweeps=…)`             | 一个或多个仰角的 VAD 廓线     | 单仰角方位谐波拟合         |
| `radar.retrieve_vvp(sweep=…)`              | 单仰角局部水平风 (u, v)       | 单仰角 VVP                 |
| `radar.retrieve_vwp(sweeps=…)`             | 垂直风廓线                    | 多仰角 VAD 汇总            |
| `radar.retrieve_wind_volume_xy/lonlat(...)`| 固定高度水平风 (u, v) 体      | VVP 三维拼装 + 高度聚合    |

```python
vad_profile = radar.retrieve_vad(sweeps=0)
vvp         = radar.retrieve_vvp(0)
vwp         = radar.retrieve_vwp(sweeps=[0, 1, 2])
```

三维风体推荐写法：

```python
wind = radar.retrieve_wind_volume_xy(
    XRange=np.arange(-60_000.0, 60_001.0, 5_000.0),
    YRange=np.arange(-60_000.0, 60_001.0, 5_000.0),
    level_heights=np.arange(500.0, 3_500.0, 500.0),
    sweeps=None,                # None/"auto" 自动选最强仰角；"all" 全部
    max_range_km=60.0,
    az_num=31, bin_num=5,
    azimuth_step=12, range_step=6,
    horizontal_radius_m=8_000.0, max_horizontal_radius_m=14_000.0,
    horizontal_min_neighbors=3,
    vertical_tolerance_m=400.0, max_vertical_gap_m=1_200.0,
    workers=4,                  # 进程级并行
)
```

输出变量：`u`, `v`, `wind_speed`, `wind_direction`, `fit_rmse`, `valid_count`, `source_sweep_count`, `neighbor_count`, `effective_vertical_support`, `sweep_spread_m`, `quality_score`, `quality_flag`（0/1/2/3 = 无效/低/可用/高置信度）。

存入 `radar.product`：

```python
radar.add_product_VWP(sweeps=[0, 1, 2], max_range_km=40.0, height_step=500.0)
radar.add_product_WIND_VOLUME_xy(XRange=..., YRange=..., level_heights=..., sweeps=[0, 1, 2])
```

### 7.1 VAD/VVP/VWP 手动画图示例

```python
import matplotlib.pyplot as plt
import numpy as np

# VAD 高度廓线
height_km = vad_profile['height'].values.flatten() / 1000.0
speed     = vad_profile['wind_speed'].values.flatten()
u         = vad_profile['u'].values.flatten()
v         = vad_profile['v'].values.flatten()

fig, ax = plt.subplots(figsize=(6, 8))
ax.plot(speed, height_km, color='blue', linewidth=1.5, marker='o',
        markersize=3, label='Wind Speed')
ax.set_xlabel("Wind Speed (m/s)"); ax.set_ylabel("Height (km)")
ax.set_title("Vertical Wind Profile"); ax.grid(True, linestyle='--', alpha=0.6)

# 风羽
skip = 40
barb_x = np.zeros_like(height_km[::skip]) + np.nanmax(speed) * 1.1
ax.barbs(barb_x, height_km[::skip], u[::skip], v[::skip], length=6, color='red')
ax.set_xlim(0, np.nanmax(speed) * 1.3)
plt.tight_layout(); plt.show()
```

```python
# VVP 水平风场
x_km   = vvp['x'].values / 1000.0
y_km   = vvp['y'].values / 1000.0
speed  = vvp['wind_speed'].values
u, v   = vvp['u'].values, vvp['v'].values

X_MIN, X_MAX, Y_MIN, Y_MAX = 20, 80, 10, 70
skip_az, skip_r = 10, 20

fig, ax = plt.subplots(figsize=(8, 7))
pm = ax.pcolormesh(x_km, y_km, speed, cmap='viridis', shading='auto', vmin=0, vmax=25)
plt.colorbar(pm, ax=ax, shrink=0.8).set_label('Wind Speed (m/s)')
ax.quiver(x_km[::skip_az, ::skip_r], y_km[::skip_az, ::skip_r],
          u[::skip_az, ::skip_r], v[::skip_az, ::skip_r],
          color='black', scale=300, width=0.003, headwidth=3)
ax.set_xlim(X_MIN, X_MAX); ax.set_ylim(Y_MIN, Y_MAX)
ax.set_aspect('equal'); ax.set_xlabel("East Distance (km)"); ax.set_ylabel("North Distance (km)")
ax.plot(0, 0, marker='+', color='red', markersize=15, markeredgewidth=2)
plt.tight_layout(); plt.show()
```

## 8. 派生产品（`PRD.add_product_*`）

| 方法                              | 含义                                       |
|-----------------------------------|--------------------------------------------|
| `add_product_CR_xy(x, y)`         | 组合反射率（极坐标）                       |
| `add_product_CAPPI_xy(x, y, h)`   | 固定高度 CAPPI（极坐标，单位 m）           |
| `add_product_CAPPI_3d_xy(...)`    | 三维 CAPPI 体                              |
| `add_product_VIL_xy(x, y, levels)`| 垂直累积液态水含量                         |
| `add_product_ET_xy(x, y)`         | 回波顶高                                   |
| `add_product_CR_lonlat(...)`      | 经纬度网格版 CR                            |
| `add_product_CAPPI_lonlat(...)`   | 经纬度网格版 CAPPI                         |
| `add_product_VIL_lonlat(...)`     | 经纬度网格版 VIL                           |
| `add_product_ET_lonlat(...)`      | 经纬度网格版 ET                            |
| `add_product_VWP(...)`            | 风廓线产品                                 |

```python
x1d = np.arange(-150000, 150001, 1000)
y1d = np.arange(-150000, 150001, 1000)
PRD.add_product_CR_xy(x1d, y1d)
PRD.add_product_CAPPI_xy(x1d, y1d, level_height=3000)
PRD.add_product_VIL_xy(x1d, y1d, [1000.0, 2000.0, 3000.0])
```

读出：

```python
print(PRD.product)                                     # 整体 product DataSet
plot_xy(ax, grid_x, grid_y, PRD.product.CAPPI_3000_native)
```

## 9. 多雷达拼图

```python
from pycwr.interp import run_radar_network_3d
```

在 lon/lat 规则网格上拼 3D 网络产品，可直接写 NetCDF。

## 10. 导出与互操作

```python
radar.to_wsr98d(path)                # WSR-98D 二进制
radar.to_nexrad_level2_msg31(path)
radar.to_nexrad_level2_msg1(path)
radar.to_pyart_radar()               # Py-ART Radar
radar.to_xradar()                    # xradar
radar.to_cfgridded_netcdf(path)      # CF / NetCDF
```

## 11. Web viewer（可选）

```python
from pycwr.GraphicalInterface import create_app, launch
# 或者命令行：python scripts/LaunchGUI.py
```

## 12. 常见陷阱

1. **`range_mode="aligned"` vs `"native"`**：低仰角反射率有时比 Doppler 库长，默认 aligned（历史兼容），要全距离库要 `native`。
2. **变量名是大小写敏感的 `dBZ` / `V` / `ZDR` / `RHO` / `KDP`**：不是 `REF` / `VEL` / `dbz`。
3. **`apply_dualpol_qc(..., inplace=False)`**：默认返回新对象，原 `radar` 不变；忘记会丢数据。
4. **HCL 必须按频段**：X 波段文件用 `band="X"`；不填会用错频段曲线。
5. **`plot_ppi` 想要中文标签**：先 `plt.rcParams['font.family'] = 'SimHei'` 再画。
6. **剖面图一定要设 `title=`**：内部默认标题可能乱码。
7. **`add_product_CAPPI_xy` 的 `level_height` 单位是米**（不是 km）。
8. **`retrieve_wind_volume_*` 的 `workers` 是进程级**：超过物理核数收益递减，且小网格基本没加速。
9. **三维风体不是真正的 uvw 反演**：是固定高度 gridded u/v，不能替代双多普勒变分。
10. **PA 文件**：`NUIST.20150627.002438.AR2.bz2` 是 X 波段相控阵，`Z_RADR_I_ZT002_..._YLD2-D_...` 是 X 波段双偏振相控阵；`read_auto` 会自动识别并路由到 `read_PA`。

## 13. 推荐工作流

```python
# 1) 读
from pycwr.io import read_auto
radar = read_auto(fp)
print(radar.summary())

# 2) 选产品 + 选仰角
data = radar.get_sweep_field(0, "dBZ")

# 3) QC（可选）
from pycwr.qc import apply_dualpol_qc
qc = apply_dualpol_qc(radar, inplace=False, clear_air_mode="mask", band='S')

# 4) HCL（可选）
hcl = qc.classify_hydrometeors(inplace=False, band="S",
                               profile_height=[0, 2000, 4000, 8000, 12000],
                               profile_temperature=[24, 12, 2, -16, -40])

# 5) 风场反演（可选）
vad = radar.retrieve_vad(sweeps=0)
vvp = radar.retrieve_vvp(0)
vwp = radar.retrieve_vwp(sweeps=[0, 1, 2])

# 6) 画图
from pycwr.draw import plot_ppi, plot_ppi_map, plot_section
plot_ppi_map(radar, field="dBZ", sweep=0, show=True)
plot_section(radar, start=(30, 60), end=(90, 60), field="dBZ",
             title="section", show=True)
```

## 14. 详细参考

- GitHub: https://github.com/YvZheng/pycwr
- 中文说明: https://github.com/YvZheng/pycwr/blob/master/README_CN.md
- API reference: https://github.com/YvZheng/pycwr/blob/master/docs/api_reference.md
- Draw quickstart: https://github.com/YvZheng/pycwr/blob/master/docs/draw_quickstart.md
- Radar network quickstart: https://github.com/YvZheng/pycwr/blob/master/docs/radar_network_quickstart_en.md
- Read the Docs: https://pycwr.readthedocs.io/en/latest/
- 1.0.9 release notes: https://github.com/YvZheng/pycwr/blob/master/docs/releases/1.0.9.md
- 本地讲义与示例：`H:\hn\PyCWR讲课与实习\pycwr实习2026\`
  - `pycwr case 01 read.py` —— 读取 + PPI/Map/VCS
  - `pycwr case 02 qc draw.py` —— 双偏振 QC
  - `pycwr case 03  hcl draw.py` —— 水凝物分类 HCL
  - `pycwr case 03 pro draw.py` —— CAPPI 产品 + 自定义网格画图
  - `pycwr case 04 wind draw.py` —— VAD/VVP/VWP + 风羽 / 箭头画图
  - `data/`：SA (`Z9731`)、SB (`Z9736`)、相控阵 (`NUIST.20150627.002438.AR2` / `ZT002_YLD2-D`)、探空 `.xlsx`、地面站 `.csv`
