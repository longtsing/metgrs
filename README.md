# metgrs
The Python Package work for The Ground-based Remote Sensing Data Operation.

The Python Package mainly work for China Ground-based Remote Sensing Data Operation System.

But It will suit for the Europen or USA instruments in future.

# Main features
1. Read microwave radiometer, millimeter wave cloud radar, wind profile radar, lidar data
2. Generate secondary products based on the above products
3. Data visualization

office website: [metgrs](https://github.com/longtsing/metgrs)   

# 依赖与安装
metgrs以高内聚低耦合思想开发，主要在 python3.9 环境下开发，依赖于以下第三方库：
- numpy
- pandas
- xarray
- matplotlib
- joblib
- python-dateutil
可以通过以下命令创建环境并安装依赖：
```shell
conda create -n metgrs python=3.9 numpy pandas xarray matplotlib joblib python-dateutil -c conda-forge -y
```
可以通过以下命令安装metgrs：
```shell
pip install metgrs
```

