# metgrs
The Python Package work for The Ground-based Remote Sensing Data Operation.

The Python Package mainly work for China Ground-based Remote Sensing Data Operation System.

But It will suit for the Europen or USA instruments in future.

# Main features
1. Read microwave radiometer, millimeter wave cloud radar, wind profile radar, lidar data
2. Generate secondary products based on the above products
3. Data visualization

开源代码地址: [metgrs github](https://github.com/longtsing/metgrs)   

文档地址：[metgrs document](https://longtsing.github.io/metgrs/)

pypi发布地址:[metgrs pypi](https://pypi.org/project/metgrs/)

# 安装
可以通过以下命令安装metgrs：
```shell
pip install metgrs
```
# 其他说明

## 环境管理与包安装
其中 mamba == conda 两者接口一致，但 mamba 比 conda 更快，建议使用 mamba 管理环境安装依赖可以从 [https://conda-forge.org/miniforge/](https://conda-forge.org/miniforge/) 下载安装（建议使用 Miniforge）。

## 依赖库
metgrs以高内聚低耦合思想开发，主要在 python3.9 环境下开发，依赖于以下第三方库：
- numpy
- pandas
- xarray
- matplotlib
- joblib
- python-dateutil

可以通过以下命令创建环境并安装依赖：

```shell
mamba create -n metgrs python==3.9 numpy pandas xarray matplotlib joblib python-dateutil -c conda-forge -y
```

## jupyter lab 运行环境安装

```shell
mamba create -n runtime python==3.12 jupyterlab==4.2.6  jupyterlab-lsp python-lsp-server jupyterlab-language-pack-zh-cn nb_conda -c conda-forge -y
```
## 开发环境安装

```shell
mamba create -n devmetgrs python==3.9 numpy xarray pandas geopandas scipy dask metpy matplotlib cartopy cnmaps sympy  nb_conda scikit-learn pytest pytest-cov pytest-xdist flake8 black pre-commit build twine -c conda-forge -y
```
## 特别说明
在国内使用清华源安装metgrs及依赖库时，可能会出现403错误，这是因为清华源的问题，切换到其他源即可。

镜像源汇总 https://help.mirrors.cernet.edu.cn/