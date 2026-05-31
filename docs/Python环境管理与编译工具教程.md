# Python 环境管理与编译工具教程

## 目录

1. [为什么需要环境管理？](#1-为什么需要环境管理)
2. [pip —— Python 官方包管理器](#2-pip--python-官方包管理器)
3. [venv —— Python 内置虚拟环境](#3-venv--python-内置虚拟环境)
4. [uv —— 新一代极速包管理器](#4-uv--新一代极速包管理器)
5. [conda / mamba —— 科学计算生态的包管理器](#5-conda--mamba--科学计算生态的包管理器)
   - [5.10 conda 环境管理最佳实践](#510-conda-环境管理最佳实践)
   - [5.11 conda 与 pip 混用策略](#511-conda-与-pip-混用策略)
   - [5.12 conda 环境故障排除](#512-conda-环境故障排除)
6. [国内镜像源配置](#6-国内镜像源配置)
   - [6.2 高校联合镜像源（推荐）](#62-高校联合镜像源推荐)
7. [编译工具基础知识](#7-编译工具基础知识)
8. [各平台编译工具安装指南](#8-各平台编译工具安装指南)
9. [Python 包的编译与安装](#9-python-包的编译与安装)
10. [工具选择建议](#10-工具选择建议)
11. [常见问题](#11-常见问题)
12. [参考资源](#12-参考资源)

---

## 1. 为什么需要环境管理？

### 1.1 问题背景

在 Python 开发中，你经常会遇到以下问题：

- **项目 A** 需要 `numpy==1.24`，而**项目 B** 需要 `numpy==1.26`
- 安装某个包时，它自动升级了另一个包，导致项目代码崩溃
- 不同项目依赖不同版本的 Python 解释器
- 某些包含 C/C++ 扩展的包在安装时需要编译环境

### 1.2 环境隔离的核心思想

**虚拟环境**的核心思想是：为每个项目创建一个独立的 Python 运行环境，互不干扰。

```
全局 Python
├── 项目 A 的虚拟环境  →  numpy 1.24, pandas 1.5
├── 项目 B 的虚拟环境  →  numpy 1.26, pandas 2.0
└── 项目 C 的虚拟环境  →  numpy 1.26, pandas 2.1
```

### 1.3 环境管理工具概览

| 工具 | 类型 | 虚拟环境 | 包管理 | 编译需求 |
|------|------|----------|--------|----------|
| **pip** | 包管理器 | ❌ 需配合 venv | ✅ | ⚠️ 可能需要 |
| **venv** | 虚拟环境 | ✅ | ❌ 需配合 pip | - |
| **uv** | 包管理 + 环境管理 | ✅ 内置 | ✅ | ⚠️ 可能需要 |
| **conda** | 包管理 + 环境管理 | ✅ 内置 | ✅ | ❌ 不需要 |
| **mamba** | conda 的替代品 | ✅ 内置 | ✅ | ❌ 不需要 |
| **poetry** | 包管理 + 环境管理 | ✅ 内置 | ✅ | ⚠️ 可能需要 |
| **pdm** | 包管理 + 环境管理 | ✅ 内置 | ✅ | ⚠️ 可能需要 |

---

## 2. pip —— Python 官方包管理器

### 2.1 原理

pip 是 Python 官方推荐的包管理工具，从 **PyPI**（Python Package Index）下载和安装包。

```
pip install numpy
    │
    ├─ 1. 查询 PyPI：numpy 有哪些版本？
    ├─ 2. 检查本地：是否已有缓存的 wheel？
    ├─ 3. 优先下载 wheel（预编译包）→ 直接安装
    └─ 4. 如果没有 wheel → 下载源码 → 编译 → 安装
```

### 2.2 包的两种分发形式

| 类型 | 格式 | 安装过程 | 说明 |
|------|------|----------|------|
| **Wheel** | `.whl` | 直接解压安装 | 无需编译，速度快 |
| **Source Distribution** | `.tar.gz` | 下载源码 → 编译 → 安装 | 需要编译器，可能失败 |

#### Wheel 文件命名规则

```
numpy-1.24.0-cp39-cp39-win_amd64.whl
│       │      │    │    │
│       │      │    │    └── 平台：win_amd64, linux_x86_64, macosx_10_9_x86_64, any
│       │      │    └── ABI 标签：cp39, abi3, none
│       │      └── Python 版本：cp39 = CPython 3.9
│       └── 包版本号
└── 包名
```

### 2.3 基本使用

```bash
# 安装包
pip install numpy

# 安装指定版本
pip install numpy==1.24.0

# 安装最低版本
pip install numpy>=1.24.0

# 升级包
pip install --upgrade numpy

# 卸载包
pip uninstall numpy

# 查看已安装的包
pip list

# 查看包详细信息
pip show numpy

# 导出依赖
pip freeze > requirements.txt

# 从文件安装依赖
pip install -r requirements.txt

# 只安装预编译 wheel（不从源码编译）
pip install --only-binary :all: numpy

# 强制从源码编译安装
pip install --no-binary :all: numpy

# 使用国内镜像源（加速下载）
pip install numpy -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2.4 pip 的局限

- ❌ 只能安装 Python 包，无法管理系统级依赖（如 HDF5、NetCDF C 库）
- ❌ 没有内置的环境隔离功能（需要 `venv` 模块配合）
- ❌ 依赖解析较慢
- ❌ 某些包需要本地编译（需要安装编译器）
- ❌ 无法管理 Python 解释器版本

---

## 3. venv —— Python 内置虚拟环境

### 3.1 原理

`venv` 是 Python 3.3+ 内置的虚拟环境模块，用于创建轻量级的隔离环境。

```
venv 的工作原理：
├── 创建独立目录（如 myenv/）
├── 复制/链接 Python 解释器到 myenv/bin/python
├── 创建独立的 site-packages/ 目录
├── 设置环境变量，使 pip 安装到该目录
└── 激活时修改 PATH，优先使用虚拟环境中的命令
```

### 3.2 基本使用

#### 创建虚拟环境

```bash
# 创建名为 myenv 的虚拟环境
python -m venv myenv

# 指定 Python 版本（如果系统有多个 Python）
python3.11 -m venv myenv
```

#### 激活虚拟环境

```bash
# Windows (CMD)
myenv\Scripts\activate.bat

# Windows (PowerShell)
myenv\Scripts\Activate.ps1

# Linux / macOS
source myenv/bin/activate
```

激活后，命令行提示符会显示环境名称：

```bash
(myenv) $ python --version
Python 3.11.5

(myenv) $ which python
/path/to/myenv/bin/python
```

#### 在虚拟环境中安装包

```bash
# 激活环境后，pip 会自动安装到虚拟环境中
(myenv) $ pip install numpy pandas matplotlib

# 查看已安装的包（只显示虚拟环境中的包）
(myenv) $ pip list

# 导出依赖
(myenv) $ pip freeze > requirements.txt
```

#### 退出虚拟环境

```bash
(myenv) $ deactivate
$ 
```

#### 删除虚拟环境

```bash
# 直接删除目录即可
rm -rf myenv            # Linux/macOS
rmdir /s /q myenv       # Windows
```

### 3.3 虚拟环境目录结构

```
myenv/
├── bin/                    # Linux/macOS 可执行文件
│   ├── python              # Python 解释器（符号链接）
│   ├── pip                 # pip 命令
│   └── activate            # 激活脚本
├── Scripts/                # Windows 可执行文件
│   ├── python.exe
│   ├── pip.exe
│   └── activate.bat
├── lib/                    # 库文件
│   └── python3.11/
│       └── site-packages/  # 安装的包
├── include/                # C 头文件
├── pyvenv.cfg              # 虚拟环境配置
└── .gitignore
```

### 3.4 venv + pip 完整工作流

```bash
# 1. 创建项目目录
mkdir myproject && cd myproject

# 2. 创建虚拟环境
python -m venv .venv

# 3. 激活环境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 4. 安装依赖
pip install numpy pandas matplotlib

# 5. 导出依赖
pip freeze > requirements.txt

# 6. 开发代码...
python my_script.py

# 7. 退出环境
deactivate

# 8. 以后重新激活
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 9. 在新机器上重建环境
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3.5 venv 的优缺点

**优点：**
- ✅ Python 内置，无需额外安装
- ✅ 轻量级，创建速度快
- ✅ 简单易用
- ✅ 广泛支持

**缺点：**
- ❌ 只能创建与系统 Python 版本相同的环境
- ❌ 无法管理 Python 解释器版本
- ❌ 无法管理系统级 C 库依赖
- ❌ 需要配合 pip 使用

### 3.6 其他虚拟环境工具

除了 `venv`，还有一些其他虚拟环境工具：

| 工具 | 特点 | 安装 |
|------|------|------|
| **virtualenv** | venv 的前身，支持 Python 2 | `pip install virtualenv` |
| **pipenv** | 结合 pip + virtualenv | `pip install pipenv` |
| **poetry** | 依赖管理 + 打包发布 | `pip install poetry` |
| **pdm** | PEP 582 支持，无需激活 | `pip install pdm` |
| **hatch** | 现代化项目管理 | `pip install hatch` |

---

## 4. uv —— 新一代极速包管理器

### 4.1 原理

uv 是用 **Rust** 编写的 Python 包管理器，目标是成为 pip 的高性能替代品。

```
uv pip install numpy
    │
    ├─ 1. Rust 并行查询 PyPI
    ├─ 2. 并行下载 wheel
    ├─ 3. 极速安装（利用 Rust 的高效 I/O）
    └─ 4. 智能缓存（避免重复下载）
```

### 4.2 特点

- ⚡ **极快**：比 pip 快 10-100 倍
- 🔒 **兼容 pip**：完全兼容 pip 的命令和 requirements.txt
- 🧩 **内置虚拟环境管理**：无需单独使用 venv
- 📦 **智能缓存**：全局缓存，避免重复下载
- 🔧 **Rust 实现**：高效的依赖解析

### 4.3 安装

```bash
# 使用 pip 安装
pip install uv

# 使用 conda 安装
mamba install -c conda-forge uv

# 使用官方安装脚本（Linux/macOS）
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 4.4 基本使用

```bash
# 创建虚拟环境
uv venv

# 激活环境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 安装包
uv pip install numpy

# 从文件安装
uv pip install -r requirements.txt

# 安装到指定环境
uv pip install numpy --python .venv/bin/python

# 查看已安装的包
uv pip list

# 导出依赖
uv pip freeze > requirements.txt
```

### 4.5 uv 的独特功能

```bash
# 直接运行 Python 脚本（自动管理依赖）
uv run script.py

# 在脚本头部声明依赖
# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pandas"]
# ///

# 安装指定版本的 Python
uv python install 3.11

# 创建项目
uv init myproject

# 添加依赖
uv add numpy pandas

# 同步依赖
uv sync
```

### 4.6 uv vs pip 对比

| 特性 | pip | uv |
|------|-----|-----|
| 语言实现 | Python | Rust |
| 安装速度 | 中等 | 极快 |
| 依赖解析 | 较慢 | 极快 |
| 缓存机制 | 基础 | 智能全局缓存 |
| 虚拟环境 | 需要 venv | 内置 |
| Python 管理 | ❌ | ✅ |
| 兼容性 | - | 完全兼容 pip |

---

## 5. conda / mamba —— 科学计算生态的包管理器

### 5.1 原理

conda 是专为科学计算设计的**跨平台包管理系统**，不仅管理 Python 包，还管理系统级依赖。

```
conda install numpy
    │
    ├─ 1. 查询 conda 仓库（conda-forge）
    ├─ 2. 依赖解析：分析所有依赖关系（包括 C 库）
    ├─ 3. 下载预编译的二进制包
    └─ 4. 直接安装（无需编译）
```

**关键区别**：conda 仓库中的所有包都是**预编译的二进制包**，安装时**永远不需要编译器**。

### 5.2 pip vs conda 核心区别

| 特性 | pip | conda |
|------|-----|-------|
| 包来源 | PyPI | conda-forge / Anaconda |
| 包格式 | wheel / sdist | 预编译二进制 |
| 是否需要编译器 | ⚠️ 可能需要 | ❌ 永远不需要 |
| 管理系统库 | ❌ | ✅（HDF5、NetCDF、CUDA 等）|
| 管理其他语言 | ❌ | ✅（R、Julia、Node.js 等）|
| 环境隔离 | 需要 venv 配合 | 内置 |
| 依赖解析 | 较慢 | 较慢（mamba 快）|
| 包数量 | ~500,000+ | ~20,000+（conda-forge）|
| 跨平台一致性 | ⚠️ 可能不一致 | ✅ 高度一致 |

### 5.3 mamba 是什么？

mamba 是 conda 的 C++ 重写版本，**完全兼容 conda**，但速度更快：

- 并行下载和依赖解析
- 内存占用更少
- 依赖解析速度快 10-100 倍

**建议**：使用 mamba 替代 conda，命令完全相同。

### 5.4 安装 Miniforge

Miniforge 是一个轻量级的 conda 发行版，推荐使用：

```bash
# 下载地址
# https://conda-forge.org/miniforge/

# Windows：下载 Miniforge3-Windows-x86_64.exe 并运行
# Linux/macOS：
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh
```

### 5.5 环境管理命令

#### 创建环境

```bash
# 创建基本环境
mamba create -n myenv

# 创建指定 Python 版本的环境
mamba create -n myenv python=3.11

# 创建环境并同时安装包
mamba create -n myenv python=3.11 numpy pandas matplotlib

# 从配置文件创建环境
mamba env create -f environment.yml

# 克隆已有环境
mamba create -n new_env --clone old_env
```

#### 激活与退出环境

```bash
# 激活环境
mamba activate myenv

# 退出当前环境
mamba deactivate

# 激活 base 环境（默认环境）
mamba activate base
```

#### 查看环境

```bash
# 列出所有环境
mamba env list
# 或
mamba info --envs

# 查看当前环境信息
mamba info

# 查看当前环境中的包
mamba list

# 查看指定环境中的包
mamba list -n myenv

# 搜索包
mamba search numpy

# 查看包详细信息
mamba info numpy
```

#### 删除环境

```bash
# 删除环境
mamba env remove -n myenv

# 或使用交互式确认
mamba env remove -n myenv --yes
```

#### 导入导出环境

```bash
# 导出当前环境（完整）
mamba env export > environment.yml

# 导出当前环境（仅手动安装的包）
mamba env export --from-history > environment.yml

# 导出当前环境（包含 pip 安装的包）
mamba env export --no-builds > environment.yml

# 从文件创建环境
mamba env create -f environment.yml

# 更新已有环境
mamba env update -f environment.yml
```

### 5.6 包管理命令

#### 安装包

```bash
# 安装单个包
mamba install numpy

# 安装多个包
mamba install numpy pandas matplotlib

# 安装指定版本
mamba install numpy=1.24
mamba install "numpy>=1.24,<1.26"

# 从指定频道安装
mamba install -c conda-forge cartopy

# 安装到指定环境
mamba install -n myenv numpy

# 强制重新安装
mamba install numpy --force-reinstall

# 只下载不安装
mamba install numpy --dry-run
```

#### 更新包

```bash
# 更新单个包
mamba update numpy

# 更新所有包
mamba update --all

# 更新到指定版本
mamba update numpy=1.26

# 更新 conda/mamba 本身
mamba update conda
mamba update mamba
```

#### 卸载包

```bash
# 卸载包
mamba remove numpy

# 卸载多个包
mamba remove numpy pandas

# 卸载并移除依赖
mamba remove numpy --force-remove

# 卸载指定环境中的包
mamba remove -n myenv numpy
```

#### 清理缓存

```bash
# 清理所有缓存
mamba clean --all

# 只清理包缓存
mamba clean --packages

# 清理索引缓存
mamba clean --index-cache

# 查看缓存大小
mamba clean --dry-run
```

### 5.7 频道管理

```bash
# 添加频道
mamba config --add channels conda-forge
mamba config --add channels defaults

# 设置频道优先级（strict 表示严格按顺序）
mamba config --set channel_priority strict

# 查看当前配置
mamba config --show channels

# 移除频道
mamba config --remove channels conda-forge

# 显示频道 URL
mamba config --set show_channel_urls yes
```

### 5.8 conda 的独有能力

conda 不仅是 Python 包管理器，更是**通用的跨平台包管理系统**：

```bash
# 安装编译器工具链（无需 MSVC）
mamba install -c conda-forge m2w64-toolchain

# 安装 Fortran 编译器
mamba install -c conda-forge gfortran

# 安装 CMake
mamba install -c conda-forge cmake

# 安装 FFmpeg（视频处理）
mamba install -c conda-forge ffmpeg

# 安装 CUDA Toolkit
mamba install -c conda-forge cudatoolkit

# 安装 HDF5 库
mamba install -c conda-forge hdf5

# 安装 NetCDF 库
mamba install -c conda-forge netcdf4
```

### 5.9 环境配置文件

`environment.yml` 示例：

```yaml
name: metgrs
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - numpy
  - pandas
  - xarray
  - matplotlib
  - joblib
  - python-dateutil
  - pip:
    - metgrs
```

### 5.10 conda 环境管理最佳实践

#### 环境命名规范

```bash
# 项目环境：使用项目名作为环境名
mamba create -n metgrs python=3.11

# 版本隔离：为不同 Python 版本创建独立环境
mamba create -n py310 python=3.10
mamba create -n py311 python=3.11

# 通用环境：用于快速测试
mamba create -n test python=3.11
```

#### 环境激活与自动切换

```bash
# 每次打开终端自动激活 base 环境
mamba config --set auto_activate_base true

# 禁止自动激活 base 环境（推荐）
mamba config --set auto_activate_base false

# 手动激活指定环境
mamba activate myenv
```

#### 环境复制与迁移

```bash
# 克隆已有环境
mamba create -n new_env --clone old_env

# 导出环境到文件
mamba env export > environment.yml

# 从文件创建环境（跨平台）
mamba env create -f environment.yml

# 更新已有环境
mamba env update -f environment.yml --prune
```

#### 环境清理与维护

```bash
# 查看所有环境
mamba env list

# 删除不用的环境
mamba env remove -n old_env

# 清理环境缓存
mamba clean --all

# 更新 conda/mamba 本身
mamba update conda mamba
```

#### 多环境工作流

```bash
# 1. 创建项目环境
mamba create -n myproject python=3.11

# 2. 激活环境
mamba activate myproject

# 3. 安装项目依赖
mamba install numpy pandas matplotlib

# 4. 导出环境配置
mamba env export > environment.yml

# 5. 开发代码...
python my_script.py

# 6. 退出环境
mamba deactivate

# 7. 在新机器上重建环境
mamba env create -f environment.yml
mamba activate myproject
```

### 5.11 conda 与 pip 混用策略

在实际开发中，conda 和 pip 经常需要配合使用：

```bash
# 推荐顺序：先 conda，后 pip

# 1. 用 conda 安装系统级依赖
mamba install -c conda-forge hdf5 netcdf4

# 2. 用 pip 安装 conda 没有的 Python 包
pip install my-custom-package

# 注意事项：
# - 避免用 pip 安装 conda 已有的包
# - 导出环境时分别导出
mamba env export > conda_env.yml
pip freeze > pip_requirements.txt
```

### 5.12 conda 环境故障排除

#### 环境损坏修复

```bash
# 清理环境缓存
mamba clean --all

# 重新安装环境
mamba env remove -n myenv
mamba env create -f environment.yml

# 强制更新环境
mamba update --all --force-reinstall
```

#### 依赖冲突解决

```bash
# 查看环境依赖树
mamba info --deps

# 尝试解决冲突
mamba install numpy --dry-run

# 使用 strict channel priority
mamba config --set channel_priority strict
```

#### 环境导出问题

```bash
# 导出时排除特定包
mamba env export | grep -v "prefix:" > environment.yml

# 导出时只包含手动安装的包
mamba env export --from-history > environment.yml
```

---

## 6. 国内镜像源配置

### 6.1 为什么需要配置国内镜像源？

由于网络原因，直接从 PyPI 或 conda 官方源下载包速度较慢。配置国内镜像源可以大幅提升下载速度。

### 6.2 高校联合镜像源（推荐）

中国教育和科研计算机网（CERNET）联合多所高校推出了**高校联合镜像源**，是国内最权威、最稳定的镜像源之一。

#### 高校联合镜像源推广背景

近年来，为提升国内学术科研网络资源获取效率，教育部科技发展中心联合中国教育和科研计算机网（CERNET）推动建设了**高校联合镜像源**平台。该平台整合了全国多所重点高校的镜像资源，旨在：

- **提升科研效率**：加速科研软件和数据的下载
- **降低网络成本**：减少国际带宽使用
- **保障数据安全**：提供可信的软件源
- **促进教育公平**：让所有高校都能享受高速镜像服务

#### 主要高校镜像源

| 高校 | 地址 | 说明 |
|------|------|------|
| 清华大学 | `https://mirrors.tuna.tsinghua.edu.cn/` | 最常用，更新快 |
| 中国科学技术大学 | `https://mirrors.ustc.edu.cn/` | 稳定可靠 |
| 北京大学 | `https://mirrors.pku.edu.cn/` | 教育网内速度快 |
| 浙江大学 | `https://mirrors.zju.edu.cn/` | 华东地区推荐 |
| 上海交通大学 | `https://mirror.sjtu.edu.cn/` | 上海地区推荐 |
| 华中科技大学 | `https://mirrors.hust.edu.cn/` | 华中地区推荐 |
| 哈尔滨工业大学 | `https://mirrors.hit.edu.cn/` | 东北地区推荐 |
| 西安交通大学 | `https://mirrors.xjtu.edu.cn/` | 西北地区推荐 |
| 南京大学 | `https://mirrors.nju.edu.cn/` | 华东地区推荐 |

#### 镜像源聚合网站

**中国教育网联合镜像站**：https://help.mirrors.cernet.edu.cn/

该网站汇总了所有高校镜像源的使用帮助和配置方法，是查找镜像源配置的首选参考。

### 6.3 pip 镜像源配置

#### 临时使用

```bash
# 使用清华源安装
pip install numpy -i https://pypi.tuna.tsinghua.edu.cn/simple

# 使用中科大源安装
pip install numpy -i https://pypi.mirrors.ustc.edu.cn/simple/

# 信任主机（避免 SSL 警告）
pip install numpy -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

#### 永久配置

```bash
# 方法 1：使用 pip config 命令
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 查看配置
pip config list

# 恢复默认
pip config unset global.index-url
```

```bash
# 方法 2：手动创建配置文件

# Windows: %APPDATA%\pip\pip.ini
# Linux/macOS: ~/.pip/pip.conf

# 配置文件内容：
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn

# 多源配置（fallback 机制）：
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
extra-index-url = https://mirrors.aliyun.com/pypi/simple/
trusted-host = pypi.tuna.tsinghua.edu.cn mirrors.aliyun.com
```

#### 常用 pip 镜像源

| 镜像源 | 地址 |
|--------|------|
| 清华大学 | `https://pypi.tuna.tsinghua.edu.cn/simple` |
| 中科大 | `https://pypi.mirrors.ustc.edu.cn/simple/` |
| 北京大学 | `https://mirrors.pku.edu.cn/pypi/web/simple` |
| 阿里云 | `https://mirrors.aliyun.com/pypi/simple/` |
| 豆瓣 | `https://pypi.douban.com/simple/` |
| 华为云 | `https://repo.huaweicloud.com/repository/pypi/simple/` |
| 腾讯云 | `https://mirrors.cloud.tencent.com/pypi/simple` |

### 6.4 conda/mamba 镜像源配置

#### 永久配置

```bash
# 添加清华源
mamba config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
mamba config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
mamba config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge
mamba config --set show_channel_urls yes

# 或使用中科大源
mamba config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/main
mamba config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/free
mamba config --add channels https://mirrors.ustc.edu.cn/anaconda/cloud/conda-forge
mamba config --set show_channel_urls yes

# 查看配置
mamba config --show channels
mamba config --show
```

#### 手动编辑配置文件

```bash
# 配置文件位置
# Linux/macOS: ~/.condarc
# Windows: C:\Users\<username>\.condarc

# 编辑配置文件
mamba config --describe   # 查看所有配置项
```

`.condarc` 配置示例（清华源）：

```yaml
channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
  - defaults
show_channel_urls: true
default_channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/pro
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2
```

#### 常用 conda 镜像源

| 镜像源 | 地址 |
|--------|------|
| 清华大学 | `https://mirrors.tuna.tsinghua.edu.cn/anaconda/` |
| 中科大 | `https://mirrors.ustc.edu.cn/anaconda/` |
| 北京大学 | `https://mirrors.pku.edu.cn/anaconda/` |
| 阿里云 | `https://mirrors.aliyun.com/anaconda/` |

#### 恢复默认配置

```bash
# 恢复默认频道
mamba config --remove-key channels
mamba config --set default_channels true

# 或删除配置文件
# Linux/macOS: rm ~/.condarc
# Windows: del %USERPROFILE%\.condarc
```

### 6.5 uv 镜像源配置

```bash
# 临时使用
uv pip install numpy --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 永久配置（通过环境变量）
# Linux/macOS:
export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# Windows PowerShell:
$env:UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"

# 或在 pyproject.toml 中配置
[tool.uv]
index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"
```

### 6.6 镜像源选择建议

| 网络环境 | 推荐镜像源 |
|----------|------------|
| 教育网（高校） | 本校镜像源 > 清华/中科大 |
| 电信/联通 | 阿里云/华为云/腾讯云 |
| 移动网络 | 华为云/阿里云 |
| 海外 | 官方源 |

---

## 7. 编译工具基础知识

### 7.1 为什么 Python 包需要编译？

大多数 Python 包是纯 Python 代码，直接安装即可。但某些包为了提高性能，会使用 C/C++ 编写核心代码：

```
纯 Python 包：
    源码 (.py) → 直接安装 → 运行

包含 C 扩展的包：
    源码 (.py + .c/.cpp) → 编译 → 二进制文件 → 安装 → 运行
```

**需要编译的常见场景：**
- 数值计算密集型代码（如 numpy、scipy）
- 需要调用系统底层库（如 HDF5、NetCDF）
- 需要 GPU 加速（如 CUDA 扩展）
- 需要包装现有的 C/C++ 库

### 7.2 编译流程概述

```
源代码 (.c/.cpp/.h)
    │
    ▼
预处理器 (Preprocessor)
    │  处理 #include, #define 等预处理指令
    ▼
编译器 (Compiler)
    │  将源代码编译为目标文件 (.o/.obj)
    ▼
链接器 (Linker)
    │  将多个目标文件和库文件链接为可执行文件或库
    ▼
输出：可执行文件 (.exe) 或 动态库 (.dll/.so/.dylib)
```

### 7.3 常见编译工具介绍

#### GCC (GNU Compiler Collection)

GCC 是 GNU 项目的编译器套件，支持 C、C++、Fortran、Go 等多种语言。

```bash
# 编译 C 程序
gcc -o hello hello.c

# 编译 C++ 程序
g++ -o hello hello.cpp

# 编译 Fortran 程序
gfortran -o hello hello.f90

# 常用选项
gcc -O2 -Wall -o hello hello.c
# -O2: 优化级别
# -Wall: 显示所有警告
# -o: 指定输出文件名
```

#### Clang/LLVM

Clang 是 LLVM 项目的 C/C++ 编译器，在 macOS 上是默认编译器。

```bash
# 编译 C 程序
clang -o hello hello.c

# 编译 C++ 程序
clang++ -o hello hello.cpp
```

#### MSVC (Microsoft Visual C++)

MSVC 是 Windows 上的官方 C/C++ 编译器。

```cmd
# 编译 C/C++ 程序
cl.exe hello.c

# 常用选项
cl.exe /O2 /W4 /EHsc hello.cpp
# /O2: 优化级别
# /W4: 警告级别
# /EHsc: 异常处理模式
```

### 7.4 Make 构建系统

#### 什么是 Make？

`make` 是一个自动化构建工具，用于管理项目的编译过程。它读取 `Makefile` 文件中的规则，自动判断哪些文件需要重新编译。

#### Makefile 基本语法

```makefile
# Makefile 示例

# 变量定义
CC = gcc
CFLAGS = -O2 -Wall
TARGET = myprogram

# 默认目标
all: $(TARGET)

# 规则：目标: 依赖
# 	命令（必须用 Tab 缩进）
$(TARGET): main.o utils.o
	$(CC) $(CFLAGS) -o $(TARGET) main.o utils.o

main.o: main.c
	$(CC) $(CFLAGS) -c main.c

utils.o: utils.c utils.h
	$(CC) $(CFLAGS) -c utils.c

# 清理
clean:
	rm -f *.o $(TARGET)

# 伪目标
.PHONY: all clean
```

#### Make 常用命令

```bash
# 执行默认目标（通常是 all）
make

# 执行指定目标
make clean

# 并行编译（加快速度）
make -j4

# 显示详细命令
make VERBOSE=1

# 指定 Makefile 文件
make -f MyMakefile
```

#### Make 变量和自动变量

```makefile
# 自动变量
# $@ - 目标文件名
# $< - 第一个依赖文件名
# $^ - 所有依赖文件名

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@
```

### 7.5 CMake —— 跨平台构建系统

#### 什么是 CMake？

CMake 是一个跨平台的构建系统生成器，它可以生成各种平台的构建文件（Makefile、Visual Studio 项目等）。

```
CMakeLists.txt → CMake → Makefile / VS Project / Ninja
                             ↓
                          make / msbuild / ninja
                             ↓
                          可执行文件 / 库
```

#### CMakeLists.txt 基本语法

```cmake
# CMakeLists.txt 示例

cmake_minimum_required(VERSION 3.10)
project(MyProject)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)

# 添加可执行文件
add_executable(myprogram main.cpp utils.cpp)

# 添加库
add_library(mylib STATIC utils.cpp)

# 查找并链接外部库
find_package(PkgConfig)
pkg_check_modules(SDL2 REQUIRED sdl2)
target_link_libraries(myprogram ${SDL2_LIBRARIES})
```

#### CMake 常用命令

```bash
# 创建构建目录
mkdir build && cd build

# 配置项目
cmake ..

# 指定生成器
cmake -G "Visual Studio 17 2022" ..
cmake -G "Unix Makefiles" ..
cmake -G "Ninja" ..

# 指定安装前缀
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..

# 编译
cmake --build .

# 安装
cmake --install .

# 编译并指定配置（多配置生成器）
cmake --build . --config Release
```

### 7.6 其他构建工具

| 工具 | 特点 | 使用场景 |
|------|------|----------|
| **Ninja** | 极快的构建速度 | 常作为 CMake 的后端 |
| **Meson** | 现代化、易用 | 新项目推荐 |
| **Autotools** | GNU 传统工具 | 老项目、Linux 软件 |
| **SCons** | Python 编写 | Python 项目 |
| **Bazel** | Google 出品 | 大型项目 |

---

## 8. 各平台编译工具安装指南

### 8.1 Windows

#### 方案 1：MSVC Build Tools（推荐）

```bash
# 下载地址
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 安装时选择 "使用 C++ 的桌面开发" 工作负载

# 验证安装（在 Developer Command Prompt 中）
cl
```

详细安装教程请参考 [MSVC 安装教程](msvc编译器安装教程.md)。

#### 方案 2：MinGW-w64（通过 conda）

```bash
# 使用 conda 安装 MinGW 工具链
mamba install -c conda-forge m2w64-toolchain

# 验证安装
gcc --version
g++ --version
```

#### 方案 3：MSYS2

```bash
# 下载安装 MSYS2
# https://www.msys2.org/

# 在 MSYS2 终端中安装工具链
pacman -S mingw-w64-x86_64-gcc
pacman -S mingw-w64-x86_64-cmake
pacman -S mingw-w64-x86_64-make
```

#### 方案 4：WSL (Windows Subsystem for Linux)

```bash
# 启用 WSL
wsl --install

# 在 WSL 中安装编译工具
sudo apt update
sudo apt install build-essential cmake
```

### 8.2 Linux

#### Ubuntu / Debian

```bash
# 安装基本编译工具
sudo apt update
sudo apt install build-essential

# build-essential 包含：
# - gcc: C 编译器
# - g++: C++ 编译器
# - make: 构建工具
# - libc-dev: C 标准库开发文件

# 安装 CMake
sudo apt install cmake

# 安装 Fortran 编译器
sudo apt install gfortran

# 安装 Python 开发头文件
sudo apt install python3-dev

# 安装常用的开发库
sudo apt install libhdf5-dev libnetcdf-dev libproj-dev libgeos-dev
```

#### CentOS / RHEL / Fedora

```bash
# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install cmake

# Fedora
sudo dnf groupinstall "Development Tools"
sudo dnf install cmake

# 安装 Python 开发头文件
sudo yum install python3-devel   # CentOS/RHEL
sudo dnf install python3-devel   # Fedora
```

#### Arch Linux

```bash
# 安装基本编译工具
sudo pacman -S base-devel cmake

# 安装 Python 开发文件
sudo pacman -S python
```

### 8.3 macOS

#### Xcode Command Line Tools

```bash
# 安装 Xcode 命令行工具（包含 Clang 编译器）
xcode-select --install

# 验证安装
clang --version
```

#### Homebrew

```bash
# 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装编译工具
brew install cmake
brew install gcc          # GNU 编译器（可选）
brew install llvm         # LLVM 编译器（可选）

# 安装常用开发库
brew install hdf5 netcdf proj geos
```

### 8.4 各平台编译工具对比

| 工具 | Windows | Linux | macOS | 说明 |
|------|---------|-------|-------|------|
| **GCC** | MinGW/MSYS2 | ✅ 默认 | brew install | GNU 编译器 |
| **Clang** | LLVM 官方 | ✅ 可选 | ✅ 默认 | LLVM 编译器 |
| **MSVC** | ✅ 默认 | ❌ | ❌ | 微软官方 |
| **CMake** | ✅ | ✅ | ✅ | 构建系统生成器 |
| **Make** | MinGW/MSYS2 | ✅ 默认 | ✅ 默认 | 构建工具 |
| **Ninja** | ✅ | ✅ | ✅ | 快速构建工具 |

---

## 9. Python 包的编译与安装

### 9.1 setup.py 方式（传统）

```python
# setup.py 示例
from setuptools import setup, Extension

# 定义 C 扩展
ext_modules = [
    Extension(
        'mypackage._core',
        sources=['src/core.c', 'src/utils.c'],
        include_dirs=['include'],
        libraries=['m'],
        extra_compile_args=['-O2'],
    )
]

setup(
    name='mypackage',
    version='1.0.0',
    ext_modules=ext_modules,
)
```

```bash
# 从源码安装
pip install .

# 开发模式安装（可编辑安装）
pip install -e .

# 构建 wheel
python setup.py bdist_wheel

# 构建源码包
python setup.py sdist
```

### 9.2 pyproject.toml 方式（现代）

```toml
# pyproject.toml 示例
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mypackage"
version = "1.0.0"
dependencies = ["numpy>=1.20"]

[tool.setuptools.ext-modules]
"mypackage._core" = {sources = ["src/core.c", "src/utils.c"]}
```

### 9.3 scikit-build-core 方式（CMake 集成）

```toml
# pyproject.toml
[build-system]
requires = ["scikit-build-core>=0.5", "pybind11>=2.10"]
build-backend = "scikit_build_core.build"

[project]
name = "mypackage"
version = "1.0.0"
```

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.15)
project(mypackage)

find_package(pybind11 REQUIRED)
pybind11_add_module(_core src/core.cpp)
install(TARGETS _core DESTINATION mypackage)
```

### 9.4 编译时常见问题

#### 问题 1：找不到头文件

```bash
error: Python.h: No such file or directory
```

**解决方案：**
```bash
# Linux
sudo apt install python3-dev

# macOS (使用 Homebrew Python)
export CFLAGS="-I$(python3 -c 'import sysconfig; print(sysconfig.get_path("include"))')"

# Windows
# 确保安装了 Python 开发包
```

#### 问题 2：找不到库文件

```bash
error: cannot find -lhdf5
```

**解决方案：**
```bash
# Linux
sudo apt install libhdf5-dev

# macOS
brew install hdf5
export LDFLAGS="-L$(brew --prefix hdf5)/lib"
export CFLAGS="-I$(brew --prefix hdf5)/include"

# Windows
# 使用 conda 安装
mamba install -c conda-forge hdf5
```

#### 问题 3：编译器版本不兼容

```bash
error: Microsoft Visual C++ 14.0 or greater is required
```

**解决方案：**
1. 安装 MSVC Build Tools
2. 或使用 conda 安装预编译包
3. 参考 [MSVC 安装教程](msvc编译器安装教程.md)

---

## 10. 工具选择建议

### 10.1 按场景选择

| 场景 | 推荐工具 | 原因 |
|------|----------|------|
| 科学计算 / 气象数据处理 | **mamba** | 预编译包，无需编译器，管理系统库 |
| 快速安装纯 Python 包 | **uv** | 速度极快 |
| 通用 Python 开发 | **uv** + **mamba** | 结合两者优势 |
| 需要精确锁定依赖 | **pip** + **poetry** | 锁文件机制 |
| CI/CD 流水线 | **uv** | 安装速度最快 |
| 学习 / 简单项目 | **venv** + **pip** | 内置，无需额外安装 |
| 多 Python 版本管理 | **conda** / **uv** | 支持管理 Python 版本 |

### 10.2 混合使用策略（推荐）

```bash
# 1. 用 mamba 创建环境并安装难编译的科学计算包
mamba create -n myenv python=3.11
mamba activate myenv
mamba install numpy scipy pandas cartopy netcdf4 -c conda-forge

# 2. 用 pip 安装其他纯 Python 包
pip install requests flask django

# 或者用 uv 替代 pip（更快）
uv pip install requests flask django
```

### 10.3 metgrs 推荐安装方式

```bash
# 方式 1：pip（最简单）
pip install metgrs

# 方式 2：mamba + pip（推荐，避免编译问题）
mamba create -n metgrs python=3.11 -c conda-forge -y
mamba activate metgrs
pip install metgrs

# 方式 3：uv（最快）
uv venv metgrs-env
source metgrs-env/bin/activate
uv pip install metgrs

# 方式 4：venv + pip（纯标准库）
python -m venv metgrs-env
source metgrs-env/bin/activate  # Linux/macOS
# metgrs-env\Scripts\activate   # Windows
pip install metgrs
```

---

## 11. 常见问题

### Q1: pip 安装包时报错 "Microsoft Visual C++ 14.0 or greater is required"

这是因为包没有预编译 wheel，需要本地编译。解决方案：

1. 使用 conda/mamba 安装（推荐）
2. 安装 MSVC Build Tools（参考 [MSVC 安装教程](msvc编译器安装教程.md)）
3. 从第三方下载预编译 wheel

### Q2: conda 安装速度太慢

1. 使用 mamba 替代 conda
2. 配置国内镜像源（参考 [国内镜像源配置](#6-国内镜像源配置)）

### Q3: pip 和 conda 混用会不会有问题？

混用时需要注意：
- 安装顺序：**先 conda，后 pip**
- 避免用 pip 安装 conda 已有的包（可能导致依赖冲突）
- 导出环境时分别导出：`conda env export` 和 `pip freeze`

### Q4: venv 创建的虚拟环境在哪里？

虚拟环境默认创建在当前目录下。如果使用 `python -m venv myenv`，则在 `myenv/` 目录中。

### Q5: 如何删除 matplotlib 字体缓存？

```bash
# 查看缓存位置
python -c "import matplotlib; print(matplotlib.get_cachedir())"

# 删除缓存
rm -rf ~/.cache/matplotlib          # Linux/macOS
# Windows: 删除 %USERPROFILE%\.matplotlib 目录
```

### Q6: Windows 上没有 make 命令怎么办？

```bash
# 方案 1：使用 CMake 生成 Visual Studio 项目
cmake -G "Visual Studio 17 2022" ..
cmake --build . --config Release

# 方案 2：使用 MinGW 的 make
mamba install -c conda-forge m2w64-make
mingw32-make

# 方案 3：使用 Ninja
mamba install -c conda-forge ninja
cmake -G Ninja ..
ninja
```

### Q7: 如何查看包是否需要编译？

```bash
# 查看 PyPI 上的包是否有 wheel
pip index versions numpy

# 强制只使用 wheel（如果失败说明需要编译）
pip install --only-binary :all: numpy

# 查看包的安装日志
pip install -v numpy 2>&1 | grep -i "building\|compiling\|error"
```

---

## 12. 参考资源

### 包管理工具

- [pip 官方文档](https://pip.pypa.io/en/stable/)
- [venv 官方文档](https://docs.python.org/3/library/venv.html)
- [conda 官方文档](https://docs.conda.io/en/latest/)
- [mamba 官方文档](https://mamba.readthedocs.io/en/latest/)
- [uv 官方文档](https://docs.astral.sh/uv/)
- [poetry 官方文档](https://python-poetry.org/docs/)
- [conda-forge 频道](https://conda-forge.org/)
- [PyPI 官方网站](https://pypi.org/)
- [Miniforge 下载](https://conda-forge.org/miniforge/)

### 编译工具

- [GCC 官方文档](https://gcc.gnu.org/onlinedocs/)
- [CMake 官方文档](https://cmake.org/cmake/help/latest/)
- [Make 官方手册](https://www.gnu.org/software/make/manual/)
- [MSVC 官方文档](https://learn.microsoft.com/en-us/cpp/)
- [Meson 官方文档](https://mesonbuild.com/)

### 国内镜像源

- [中国教育网联合镜像站](https://help.mirrors.cernet.edu.cn/) - 镜像源配置帮助汇总
- [清华大学镜像源](https://mirrors.tuna.tsinghua.edu.cn/)
- [中国科学技术大学镜像源](https://mirrors.ustc.edu.cn/)
- [北京大学镜像源](https://mirrors.pku.edu.cn/)
- [浙江大学镜像源](https://mirrors.zju.edu.cn/)
- [上海交通大学镜像源](https://mirror.sjtu.edu.cn/)
- [阿里云镜像源](https://mirrors.aliyun.com/)
