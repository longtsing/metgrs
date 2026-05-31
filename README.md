# metgrs

[![PyPI version](https://badge.fury.io/py/metgrs.svg)](https://pypi.org/project/metgrs/)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

**地基遥感垂直观测数据处理 Python 库**

The Python Package for The Ground-based Remote Sensing Data Operation.

本项目主要用于中国地基遥感垂直观测系统数据的读取、处理和可视化，同时也兼容欧洲和美国的同类设备数据。

---

## 主要功能

1. **多设备数据读取**：微波辐射计、毫米波测云仪、风廓线仪、激光雷达
2. **数据处理**：L1→L2→L3 逐级反演（谱矩法、杂波抑制、风分量合成）
3. **数据可视化**：基于 xarray + matplotlib 的专业气象绘图
4. **标准输出**：所有数据以 `xarray.Dataset` 标准对象输出，完全兼容 xarray 生态

## 相关链接

- 开源代码：[metgrs GitHub](https://github.com/longtsing/metgrs)
- 在线文档：[metgrs document](https://longtsing.github.io/metgrs/)
- PyPI 发布：[metgrs PyPI](https://pypi.org/project/metgrs/)

---

## 分支说明

本项目使用以下分支策略进行开发和发布管理：

| 分支 | 用途 | 说明 |
|------|------|------|
| `main` | 主分支 | 稳定发布版本，与 PyPI 发布版本保持同步 |
| `develop` | 开发分支 | 最新开发进度，包含已测试但未发布的功能 |
| `feature/*` | 功能分支 | 特定功能的开发，如 `feature/lidar-l2-product` |
| `bugfix/*` | 修复分支 | Bug 修复，修复完成后合并到 `develop` |
| `release/*` | 发布分支 | 版本发布准备，从 `develop` 分出，测试通过后合并到 `main` |

### 分支工作流

```
main ─────●────────────●────────────●──── 稳定发布
           \          / \          /
develop ────●────●────●───●────●───●──── 开发主线
             \  /          \  /
feature ──────●──────────────●────────── 功能开发
```

### 如何选择分支

- **普通用户**：使用 `main` 分支或直接 `pip install metgrs`
- **开发者**：基于 `develop` 分支进行开发
- **测试新功能**：切换到对应的 `feature/*` 分支

---

## 快速开始

### 安装

```shell
pip install metgrs
```

### 基本使用

```python
import metgrs

# 读取风廓线雷达 L3 数据
ds = metgrs.WindProfileRadar.readSingleL3file('path/to/OBS.TXT')
print(ds)

# 读取云雷达基数据并绘图
ds = metgrs.CloudRadar.readSingleBaseData('path/to/RAW.BIN')
ds.cld.plot(data_name='Z1', savepath='reflectivity.png')

# 风廓线雷达 L1→L2→L3 完整处理流程
ds_l1 = metgrs.WindProfileRadar.readSingleL1file('path/to/FFT.BIN')
ds_l2 = ds_l1.wpr.calc_l1_to_l2(clutter_filter=True)
ds_l3 = ds_l2.wpr.calc_l2_to_l3(qcw=3, rollmean=True)
ds_l3.wpr.plot_l3_wind(savepath='wind_profile.png')
```

---

## 支持的设备与数据格式

| 设备 | 数据类型 | 文件格式 | 读取函数 |
|------|----------|----------|----------|
| **风廓线仪** | L1 功率谱 | FFT.BIN | `readSingleL1file()` |
| | L2 径向数据 | RAD.TXT | `readSingleL2file()` |
| | L3 产品数据 | OBS.TXT | `readSingleL3file()` |
| | 实时产品 | ROBS.TXT | `readSingleROBSfile()` |
| | 半小时平均 | HOBS.TXT | `readSingleHOBSfile()` |
| | 一小时平均 | OOBS.TXT | `readSingleOOBSfile()` |
| **云雷达** | FFT 谱数据 | FFT_M.BIN | `readSingleFFTData()` |
| | 基数据 | RAW_M.BIN | `readSingleBaseData()` |
| | 产品数据 | CP_M.TXT | `readSingleProductFile()` |
| **激光雷达** | L0 原始数据 | L0.BIN | `readSingleL0File()` |
| | L1 产品 | L1_*.BIN | `readSingleL1ProductFile()` |
| | L2 产品 | L2_*.TXT | `readSingleL2ProductFile()` |
| | CDWL 数据 | CDWL.BIN | `readSingleCDWLBinFile()` |
| **微波辐射计** | 观测数据 | CSV | `readMWRFileAsDataset()` |

---

## 环境管理与安装

### 使用 pip 安装（最简单）

```shell
pip install metgrs
```

### 使用 conda/mamba 创建环境（推荐）

mamba 与 conda 接口一致，但速度更快。建议从 [Miniforge](https://conda-forge.org/miniforge/) 下载安装。

```shell
# 创建运行环境
mamba create -n metgrs python==3.9 numpy pandas xarray matplotlib joblib python-dateutil -c conda-forge -y

# 激活环境并安装 metgrs
mamba activate metgrs
pip install metgrs
```

### 使用 uv 安装（极速）

```shell
# 安装 uv
pip install uv

# 创建环境并安装
uv venv metgrs-env
source metgrs-env/bin/activate  # Linux/macOS
# metgrs-env\Scripts\activate   # Windows
uv pip install metgrs
```

> 详细的环境管理教程请参考 [docs/python_env_management.md](docs/python_env_management.md)

---

## 依赖库

metgrs 以高内聚低耦合思想开发，依赖以下第三方库：

| 库 | 用途 |
|---|------|
| numpy | 数值计算 |
| pandas | 数据处理 |
| xarray | 多维数据集 |
| matplotlib | 数据可视化 |
| joblib | 多进程并行 |
| python-dateutil | 日期解析 |

### Jupyter Lab 运行环境

```shell
mamba create -n runtime python==3.12.9 jupyterlab jupyterlab-lsp python-lsp-server jupyterlab-language-pack-zh-cn jupyterlab-git nb_conda jupyter-ai -c conda-forge -y
```

### 开发环境

```shell
mamba create -n devmetgrs python==3.9 numpy xarray pandas geopandas scipy dask metpy matplotlib cartopy cnmaps sympy nb_conda scikit-learn pytest pytest-cov seaborn pytest-xdist flake8 black pre-commit build twine -c conda-forge -y
```

---

## 项目结构

```
metgrs/
├── metgrs/
│   ├── __init__.py              # 包入口
│   ├── __version__.py           # 版本号
│   ├── base.py                  # 基础工具函数
│   ├── Utils.py                 # 通用工具函数
│   ├── WindProfileRadar.py      # 风廓线雷达数据处理
│   ├── CloudRadar.py            # 云雷达数据处理
│   ├── Lidar.py                 # 激光雷达数据处理
│   └── MicroWaveRadiometer.py   # 微波辐射计数据处理
├── examples/                    # 示例代码
├── docs/                        # 文档
├── tests/                       # 测试
├── README.md
└── pyproject.toml
```

---

## Accessor API

所有数据读取函数返回标准 `xr.Dataset` 对象，通过 xarray accessor 提供领域方法：

| Accessor | 方法 | 说明 |
|----------|------|------|
| `ds.wpr` | `calc_l1_to_l2()` | L1 功率谱 → L2 径向数据 |
| | `calc_l2_to_l3()` | L2 径向数据 → L3 产品数据 |
| | `plot_l3_wind()` | 绘制 L3 风场 |
| `ds.cld` | `plot(data_name)` | 绘制云雷达数据 |
| `ds.lidar` | `channel_metas` | 获取通道元数据 |

---

## 特别说明

在国内使用清华源安装 metgrs 及依赖库时，可能会出现 403 错误，这是因为清华源的问题，切换到其他源即可。

镜像源汇总：https://help.mirrors.cernet.edu.cn/

---

## 许可证

MIT License

## 引用

如果你在研究中使用了 metgrs，请引用：

```bibtex
@software{metgrs,
  title={metgrs: Ground-based Remote Sensing Data Operation},
  author={longtsing},
  year={2024},
  url={https://github.com/longtsing/metgrs}
}
```
