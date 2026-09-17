# PyCINRAD 使用指南

> 中国新一代天气雷达（CINRAD/SA/SB/CA/CB、相控阵 AXPT0364/DXK）数据解码、可视化与衍生产品计算。
> 仓库：https://github.com/CyanideCN/PyCINRAD

## 1. 适用场景

当用户的任务涉及以下任一情况时，调用本 skill：

- 解码 CINRAD 基数据（`.bin`/`.bz2`，包含 SA/SB/CA/CB/SC/CC/CD 等雷达型号），返回 `xarray.Dataset`
- 解码 ROSE 2.0 标准的 PUP 产品：`REF/VEL/SW/RHO/ZDR/KDP/CAPPI/CR/HCL/HC/HI/MAX/HSR/WER/STI/UAM/VWP/CAR/OHP/CS/ML` 等
- 解码 SWAN 产品：Mosaic、CR、TREC、ET/VIL/VILD/QPE、雷达拼图等
- 相控阵雷达基数据（AXPT0364 新旧格式、DXK 老格式）
- 计算衍生量：组合反射率 CR、回波顶 ET、垂直累积液态水含量 VIL、水凝物分类 HCL
- 速度退模糊（`cinrad.correct.dealias`）
- 在地图上画 PPI / RHI / VCS，自定义色标、距离圈、城市名、shapefile 边界等

## 2. 安装与导入

```bash
# 安装
pip install numpy cartopy matplotlib cython -U
pip install cinrad -U
# 升级到测试版
pip install cinrad -U -i https://pycinrad.cn/simple/ --trusted-host pycinrad.cn
```

```python
import warnings
import cinrad
import numpy as np
import cartopy
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from cinrad.visualize import PPI
warnings.filterwarnings("ignore")
```

中文字体：

```python
import matplotlib
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False
```

数据通常放在一个根目录下（示例用 `D:/pycinrad/`），所有路径文件名形如：

```
Z_RADR_I_Z9532_20200517124300_O_DOR_SAD_CAP_FMT.bin.bz2
Z_RADR_I_Z9735_20240511082558_O_DOR_SAD_CAP_FMT.bin.bz2
Z_OTHE_RADAMCR_20220525085400.bin.bz2
```

## 3. 模块结构与典型调用

### 3.1 `cinrad.io` —— 数据读取

#### 自动判断格式

```python
import cinrad
f = cinrad.io.read_auto("Z_RADR_I_Z9532_20200517124300_O_DOR_SAD_CAP_FMT.bin.bz2")
print(type(f).__name__)  # StandardData / CinradReader / PhasedArrayData / ...
```

#### 标准格式基数据（SA/SC/SB/CA/CB/CC/CD）

```python
f = cinrad.io.StandardData("Z_RADR_I_Z9532_..._CAP_FMT.bin.bz2")

# 元信息
f.available_product(0)            # 第 0 个仰角有哪些产品（'REF', 'VEL', 'SW', 'ZDR', ...）
f.available_tilt("REF")          # REF 产品在哪些仰角
f.el                             # 所有仰角（弧度）
f.scan_config                    # 扫描配置
f.scantime                       # 扫描时间

# 单仰角单产品 -> xarray.Dataset
data = f.get_data(tilt=0, drange=230, dtype="REF")  # (azimuth, distance, x, y, latitude, longitude)

# 批量遍历所有仰角
r_list = list(f.iter_tilt(150, "REF"))  # 150 km 半径下所有仰角的 REF
```

读取老格式 SB：

```python
f = cinrad.io.CinradReader("Z_RADR_I_Z9636_..._CAP.bz2", radar_type="SB")
f.el
f.available_product(0)
```

#### 修正时间为北京时

```python
import datetime
f.scantime = f.scantime + datetime.timedelta(hours=8)
```

#### 双偏振产品

```python
rho = f.get_data(0, 230, "RHO")   # 相关系数
zdr = f.get_data(0, 230, "ZDR")   # 差分反射率
kdp = f.get_data(0, 230, "KDP")   # 差分相移
sw  = f.get_data(1, 230, "SW")    # 速度谱宽
```

#### 相控阵雷达

```python
# AXPT0364 新格式
f = cinrad.io.read_auto("Z_RADR_I_ZA601_20240415183600_O_DOR_AXPT0364_CRA_FMT.bin.bz2")
data = f.get_data(0, 130, "REF")
r_list = list(f.iter_tilt(130, "REF"))

# AXPT0364 旧格式
f = cinrad.io.read_auto("Z_RADR_I_ZS409_20231220000000_O_DOR_AXPT0364_CRA_.bz2")
data = f.get_data(15, 230, "REF")

# DXK 老格式
f = cinrad.io.read_auto("Z_RADR_I_ZBJ02_20210815155836_O_DOR_DXK_CAR.bin")
```

#### ROSE 2.0 产品

```python
# 自动判断产品类型
f = cinrad.io.read_auto("Z_RADR_I_Z9730_..._CR_250X250_230_NUL_FMT.bin")
data = f.get_data()                 # 直接拿到完整 Dataset

# WER（垂直累积液态水含量）
f = cinrad.io.StandardPUP("Z_RADR_I_Z9731_..._WER_250_50X50_NUL_FMT.bin")
data = f.get_data()
dt = data.rename({"WER_0.5": "REF"})    # 改名后可直接画 PPI

# STI（风暴追踪）
f = cinrad.io.StandardPUP("Z9737_20230424171836Z_STI_00_58")
f.sti_adaptation
f.sti_attributes
f.sti_components

# UAM（用户报警产品）
f = cinrad.io.StandardPUP("Z9737_20231128135254Z_UAM_00_hail")
dt = f.get_data()
```

#### VWP（VAD 风廓线）

```python
f = cinrad.io.read_auto("Z_RADR_I_Z9731_20240126000025_P_DOR_SAD_VWP_NUL_NUL_NUL_FMT.bin")
vwp = f.get_data()
# vwp.wind_speed.values = np.ma.masked_less(vwp.wind_speed.values, 0.0)
# vwp.wind_speed.values = np.round(vwp.wind_speed.values, 2)
```

#### SWAN 产品（探测中心）

```python
# CR / MOSAIC / TREC / ET-VIL-VILD-QPE / MocMosaic 等
f = cinrad.io.SWAN("Z_OTHE_RADAMCR_20220525085400.bin.bz2")
data = f.get_data()                 # xarray.Dataset

f.header["data_name"][0].decode("gbk")
f.data.shape

# 过滤低值
data["CR"].values = np.ma.masked_less_equal(data["CR"].values, 5)

# 选某一高度层
dt = data.sel(height=5.0)
dt = data.sel(height=1500)
fig = PPI(dt, style="black", add_city_names=True)
```

#### 导出为 Py-ART

```python
import pyart
sradar = cinrad.io.export.standard_data_to_pyart(f)   # 接收 StandardData
display = pyart.graph.RadarMapDisplay(sradar)
```

### 3.2 `cinrad.calc` —— 衍生产品

#### 组合反射率 CR

```python
r_list = list(f.iter_tilt(150, "REF"))   # 列表/迭代器均可
cr = cinrad.calc.quick_cr(r_list)

# xarray 选择/插值
cr.sel(latitude=30.0, longitude=120.0, method="nearest")
# cr.interp(latitude=30.0, longitude=120.0)

cr.max()
```

#### 回波顶 ET / VIL / VILD

```python
r_list = list(f.iter_tilt(230, "REF"))
et = cinrad.calc.quick_et(r_list)
```

#### 水凝物分类 HCL（Dolan 算法）

```python
ref = f.get_data(0, 230, "REF")
zdr = f.get_data(0, 230, "ZDR")
rho = f.get_data(0, 230, "RHO")
kdp = f.get_data(0, 230, "KDP")

cHCL = cinrad.calc.hydro_class(ref, zdr, rho, kdp, band="S")  # band: "S" / "C" / "X"
fig = cinrad.visualize.PPI(cHCL, add_city_names=True, dpi=300, style="black")
```

#### 极坐标 → 笛卡尔

```python
vel_xy = cinrad.calc.polar_to_xy(vel0)
```

### 3.3 `cinrad.correct.dealias` —— 速度退模糊

```python
import cinrad
v = f.get_data(1, 230, "VEL")
v_corrected = cinrad.correct.dealias(v)
```

底层走 `pyart` 区域法（需要 C 编译器）。

### 3.4 `cinrad.visualize` —— 绘图

#### PPI（最常用）

```python
from cinrad.visualize import PPI
fig = PPI(data, style="black")   # style: white / black / transparent
fig("d:/abc.png")                # 路径可以是目录或具体 png 文件
```

支持的 `Dataset`：基数据单层 / `quick_cr` 结果 / HCL / WER（改名后）/ SWAN 各产品 / `xr.concat` 后的拼接数据。

主要参数：

| 参数               | 作用                                                |
|--------------------|-----------------------------------------------------|
| `cmap` / `norm`    | 自定义色标                                          |
| `nlabel`           | colorbar 标签数                                     |
| `label`            | colorbar 标签文字                                   |
| `highlight`        | 高亮区域                                            |
| `dpi`              | 图片 dpi                                            |
| `extent`           | 经纬度裁剪，如 `extent=[90, 91, 29, 30]`            |
| `section`          | 同一图上叠加 VCS                                    |
| `style`            | 背景颜色                                            |
| `add_city_names`   | 是否叠加自带城市名                                  |

辅助方法：

```python
fig.plot_range_rings([10, 20, 30, 50, 150], color=None, linewidth=1)   # 距离圈
fig.gridlines(draw_labels=True, linewidth=1, color=None)              # 经纬度网格
fig.plot_ring_rays(angles, 150, color=None, linewidth=1)              # 方位射线
fig.add_custom_shp("d:/data/shp/City.shp")                            # 自定义边界
fig.geoax.scatter(x=..., y=..., s=500, c="red", marker=".",
                  transform=ccrs.PlateCarree())                        # 加点
fig.geoax.text(lon, lat, "中文", transform=ccrs.PlateCarree(), **fig.font_kw)
```

#### VCS 剖面

```python
import cinrad
from cinrad.visualize import Section

rl = [f.get_data(i, 230, "REF") for i in f.angleindex_r]
vcs = cinrad.calc.VCS(rl)
sec = vcs.get_section(start_cart=(111, 25.5), end_cart=(112, 26.7))   # 地理坐标
# sec = vcs.get_section(start_polar=(115, 350), end_polar=(130, 30))  # 极坐标
fig = Section(sec)
fig("D:/")
```

#### 在 PPI 图下方添加剖面

```python
fig.plot_cross_section(sec, ymax=15)   # sec 是 vcs.get_section(...) 的结果
```

#### 自定义色标

```python
from cinrad.visualize.gpf import _cmap
cmap = _cmap("REF")["cmap"]   # REF / VEL / SW / ZDR / RHO / KDP / HCL ...
fig = PPI(data, cmap=cmap, style="black")
```

#### 三维可视化

```python
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from cinrad.visualize.gpf import _cmap

# 假设已有 X, Y, Z, value 数组
fig = plt.figure(figsize=(10, 10), dpi=200)
ax = Axes3D(fig)
fig.add_axes(ax)
cmap = _cmap("REF")["cmap"]
ax.scatter(X, Y, Z, c=value, alpha=0.8, cmap=cmap)
```

### 3.5 雷达拼图（新方法）

```python
from cinrad.calc import GridMapper
mergePath = "D:/pycinrad/cr/"
# 见 example 详细用法：把多部雷达的 .bz2 拼到统一 cartesian 网格
```

## 4. 通用使用模式

### 4.1 数据读取 → 派生量 → 画图

```python
f = cinrad.io.read_auto(fp)
data = f.get_data(0, 230, "REF")                 # 基数据
r_list = list(f.iter_tilt(150, "REF"))           # 多仰角列表
cr = cinrad.calc.quick_cr(r_list)                # 派生量
PPI(cr, style="black")("d:/cr.png")              # 画图保存
```

### 4.2 多产品同仰角批量读取

```python
ref = f.get_data(0, 230, "REF")
vel = f.get_data(1, 230, "VEL")
sw  = f.get_data(1, 230, "SW")
rho = f.get_data(0, 230, "RHO")
zdr = f.get_data(0, 230, "ZDR")
kdp = f.get_data(0, 230, "KDP")
```

### 4.3 拼接 Dataset

```python
import xarray as xr
data0.values = np.where(data0.values < 5, np.nan, data0.values)
combined = xr.concat([data0, data1], dim="time")
```

### 4.4 字符串编码字段解码

SWAN/PUP 文件头常有 GBK 字段：

```python
f.header["data_name"][0].decode("gbk")
```

## 5. 常见陷阱

1. **`read_auto` vs `StandardData` / `CinradReader` / `PhasedArrayData`**：`read_auto` 会按文件头自动选择类；老格式 SB 必须显式 `CinradReader(fp, radar_type="SB")`，否则会读错。
2. **`f.scantime` 是 UTC**：直接画出来是中国时差 8 小时，需要 `f.scantime + datetime.timedelta(hours=8)`。
3. **`f.get_data(...)` 必须给 `drange`（km）**：超过有效距离会全 NaN；组合反射率通常用 150 km。
4. **HCL 必须 4 个产品齐全**：REF/ZDR/RHO/KDP，缺一不可；`band` 显式传 `"S"`/`"C"`/`"X"`，否则频段选错分类结果不对。
5. **`PPI` 不支持 height 维**：SWAN/MocMosaic 等多高度产品必须先 `data.sel(height=...)` 选一层再画。
6. **WER/SWAN 等列名带数字后缀**（如 `WER_0.5`），直接画 PPI 会找不到默认色标，需要 `data.rename({"WER_0.5": "REF"})`。
7. **`dealias` 需要 C 编译器**：Windows 上要装 MSVC 或换用预编译 `pyart`。
8. **STI/UAM 文件名是 `Zxxxx_yyyyMMddhhmmssZ_xxx_NN_xx`**（不是标准 `Z_RADR_I_` 开头），`StandardPUP` 仍可读。
9. **中文标签乱码**：参考第 2 节设置 `font.sans-serif = ['Microsoft YaHei']`。
10. **bz2 文件**：PyCINRAD 内置 `bz2` 解压，直接传 `.bz2` 路径即可，不要预先解压。

## 6. 推荐工作流

```python
import warnings, cinrad, numpy as np, matplotlib.pyplot as plt
from cinrad.visualize import PPI
warnings.filterwarnings("ignore")

# 1) 读取
f = cinrad.io.read_auto(fp)

# 2) 看有哪些产品
print(f.available_product(0))          # ['REF','VEL','SW',...]
print(f.available_tilt("REF"))         # [0.5, 1.5, 2.4, ...]

# 3) 修正时区
import datetime
f.scantime = f.scantime + datetime.timedelta(hours=8)

# 4) 取数 / 派生
data = f.get_data(0, 230, "REF")
r_list = list(f.iter_tilt(150, "REF"))
cr = cinrad.calc.quick_cr(r_list)

# 5) 画图
fig = PPI(cr, style="black", add_city_names=True, dpi=300)
fig("d:/cr.png")
```

## 7. 详细参考

- GitHub: https://github.com/CyanideCN/PyCINRAD
- 中文文档: https://github.com/CyanideCN/PyCINRAD/blob/master/README_zh.md
- 在线文档: https://pycinrad.cn
- 本仓库内讲解示例：`H:\hn\pycinrad\讲课示例.ipynb`
- 示例数据：`H:\hn\pycinrad\`（含 SA/SB/CA、相控阵、PUP、SWAN、shapefile 等）
- 国内安装源：`pip install cinrad -U -i https://pycinrad.cn/simple/ --trusted-host pycinrad.cn`
