# python-radar-basics 使用指南

> 雷达数据处理的三件套基础：NumPy（雷达回波数组）、Pandas（站点/降水表）、Xarray（带坐标的雷达 Dataset）。
> 本 skill 对应 9 月 14 日下午《Python 基础知识：Xarray, Numpy, Pandas》实习。

## 1. 适用场景

当用户的任务涉及以下任一情况时，调用本 skill：

- 把雷达 PPI 数据读成二维数组、做切片/掩膜/广播运算
- 读取雷达站点表、站点降水 CSV，做筛选、分组、合并
- 把雷达产品封装成 `xarray.Dataset`，利用坐标做切片、重采样、对齐
- 在进入 Py-ART / PyCINRAD / PyCWR 之前，需要先把"数组—表格—Dataset"三种数据形态打通
- 学生报错出在维度不对齐、广播规则、DataFrame 列名乱码、`sel/isel/loc` 混用等基础问题

## 2. 安装与导入

```bash
pip install numpy pandas xarray matplotlib
```

```python
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
```

## 3. NumPy：雷达回波数组

### 3.1 雷达回波的本质

一帧 PPI 就是一个 `(方位角, 距离库)` 的二维浮点数组，常见值 `np.nan` 表示无回波：

```python
data = np.load("data/ppi_sample.npy")      # shape: (360, 400) 方位 × 距离
print(data.shape, data.dtype)
```

### 3.2 高频操作

```python
# 1) 切片：取第 0~60 个方位、0~100 km
sub = data[0:60, 0:100]

# 2) 掩膜：只看 >= 30 dBZ 的回波
masked = np.ma.masked_less(data, 30)

# 3) 阈值处理（雷达 QC 常见）
dbz = np.where(data < 5, np.nan, data)

# 4) 广播：(360,1) 的方位列向量 与 (400,) 的距离向量 运算
az = np.linspace(0, 360, 360, endpoint=False).reshape(-1, 1)
r  = np.linspace(0, 230, 400)
x  = r * np.sin(np.deg2rad(az))           # 自动广播成 (360, 400)

# 5) 统计
np.nanmax(dbz), np.nanmean(dbz), np.nanpercentile(dbz, 95)
```

### 3.3 常见陷阱

1. **`np.nan` 与 `np.ma` 不要混用**：`np.nanmax` 只跳过 `nan`；`np.ma.masked_*` 走掩码；matplotlib 对两者都安全。
2. **广播维度从右往左对齐**：`(360,400)` 与 `(400,)` 可广播；与 `(360,)` 不能，要 `reshape(-1,1)`。
3. **布尔索引返回拷贝**：`dbz[dbz<5] = np.nan` 是原地改；`dbz2 = dbz[dbz<5]` 是拷贝。
4. **`.npy` 是原始数组**：没有坐标、没有单位，必须自己知道 shape 含义。

## 4. Pandas：站点与降水表

### 4.1 读取

```python
st = pd.read_csv("data/radar_stations.csv")      # 站号/经度/纬度/海拔
pr = pd.read_csv("data/station_precip.csv")      # 站号/时间/雨量
print(st.head(), st.dtypes)
```

### 4.2 高频操作

```python
# 1) 按条件筛选：湖南境内 S 波段雷达
hn = st[(st["经度"] > 108) & (st["经度"] < 115) &
        (st["纬度"] > 24)  & (st["纬度"] < 30)]

# 2) 时间列解析 + 按日聚合
pr["time"] = pd.to_datetime(pr["time"])
daily = pr.groupby(["站号", pr["time"].dt.date])["rain"].sum()

# 3) 合并：站点属性并入降水记录
m = pr.merge(st, on="站号", how="left")

# 4) 写回
m.to_csv("merged.csv", index=False, encoding="utf-8-sig")
```

### 4.3 常见陷阱

1. **中文列名与编码**：`read_csv` 读中文 CSV 用 `encoding="utf-8-sig"` 或 `gbk`；写出给 Excel 用 `utf-8-sig`。
2. **`loc` vs `iloc` vs `[]`**：`df[mask]` 按行筛；`df.loc[row, col]` 按标签；`df.iloc[i, j]` 按位置。
3. **`groupby` 后保留原列**：`groupby(...).agg(...)` 后想带其它列要先 `transform` 或 `merge`。
4. **时间字符串解析**：不要用字符串切时间，统一 `pd.to_datetime`。

## 5. Xarray：带坐标的雷达 Dataset

### 5.1 为什么用 Xarray

雷达数据的痛点是"维度多、坐标语义化"：方位角、距离、仰角、时间、经纬度。Xarray 用名字索引，不用死记 shape。

### 5.2 构造一个雷达 Dataset

```python
az = np.linspace(0, 360, 360, endpoint=False)
r  = np.linspace(0, 230, 400)
dbz = np.random.RandomState(0).normal(5, 15, (360, 400))

ds = xr.Dataset(
    data_vars={"reflectivity": (("azimuth", "range"), dbz)},
    coords={"azimuth": az, "range": r},
    attrs={"site": "Z9731", "elevation": 0.5, "units": "dBZ"},
)
print(ds)
```

### 5.3 高频操作

```python
# 1) 按坐标值切片（不是按位置）
sub = ds.sel(azimuth=slice(0, 90), range=slice(0, 100))

# 2) 按位置切片
sub2 = ds.isel(azimuth=slice(0, 60), range=slice(0, 100))

# 3) 算术运算保留坐标
ds["dbz_masked"] = ds["reflectivity"].where(ds["reflectivity"] >= 5)

# 4) 跨文件按时间拼接
ds_list = [xr.open_dataset(f) for f in sorted(files)]
ds_all  = xr.concat(ds_list, dim="time")

# 5) 快速画图
ds["reflectivity"].plot(x="range", y="azimuth", cmap="jet", vmin=-10, vmax=70)
```

### 5.4 常见陷阱

1. **`sel` 用标签、`isel` 用位置**：混淆是新手最常见报错。
2. **坐标必须单调递增**：`sel(slice(...))` 要求坐标排序；方位角 0~360 跨过 360 度时要先 `roll`。
3. **`where(cond, drop=False)` 默认保留 NaN**：想删行加 `drop=True`。
4. **`attrs` 不参与运算**：单位、站点名放 `attrs`，不要塞进 `coords`。
5. **雷达库返回的就是 Dataset**：PyCINRAD `get_data()`、metgrs 读取函数、PyCWR `PRD.product` 都是 Xarray，先 `print(ds)` 看坐标名再操作。

## 6. 推荐工作流

```python
# 1) 读
import numpy as np, pandas as pd, xarray as xr
arr = np.load("ppi_sample.npy")
st  = pd.read_csv("radar_stations.csv")

# 2) 构造 / 切片 / 掩膜
ds = xr.Dataset({"dbz": (("az","r"), arr)},
                coords={"az": np.linspace(0,360,360,endpoint=False),
                        "r": np.linspace(0,230,400)})
hi = ds["dbz"].where(ds["dbz"] >= 30)

# 3) 画
hi.plot(x="r", y="az", cmap="jet", vmin=30, vmax=70)
```

## 7. 与后续课程库的衔接

| 库            | 返回类型              | 本 skill 的作用               |
|---------------|----------------------|------------------------------|
| Py-ART        | `pyart.core.Radar`   | 理解 `fields` 里的二维数组     |
| PyCINRAD      | `xarray.Dataset`      | 直接用 `sel/where/plot`       |
| PyCWR         | `PRD` 包装 xarray     | `get_sweep_field` 返回值可继续用 |
| metgrs        | `xarray.Dataset`      | `.wpr/.cld/.lidar` accessor   |

## 8. 详细参考

- 本地讲义：`H:\hn\radar_202609\`
  - `01_NumPy入门_雷达回波数组.ipynb`
  - `02_Pandas入门_雷达站点与降水数据.ipynb`
  - `03_Xarray入门_雷达数据读写与索引.ipynb`
- 官方文档：NumPy / Pandas / Xarray 各自 docs.xarray.org
