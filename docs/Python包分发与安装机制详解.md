---
layout: doc
title: Python 包分发与安装机制详解
description: 深入了解 Python 包的分发方式（源码与二进制）、pip 安装流程、wheel 格式等底层细节
---

# Python 包分发与安装机制详解

## 目录

1. [概述](#1-概述)
2. [Python 包的两种分发形式](#2-python-包的两种分发形式)
3. [源码分发（sdist）详解](#3-源码分发sdist详解)
4. [二进制分发（wheel）详解](#4-二进制分发wheel详解)
5. [Wheel 命名规范与平台标签](#5-wheel-命名规范与平台标签)
6. [pip 安装流程深度解析](#6-pip-安装流程深度解析)
7. [pip 命令详解](#7-pip-命令详解)
8. [构建系统与后端](#8-构建系统与后端)
9. [编译扩展模块](#9-编译扩展模块)
10. [跨平台分发策略](#10-跨平台分发策略)
11. [现代打包工具链](#11-现代打包工具链)
12. [常见问题与解决方案](#12-常见问题与解决方案)
13. [参考资源](#13-参考资源)

---

## 1. 概述

### 1.1 Python 包分发的历史演进

Python 包分发机制经历了多次演进：

```
distutils (1998)  →  setuptools (2004)  →  wheel (2012)  →  pyproject.toml (2016)
    │                    │                    │                    │
    │                    │                    │                    └── PEP 517/518/621
    │                    │                    └── PEP 427：预编译二进制格式
    │                    └── 增强的 distutils，支持更多功能
    └── Python 标准库，基本构建功能
```

### 1.2 核心概念

| 概念 | 说明 |
|------|------|
| **包（Package）** | 包含 `__init__.py` 的 Python 模块集合 |
| **模块（Module）** | 单个 `.py` 文件 |
| **分发包（Distribution Package）** | 可以安装的包，包含元数据和代码 |
| **构建系统（Build System）** | 将源码转换为分发包的工具链 |
| **包索引（Package Index）** | 存储和分发包的服务器（如 PyPI） |

### 1.3 分发包的生命周期

```
源代码开发
    │
    ▼
构建（Build）
    │  使用构建后端将源码打包
    ▼
分发包（Distribution）
    ├── sdist（源码分发包）
    └── wheel（二进制分发包）
    │
    ▼
发布（Publish）
    │  上传到 PyPI 或其他索引
    ▼
安装（Install）
    │  pip 下载并安装到用户环境
    ▼
运行（Runtime）
```

---

## 2. Python 包的两种分发形式

### 2.1 概览对比

| 特性 | sdist（源码分发） | wheel（二进制分发） |
|------|-------------------|---------------------|
| **文件格式** | `.tar.gz` | `.whl` |
| **内容** | 源代码 + 构建脚本 | 预编译的可安装文件 |
| **安装过程** | 下载 → 解压 → 构建 → 安装 | 下载 → 解压 → 安装 |
| **是否需要编译器** | ⚠️ 可能需要 | ❌ 永远不需要 |
| **安装速度** | 较慢 | 极快 |
| **跨平台** | ✅ 通用 | ❌ 特定平台 |
| **文件大小** | 较小 | 较大（包含二进制） |

### 2.2 为什么需要两种形式？

```
开发者视角：
    源码 → sdist（通用分发）→ 任何人可以从源码构建
    源码 → wheel（快速安装）→ 用户无需编译环境

用户视角：
    pip install numpy
        │
        ├─ 优先查找 wheel（预编译）→ 直接安装（秒级）
        │
        └─ 如果没有 wheel → 下载 sdist → 编译 → 安装（分钟级）
```

### 2.3 选择策略

| 场景 | 推荐格式 | 原因 |
|------|----------|------|
| 纯 Python 包 | sdist 或 wheel | 无需编译，两者都可 |
| 包含 C 扩展 | wheel（必须） | 避免用户编译失败 |
| 特定平台优化 | wheel | 可针对平台优化编译 |
| 源码审查 | sdist | 包含完整源码 |

---

## 3. 源码分发（sdist）详解

### 3.1 sdist 的结构

```
mypackage-1.0.0.tar.gz
    │
    └── mypackage-1.0.0/
        ├── PKG-INFO                    # 包元数据
        ├── pyproject.toml              # 构建配置
        ├── setup.py                    # 传统构建脚本（可选）
        ├── setup.cfg                   # 传统配置（可选）
        ├── README.md                   # 项目说明
        ├── LICENSE                     # 许可证
        ├── mypackage/                  # Python 源码
        │   ├── __init__.py
        │   ├── core.py
        │   └── utils.py
        ├── src/                        # C/C++ 源码（如有）
        │   ├── core.c
        │   └── utils.cpp
        ├── include/                    # 头文件（如有）
        │   └── mypackage.h
        └── tests/                      # 测试代码
            ├── test_core.py
            └── test_utils.py
```

### 3.2 PKG-INFO 文件

`PKG-INFO` 是包的元数据文件，遵循 RFC 822 格式：

```
Metadata-Version: 2.1
Name: mypackage
Version: 1.0.0
Summary: A sample package
Home-page: https://github.com/user/mypackage
Author: Author Name
Author-email: author@example.com
License: MIT
Classifier: Programming Language :: Python :: 3
Classifier: License :: OSI Approved :: MIT License
Requires-Python: >=3.8
Requires-Dist: numpy>=1.20
Requires-Dist: pandas>=1.3
Description-Content-Type: text/markdown
```

### 3.3 构建 sdist

```bash
# 使用现代构建工具
pip install build
python -m build --sdist

# 使用 setuptools
python setup.py sdist

# 使用 flit
flit build --format sdist

# 使用 poetry
poetry build --format sdist
```

### 3.4 sdist 的安装过程

```
pip install mypackage-1.0.0.tar.gz
    │
    ├─ 1. 解压 tar.gz 到临时目录
    │
    ├─ 2. 读取 pyproject.toml 或 setup.py
    │      确定构建后端（setuptools, flit, poetry 等）
    │
    ├─ 3. 创建隔离的构建环境
    │      安装构建依赖（build-system.requires）
    │
    ├─ 4. 调用构建后端
    │      python -m setuptools.build_meta
    │      │
    │      ├─ 编译 C/C++ 扩展（如有）
    │      ├─ 生成 wheel
    │      └─ 返回 wheel 路径
    │
    ├─ 5. 安装生成的 wheel
    │      复制文件到 site-packages/
    │
    └─ 6. 清理临时文件
```

### 3.5 sdist 的优缺点

**优点：**
- ✅ 通用性强，一份源码可在任何平台构建
- ✅ 文件体积小
- ✅ 包含完整源码，便于审查
- ✅ 支持自定义编译选项

**缺点：**
- ❌ 安装时需要构建环境（编译器等）
- ❌ 安装速度慢
- ❌ 可能因环境差异导致构建失败
- ❌ 依赖解析复杂

---

## 4. 二进制分发（wheel）详解

### 4.1 Wheel 格式规范

Wheel 格式由 PEP 427 定义，文件扩展名为 `.whl`，实际上是一个 ZIP 格式的压缩包。

### 4.2 Wheel 的内部结构

```
mypackage-1.0.0-cp311-cp311-win_amd64.whl
    │
    ├── mypackage/                      # 安装到 site-packages/ 的文件
    │   ├── __init__.py
    │   ├── core.py
    │   ├── utils.py
    │   └── _core.cp311-win_amd64.pyd   # 编译后的 C 扩展
    │
    └── mypackage-1.0.0.dist-info/      # 包元数据
        ├── METADATA                    # 包的元数据（类似 PKG-INFO）
        ├── WHEEL                       # Wheel 自身的元数据
        ├── RECORD                      # 文件清单和哈希
        ├── INSTALLER                   # 安装器标识（如 "pip"）
        ├── REQUESTED                   # 标记是否用户主动请求
        ├── top_level.txt               # 顶层包名
        └── entry_points.txt            # 入口点（如有）
```

### 4.3 WHEEL 文件详解

`WHEEL` 文件包含 wheel 自身的元数据：

```
Wheel-Version: 1.0
Generator: setuptools (69.0.0)
Root-Is-Purelib: false
Tag: cp311-cp311-win_amd64
```

| 字段 | 说明 |
|------|------|
| Wheel-Version | Wheel 格式版本 |
| Generator | 生成此 wheel 的工具 |
| Root-Is-Purelib | 是否为纯 Python 包（无平台依赖） |
| Tag | 平台标签（见下文） |

### 4.4 RECORD 文件详解

`RECORD` 文件记录了所有安装文件的路径和哈希值：

```
mypackage/__init__.py,sha256=xxx,1234
mypackage/core.py,sha256=yyy,5678
mypackage/_core.cp311-win_amd64.pyd,sha256=zzz,9012
mypackage-1.0.0.dist-info/METADATA,sha256=aaa,3456
mypackage-1.0.0.dist-info/WHEEL,sha256=bbb,7890
mypackage-1.0.0.dist-info/RECORD,,
```

### 4.5 Wheel 的安装过程

```
pip install mypackage-1.0.0-cp311-cp311-win_amd64.whl
    │
    ├─ 1. 验证 wheel 兼容性
    │      检查 Python 版本、平台是否匹配
    │
    ├─ 2. 解压 wheel 到临时目录
    │
    ├─ 3. 复制文件到目标位置
    │      mypackage/ → site-packages/mypackage/
    │      mypackage-1.0.0.dist-info/ → site-packages/mypackage-1.0.0.dist-info/
    │
    ├─ 4. 更新 easy-install.pth（如需要）
    │
    ├─ 5. 运行 post-install 脚本（如有）
    │
    └─ 6. 记录安装信息
           更新 installed-files.txt
```

### 4.6 Wheel 的优缺点

**优点：**
- ✅ 安装速度极快（无需编译）
- ✅ 无需编译器
- ✅ 安装过程确定性强
- ✅ 支持平台特定优化

**缺点：**
- ❌ 需要为每个平台单独构建
- ❌ 文件体积较大
- ❌ 不包含源码
- ❌ 维护成本高

---

## 5. Wheel 命名规范与平台标签

### 5.1 命名格式

Wheel 文件名遵循严格的命名规范：

```
{distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl

示例：
numpy-1.24.0-cp39-cp39-win_amd64.whl
│       │      │    │    │
│       │      │    │    └── 平台标签
│       │      │    └── ABI 标签
│       │      └── Python 标签
│       └── 版本号
└── 包名
```

### 5.2 Python 标签（Python Tag）

| 标签 | 含义 |
|------|------|
| `py3` | 任意 Python 3 版本 |
| `cp39` | CPython 3.9 |
| `cp310` | CPython 3.10 |
| `cp311` | CPython 3.11 |
| `pp38` | PyPy 3.8 |
| `py2.py3` | Python 2 和 3 通用 |

### 5.3 ABI 标签（ABI Tag）

| 标签 | 含义 |
|------|------|
| `none` | 无 ABI 要求 |
| `cp39` | CPython 3.9 ABI |
| `abi3` | Python 3 稳定 ABI（向后兼容） |
| `cp39d` | CPython 3.9 调试版 ABI |

### 5.4 平台标签（Platform Tag）

| 标签 | 含义 |
|------|------|
| `any` | 任意平台 |
| `win_amd64` | Windows 64 位 (x86_64) |
| `win32` | Windows 32 位 |
| `win_arm64` | Windows ARM64 |
| `manylinux_2_17_x86_64` | Linux x86_64（manylinux 标准） |
| `manylinux_2_17_aarch64` | Linux ARM64 |
| `macosx_10_9_x86_64` | macOS 10.9+ x86_64 |
| `macosx_11_0_arm64` | macOS 11.0+ ARM64（Apple Silicon） |
| `musllinux_1_1_x86_64` | Alpine Linux x86_64 |

### 5.5 manylinux 标准详解

manylinux 是 Linux 平台上 Python wheel 的兼容性标准：

```
manylinux_2_17_x86_64
│       │   │
│       │   └── 平台架构
│       └── glibc 最低版本（2.17 = CentOS 7）
└── 标准名称

兼容性：
    manylinux_2_17_x86_64 wheel 可以在以下系统上安装：
    ├── CentOS 7+ (glibc 2.17+)
    ├── Ubuntu 18.04+ (glibc 2.27+)
    ├── Debian 10+ (glibc 2.28+)
    └── 其他 glibc >= 2.17 的系统
```

### 5.6 通用 Wheel（Pure Python）

纯 Python 包可以构建为通用 wheel：

```
mypackage-1.0.0-py3-none-any.whl
    │          │    │    │
    │          │    │    └── any = 任意平台
    │          │    └── none = 无 ABI 要求
    │          └── py3 = Python 3
    └── 包名

特点：
- 一个 wheel 适用于所有平台和 Python 版本
- 文件体积小
- 安装速度快
```

### 5.7 多平台 Wheel 示例

```bash
# 同一个包的不同平台 wheel
numpy-1.24.0-cp39-cp39-win_amd64.whl      # Windows x64
numpy-1.24.0-cp39-cp39-manylinux_2_17_x86_64.whl  # Linux x64
numpy-1.24.0-cp39-cp39-macosx_10_9_x86_64.whl    # macOS x64
numpy-1.24.0-cp39-cp39-macosx_11_0_arm64.whl      # macOS ARM64
```

---

## 6. pip 安装流程深度解析

### 6.1 完整安装流程

```
pip install numpy
    │
    ├─ 1. 解析包名和版本约束
    │      numpy → "最新版本"
    │      numpy==1.24.0 → "精确版本"
    │      numpy>=1.24,<1.26 → "版本范围"
    │
    ├─ 2. 查询包索引
    │      │
    │      ├─ 请求 PyPI API：https://pypi.org/pypi/numpy/json
    │      │   返回：所有可用版本、文件列表
    │      │
    │      └─ 筛选兼容的文件
    │          ├─ Python 版本匹配
    │          ├─ 平台匹配
    │          └─ ABI 匹配
    │
    ├─ 3. 选择最佳文件
    │      │
    │      ├─ 优先选择 wheel（预编译）
    │      │   numpy-1.24.0-cp39-cp39-win_amd64.whl
    │      │
    │      └─ 如果没有 wheel → 选择 sdist
    │          numpy-1.24.0.tar.gz
    │
    ├─ 4. 下载文件
    │      │
    │      ├─ 检查本地缓存
    │      │   ~/.cache/pip/http/  (HTTP 缓存)
    │      │   ~/.cache/pip/packages/  (包缓存)
    │      │
    │      └─ 如果缓存未命中 → 下载
    │          使用 HTTP Range 请求支持断点续传
    │
    ├─ 5. 验证文件
    │      │
    │      ├─ 检查哈希（如果指定了 --require-hashes）
    │      │
    │      └─ 检查签名（如果支持）
    │
    ├─ 6. 安装文件
    │      │
    │      ├─ wheel → 直接解压安装
    │      │
    │      └─ sdist → 构建 → wheel → 安装
    │          │
    │          ├─ 创建隔离构建环境
    │          ├─ 安装构建依赖
    │          ├─ 调用构建后端
    │          └─ 安装生成的 wheel
    │
    └─ 7. 更新元数据
           │
           ├─ 写入 .dist-info/
           ├─ 更新 installed-files.txt
           └─ 运行 post-install 脚本
```

### 6.2 依赖解析

pip 的依赖解析器负责确定所有包的版本：

```
pip install mypackage
    │
    ├─ 获取 mypackage 的依赖
    │   Requires-Dist: numpy>=1.20
    │   Requires-Dist: pandas>=1.3
    │
    ├─ 获取 numpy 的依赖
    │   Requires-Dist: ...
    │
    ├─ 获取 pandas 的依赖
    │   Requires-Dist: numpy>=1.20,<2.0
    │
    └─ 解析版本冲突
        │
        ├─ numpy>=1.20 (来自 mypackage)
        ├─ numpy>=1.20,<2.0 (来自 pandas)
        │
        └─ 最终选择：numpy==1.24.0（满足所有约束）
```

### 6.3 构建隔离

pip 在构建 sdist 时会创建隔离环境：

```bash
# 构建隔离过程
/tmp/pip-build-env-xxxxx/
├── lib/python3.11/site-packages/
│   ├── setuptools/        # 构建后端
│   ├── wheel/             # wheel 构建工具
│   └── 其他构建依赖
└── bin/
    └── python             # 隔离的 Python

# 然后在此环境中执行构建
cd /tmp/pip-install-xxxxx/mypackage/
/tmp/pip-build-env-xxxxx/bin/python -m setuptools.build_meta
```

### 6.4 安装位置

```bash
# 查看包的安装位置
python -c "import numpy; print(numpy.__file__)"
# 输出：/path/to/lib/python3.11/site-packages/numpy/__init__.py

# site-packages 目录结构
site-packages/
├── numpy/                      # 包代码
│   ├── __init__.py
│   ├── core.py
│   └── ...
├── numpy-1.24.0.dist-info/    # 包元数据
│   ├── METADATA
│   ├── WHEEL
│   ├── RECORD
│   └── ...
└── numpy.libs/                 # 共享库（Linux）
    └── libopenblas.so.0
```

### 6.5 pip 缓存机制

```bash
# 缓存目录结构
~/.cache/pip/                   # Linux/macOS
%LOCALAPPDATA%\pip\Cache\       # Windows
│
├── http/                       # HTTP 响应缓存
│   └── <hash>/
│       └── <hash>.json
│
├── packages/                   # 下载的包文件
│   └── <hash>/
│       └── numpy-1.24.0-cp39-cp39-win_amd64.whl
│
└── selfcheck/                  # pip 版本检查
    └── selfcheck.json

# 缓存管理命令
pip cache info                  # 查看缓存信息
pip cache list                  # 列出缓存的包
pip cache purge                 # 清除所有缓存
pip cache remove numpy          # 清除特定包缓存
```

---

## 7. pip 命令详解

### 7.1 pip 安装命令基础

pip 是 Python 的标准包管理器，提供了丰富的命令来管理 Python 包。

```bash
# 基本安装
pip install package_name

# 安装指定版本
pip install package_name==1.0.0
pip install "package_name>=1.0,<2.0"

# 从 requirements.txt 安装
pip install -r requirements.txt

# 升级包
pip install --upgrade package_name

# 卸载包
pip uninstall package_name
```

### 7.2 pip 安装选项详解

```bash
# 仅使用预编译 wheel（不从源码编译）
pip install --only-binary :all: package_name

# 强制从源码编译
pip install --no-binary :all: package_name

# 不使用缓存
pip install --no-cache-dir package_name

# 安装到用户目录
pip install --user package_name

# 详细输出（查看安装过程）
pip install -v package_name

# 保留构建临时文件（调试用）
pip install --no-clean package_name

# 指定 Python 版本
pip3.11 install package_name

# 安装可编辑模式（开发用）
pip install -e .
```

### 7.3 构建隔离机制

pip 在安装源码包（sdist）时，默认会使用**构建隔离**机制：

```bash
pip install cinrad
```

**构建隔离的工作原理：**

```
pip install cinrad
    │
    ├─ 1. 下载 cinrad-x.x.x.tar.gz (sdist)
    │
    ├─ 2. 创建临时隔离环境
    │      /tmp/pip-build-env-xxxxx/
    │      ├── lib/python3.x/site-packages/
    │      │   └── setuptools/, wheel/  # 构建工具
    │      └── bin/python
    │
    ├─ 3. 在隔离环境中安装构建依赖
    │      pip install numpy cython  # 根据 pyproject.toml 的 requires
    │
    ├─ 4. 在隔离环境中执行构建
    │      python setup.py build_ext --inplace
    │      # 编译 C 扩展，需要链接 numpy 的头文件
    │
    └─ 5. 将构建好的 wheel 安装到目标环境
```

### 7.4 案例分析：Linux 安装 cinrad 失败问题

#### 问题描述

在 Linux 系统上使用 pip 安装 `cinrad`（中国气象雷达数据处理库）时，经常遇到安装失败的情况：

```bash
$ pip install cinrad
```

**错误信息示例：**

```
  error: command 'gcc' failed with exit status 1
  
  numpy/core/include/numpy/npy_common.h:253:2: error: #error "Must use a C compiler to compile numpy"
  
  or
  
  FileNotFoundError: numpy/core/include/numpy/npy_common.h not found
  
  or
  
  ImportError: numpy.core.multiarray failed to import
```

#### 问题根因分析

**核心问题：构建隔离环境中的 numpy 版本不兼容**

```
时间线：
1. pip 下载 cinrad-x.x.x.tar.gz (sdist)
2. pip 创建隔离构建环境 /tmp/pip-build-env-xxxxx/
3. pip 在隔离环境中安装 cinrad 的构建依赖
   │
   └─ 根据 pyproject.toml:
      [build-system]
      requires = ["setuptools", "numpy", "cython"]
      
      pip 会安装最新版本的 numpy 到隔离环境
      │
      └─ 问题：最新 numpy (如 2.x) 可能与 cinrad 代码不兼容
         或者隔离环境中的 numpy 缺少编译好的头文件

4. pip 在隔离环境中编译 cinrad 的 C 扩展
   │
   └─ 失败！因为：
      - numpy 2.x 的 API 与 numpy 1.x 不兼容
      - 或者隔离环境中的 numpy 没有预编译的头文件

5. 安装失败
```

**详细技术原因：**

1. **cinrad 包含 C 扩展模块**，需要编译
2. **cinrad 的 C 扩展依赖 numpy 的 C API**（头文件）
3. **pip 的构建隔离机制**会创建临时环境并安装构建依赖
4. **隔离环境中的 numpy 版本可能不兼容**：
   - numpy 2.x 与 numpy 1.x 的 C API 不完全兼容
   - 某些 numpy 版本的 sdist 安装时可能缺少预编译的头文件
5. **编译失败**：找不到 numpy 头文件或版本不匹配

#### 解决方案

**方案 1：禁用构建隔离（推荐）**

```bash
# 不使用隔离环境，在当前环境中构建
pip install --no-build-isolation cinrad
```

**原理：**
- 直接在当前 Python 环境中构建
- 使用当前环境中已安装的 numpy（通常是预编译的 wheel）
- 避免了隔离环境中的版本不兼容问题

**前提条件：**
- 当前环境已安装 numpy（推荐先手动安装）
- 已安装编译器（gcc/g++）

```bash
# 步骤：
pip install numpy cython  # 先安装构建依赖
pip install --no-build-isolation cinrad
```

**方案 2：指定兼容的 numpy 版本**

```bash
# 先安装兼容版本的 numpy
pip install "numpy<2.0"

# 然后安装 cinrad（不使用隔离）
pip install --no-build-isolation cinrad
```

**方案 3：安装编译依赖**

```bash
# Ubuntu/Debian
sudo apt install build-essential python3-dev python3-numpy

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel python3-numpy

# 然后安装
pip install --no-build-isolation cinrad
```

**方案 4：使用 conda/mamba（最简单）**

```bash
# conda 会安装预编译的二进制包，无需编译
mamba install -c conda-forge cinrad
```

**方案 5：从预编译 wheel 安装**

```bash
# 如果 PyPI 上有对应平台的 wheel
pip install cinrad --only-binary :all:

# 或从其他源下载 wheel
pip install cinrad -f https://mirrors.tuna.tsinghua.edu.cn/pypi/simple/
```

#### 完整解决流程

```bash
# 1. 检查当前环境
python --version
pip show numpy

# 2. 安装编译工具（如果没有）
sudo apt install build-essential python3-dev  # Linux

# 3. 安装 numpy（确保是 wheel 版本）
pip install numpy

# 4. 安装 cinrad（禁用隔离）
pip install --no-build-isolation cinrad

# 5. 验证安装
python -c "import cinrad; print(cinrad.__version__)"
```

#### 类似问题的通用解决思路

当遇到 **"源码安装失败"** 问题时，可以按照以下思路排查：

```
安装失败
    │
    ├─ 检查是否有预编译 wheel
    │   pip install --only-binary :all: package_name
    │
    ├─ 检查是否需要禁用隔离
    │   pip install --no-build-isolation package_name
    │
    ├─ 检查是否缺少编译依赖
    │   sudo apt install build-essential python3-dev
    │
    ├─ 检查 numpy/scipy 等依赖版本
    │   pip install "numpy<2.0"
    │
    └─ 使用 conda/mamba 替代
        mamba install package_name
```

---

## 8. 构建系统与后端

### 8.1 PEP 517/518 构建系统

现代 Python 包使用 `pyproject.toml` 定义构建系统：

```toml
# pyproject.toml

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mypackage"
version = "1.0.0"
dependencies = ["numpy>=1.20"]
```

| 字段 | 说明 |
|------|------|
| `build-system.requires` | 构建时需要的依赖 |
| `build-system.build-backend` | 构建后端模块 |
| `project` | 包的元数据（PEP 621） |

### 8.2 常用构建后端

| 后端 | 特点 | 使用场景 |
|------|------|----------|
| **setuptools** | 传统，功能全面 | 通用项目 |
| **flit** | 简单，纯 Python 包 | 简单项目 |
| **poetry** | 依赖管理 + 打包 | 需要依赖锁定的项目 |
| **pdm** | PEP 582 支持 | 现代项目 |
| **hatchling** | 现代化，插件系统 | 新项目推荐 |
| **scikit-build-core** | CMake 集成 | 包含 CMake 项目的包 |
| **meson-python** | Meson 集成 | 使用 Meson 的项目 |
| **maturin** | Rust 扩展 | PyO3 绑定 |

### 8.3 setuptools 构建流程

```python
# setup.py 或 pyproject.toml 中的配置

# 1. 收集元数据
name = "mypackage"
version = "1.0.0"
install_requires = ["numpy>=1.20"]

# 2. 收集 Python 文件
packages = find_packages()

# 3. 编译 C 扩展（如有）
ext_modules = [
    Extension(
        'mypackage._core',
        sources=['src/core.c'],
        include_dirs=['include'],
        libraries=['m'],
    )
]

# 4. 生成 wheel
# python setup.py bdist_wheel
# 或 python -m build --wheel
```

### 8.4 构建后端接口

构建后端必须实现 PEP 517 定义的接口：

```python
# build_backend.py

def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """构建 wheel 文件"""
    # 1. 收集源码
    # 2. 编译扩展（如有）
    # 3. 创建 wheel 结构
    # 4. 打包为 .whl 文件
    # 5. 返回 wheel 文件名
    return "mypackage-1.0.0-py3-none-any.whl"

def build_sdist(sdist_directory, config_settings=None):
    """构建 sdist 文件"""
    # 1. 收集源码
    # 2. 创建 tar.gz 结构
    # 3. 返回 sdist 文件名
    return "mypackage-1.0.0.tar.gz"

def get_requires_for_build_wheel(config_settings=None):
    """获取构建 wheel 需要的依赖"""
    return ["numpy", "cython"]

def get_requires_for_build_sdist(config_settings=None):
    """获取构建 sdist 需要的依赖"""
    return []
```

---

## 9. 编译扩展模块

### 9.1 C 扩展类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **CPython C API** | 直接使用 Python C API | numpy 核心 |
| **Cython** | Python 到 C 的编译器 | pandas 部分模块 |
| **pybind11** | C++11 到 Python 的绑定 | OpenCV Python |
| **cffi** | C 外部函数接口 | cryptography |
| **SWIG** | 多语言绑定生成器 | 老项目 |
| **PyO3/maturin** | Rust 到 Python 的绑定 | ruff |

### 9.2 C 扩展编译流程

```
源码 (.c/.cpp)
    │
    ▼
预处理
    │  处理 #include, #define
    ▼
编译
    │  生成目标文件 (.o/.obj)
    │
    │  编译选项：
    │  -I<include_dir>     # 头文件搜索路径
    │  -L<lib_dir>         # 库文件搜索路径
    │  -l<library>         # 链接库
    │  -O2                 # 优化级别
    │  -fPIC               # 位置无关代码
    ▼
链接
    │  链接 Python 库和其他依赖
    │
    │  链接选项：
    │  -lpython3.11        # Python 库
    │  -lm                 # 数学库
    ▼
输出
    │
    ├─ Linux: mypackage/_core.cpython-311-x86_64-linux-gnu.so
    ├─ macOS: mypackage/_core.cpython-311-darwin.so
    └─ Windows: mypackage/_core.cp311-win_amd64.pyd
```

### 9.3 Python 扩展模块命名

扩展模块必须遵循特定命名规范：

```python
# Python 3.x 命名格式
{module_name}.cpython-{version}-{platform}.so     # Linux/macOS
{module_name}.cp{version}-{platform}.pyd           # Windows

# 示例
_core.cpython-311-x86_64-linux-gnu.so
_core.cpython-311-darwin.so
_core.cp311-win_amd64.pyd

# 稳定 ABI 命名（向后兼容）
_core.abi3-x86_64-linux-gnu.so
_core.abi3-win_amd64.pyd
```

### 9.4 setuptools Extension 配置

```python
from setuptools import setup, Extension

ext_modules = [
    Extension(
        'mypackage._core',                    # 扩展模块名
        sources=['src/core.c', 'src/utils.c'], # 源文件
        include_dirs=['include'],              # 头文件目录
        library_dirs=['libs'],                 # 库文件目录
        libraries=['m', 'hdf5'],              # 链接库
        define_macros=[('DEBUG', 1)],          # 预处理器宏
        undef_macros=['NDEBUG'],               # 取消宏定义
        extra_compile_args=['-O2', '-Wall'],   # 额外编译选项
        extra_link_args=['-L/usr/local/lib'],  # 额外链接选项
        depends=['include/core.h'],            # 依赖文件
        language='c',                          # 语言（c 或 c++）
    )
]

setup(
    name='mypackage',
    ext_modules=ext_modules,
)
```

### 9.5 Cython 扩展

```python
# setup.py with Cython
from setuptools import setup
from Cython.Build import cythonize

setup(
    name='mypackage',
    ext_modules=cythonize("mypackage/*.pyx"),
)
```

```cython
# mypackage/core.pyx
import numpy as np
cimport numpy as np

def process_data(np.ndarray[double, ndim=2] data):
    cdef int i, j
    cdef int rows = data.shape[0]
    cdef int cols = data.shape[1]
    cdef double total = 0.0

    for i in range(rows):
        for j in range(cols):
            total += data[i, j]

    return total
```

### 9.6 pybind11 扩展

```cpp
// src/core.cpp
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

double process_data(py::array_t<double> data) {
    auto buf = data.request();
    double *ptr = static_cast<double*>(buf.ptr);
    double total = 0.0;

    for (size_t i = 0; i < buf.size; i++) {
        total += ptr[i];
    }

    return total;
}

PYBIND11_MODULE(_core, m) {
    m.doc() = "Core processing module";
    m.def("process_data", &process_data, "Process data array");
}
```

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "pybind11>=2.10"]
build-backend = "setuptools.build_meta"
```

---

## 10. 跨平台分发策略

### 10.1 纯 Python 包

纯 Python 包最容易分发：

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "mypackage"
version = "1.0.0"
```

```bash
# 构建通用 wheel
python -m build --wheel
# 生成：mypackage-1.0.0-py3-none-any.whl
```

### 10.2 包含 C 扩展的包

包含 C 扩展的包需要为每个平台构建 wheel：

```bash
# 方法 1：本地构建
# 在每个平台上分别构建
python -m build --wheel

# 方法 2：使用 CI/CD
# GitHub Actions 示例
jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - name: Build wheel
        run: pip wheel . -w dist/
```

### 10.3 manylinux 构建

在 Linux 上构建兼容多发行版的 wheel：

```bash
# 使用 manylinux Docker 镜像
docker run --rm -v $(pwd):/io quay.io/pypa/manylinux2014_x86_64 \
    /io/build-wheels.sh

# build-wheels.sh
#!/bin/bash
for PYBIN in /opt/python/*/bin; do
    "${PYBIN}/pip" wheel /io/ -w /io/dist/
done

# 修复 wheel 标签
for whl in /io/dist/*.whl; do
    auditwheel repair "$whl" -w /io/dist/
done
```

### 10.4 cibuildwheel

cibuildwheel 是一个自动化跨平台构建工具：

```yaml
# .github/workflows/build.yml
name: Build

on: [push, pull_request]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      - uses: pypa/cibuildwheel@v2.16
        env:
          CIBW_BUILD: "cp39-* cp310-* cp311-* cp312-*"
          CIBW_SKIP: "*-musllinux_*"
      - uses: actions/upload-artifact@v4
        with:
          name: wheels
          path: ./wheelhouse/*.whl
```

### 10.5 发布到 PyPI

```bash
# 安装发布工具
pip install twine

# 构建 sdist 和 wheel
python -m build

# 上传到 TestPyPI（测试）
twine upload --repository testpypi dist/*

# 上传到 PyPI（正式）
twine upload dist/*
```

---

## 11. 现代打包工具链

### 11.1 构建工具对比

| 工具 | 构建 | 依赖管理 | 虚拟环境 | 特点 |
|------|------|----------|----------|------|
| **pip** | ❌ | ✅ | ❌ | 标准包管理器 |
| **build** | ✅ | ❌ | ✅ | PEP 517 构建前端 |
| **flit** | ✅ | ✅ | ❌ | 简单项目 |
| **poetry** | ✅ | ✅ | ✅ | 依赖锁定 |
| **pdm** | ✅ | ✅ | ✅ | PEP 582 |
| **hatch** | ✅ | ✅ | ✅ | 现代化，插件 |
| **uv** | ❌ | ✅ | ✅ | 极速 |

### 11.2 推荐工具链

#### 简单项目

```toml
# pyproject.toml
[build-system]
requires = ["flit_core>=3.4"]
build-backend = "flit_core.buildapi"

[project]
name = "mypackage"
version = "1.0.0"
dependencies = ["numpy>=1.20"]
```

#### 中型项目

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mypackage"
version = "1.0.0"
dependencies = ["numpy>=1.20"]

[tool.hatch.build.targets.wheel]
packages = ["src/mypackage"]
```

#### 包含 C 扩展的项目

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "pybind11>=2.10"]
build-backend = "setuptools.build_meta"

[project]
name = "mypackage"
version = "1.0.0"
dependencies = ["numpy>=1.20"]
```

### 11.3 项目结构最佳实践

```
mypackage/
├── pyproject.toml              # 项目配置
├── README.md                   # 项目说明
├── LICENSE                     # 许可证
├── CHANGELOG.md                # 变更日志
├── src/                        # 源码（src layout）
│   └── mypackage/
│       ├── __init__.py
│       ├── core.py
│       └── _core.pyi           # 类型存根
├── tests/                      # 测试
│   ├── test_core.py
│   └── conftest.py
├── docs/                       # 文档
│   └── ...
└── .github/                    # GitHub 配置
    └── workflows/
        └── build.yml
```

---

## 12. 常见问题与解决方案

### Q1: 为什么 pip 安装时需要编译？

**原因：** 包没有提供对应平台的预编译 wheel。

**解决方案：**

```bash
# 1. 检查是否有 wheel
pip index versions numpy
# 查看 Available files

# 2. 强制使用 wheel（如果失败则报错）
pip install --only-binary :all: numpy

# 3. 使用 conda 安装预编译包
mamba install numpy

# 4. 安装编译器
# Windows
pip install setuptools-rust
# 或安装 Visual Studio Build Tools

# Linux
sudo apt install build-essential python3-dev

# macOS
xcode-select --install
```

### Q2: 如何查看包的安装来源？

```bash
# 查看包的详细信息
pip show numpy
# 输出包含 Location: /path/to/site-packages

# 查看包的文件列表
pip show -f numpy

# 查看包的依赖树
pip show -r numpy
```

### Q3: wheel 和 egg 有什么区别？

| 特性 | wheel (.whl) | egg (.egg) |
|------|--------------|------------|
| 标准 | PEP 427 | setuptools 私有 |
| 格式 | ZIP | ZIP |
| 安装方式 | pip 原生支持 | easy_install |
| 运行时解压 | ❌ | ⚠️ 可能需要 |
| 状态 | ✅ 推荐 | ❌ 已弃用 |

### Q4: 如何构建平台特定的 wheel？

```bash
# 方法 1：在目标平台上构建
python -m build --wheel

# 方法 2：使用交叉编译
# 需要配置交叉编译工具链

# 方法 3：使用 cibuildwheel
pip install cibuildwheel
cibuildwheel --platform linux

# 方法 4：使用 manylinux Docker
docker run --rm -v $(pwd):/io quay.io/pypa/manylinux_2_28_x86_64 \
    bash -c "cd /io && /opt/python/cp311-cp311/bin/pip wheel . -w dist/"
```

### Q5: 如何减小 wheel 文件大小？

```bash
# 1. 排除不必要的文件
# pyproject.toml
[tool.setuptools.packages.find]
exclude = ["tests*", "docs*"]

# 2. 使用 .gitignore 规则排除
# MANIFEST.in
global-exclude *.pyc
global-exclude __pycache__
prune tests
prune docs

# 3. 压缩二进制文件
# Linux/macOS
strip mypackage/_core.so

# 4. 使用 UPX 压缩（可选）
upx --best mypackage/_core.so
```

### Q6: 如何调试构建过程？

```bash
# 1. 详细输出
pip install -v mypackage
python -m build --wheel --no-isolation

# 2. 保留构建目录
pip install --no-clean mypackage

# 3. 手动构建
python setup.py build_ext --inplace

# 4. 查看构建日志
pip install --log build.log mypackage
```

---

## 13. 参考资源

### 官方文档

- [Python 打包用户指南](https://packaging.python.org/)
- [PEP 427 - Wheel 格式](https://peps.python.org/pep-0427/)
- [PEP 517 - 构建系统接口](https://peps.python.org/pep-0517/)
- [PEP 518 - 构建系统声明](https://peps.python.org/pep-0518/)
- [PEP 621 - 项目元数据](https://peps.python.org/pep-0621/)
- [PEP 600 - manylinux 标准](https://peps.python.org/pep-0600/)
- [pip 官方文档](https://pip.pypa.io/en/stable/)
- [setuptools 文档](https://setuptools.pypa.io/)

### 工具文档

- [cibuildwheel](https://cibuildwheel.readthedocs.io/)
- [build](https://pypa-build.readthedocs.io/)
- [flit](https://flit.pypa.io/)
- [poetry](https://python-poetry.org/)
- [hatch](https://hatch.pypa.io/)
- [scikit-build-core](https://scikit-build-core.readthedocs.io/)

### 社区资源

- [Python Wheels](https://pythonwheels.com/)
- [Manylinux Docker 镜像](https://quay.io/repository/pypa/manylinux_2_28_x86_64)
- [PyPI](https://pypi.org/)
- [TestPyPI](https://test.pypi.org/)
