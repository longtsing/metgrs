---
layout: default
title: Matplotlib 中文显示配置教程
description: 在 Windows、Linux、macOS 上配置 Matplotlib 显示中文的完整教程
---

# Matplotlib 中文显示配置教程（Windows / Linux / macOS）

## 1. 问题描述

默认情况下，matplotlib 不支持显示中文字体，绘图时中文会显示为方框（□□□）或乱码。

### 问题示例

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.set_title("温度变化图")
ax.set_xlabel("时间（小时）")
ax.set_ylabel("温度（℃）")
plt.show()
```

**预期效果**：标题和坐标轴标签正常显示中文

**实际效果**：中文被替换为方框 □□□□□

---

## 2. 解决方案概览

| 方案 | 适用场景 | 持久性 | 复杂度 |
|------|----------|--------|--------|
| 临时设置（代码内） | 单个脚本 | 临时 | 简单 |
| 修改 matplotlibrc | 所有脚本 | 永久 | 中等 |
| 安装字体 + 配置 | 所有脚本 | 永久 | 中等 |

---

## 3. 方案一：代码内临时设置（最简单）

### 3.1 Windows 系统

Windows 自带微软雅黑字体，直接使用：

```python
import matplotlib.pyplot as plt
import matplotlib

# 设置中文字体
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 测试
fig, ax = plt.subplots()
ax.set_title("中文测试：你好，世界！")
ax.set_xlabel("横轴")
ax.set_ylabel("纵轴")
ax.text(0.5, 0.5, '中文字体测试', fontsize=20, ha='center', va='center', transform=ax.transAxes)
plt.show()
```

### 3.2 Linux / macOS 系统

需要先安装中文字体，然后使用：

```python
import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

# 查看系统中可用的中文字体
for f in fm.fontManager.ttflist:
    if 'CJK' in f.name or 'Noto' in f.name or 'WenQuanYi' in f.name or 'SimHei' in f.name:
        print(f.name, f.fname)

# 设置中文字体（根据实际可用字体选择）
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots()
ax.set_title("中文测试：你好，世界！")
plt.show()
```

### 3.3 使用 context manager（推荐）

如果不想影响其他代码，可以使用 `with` 语句：

```python
import matplotlib.pyplot as plt
import matplotlib

with plt.rc_context({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Microsoft YaHei'],
    'axes.unicode_minus': False
}):
    fig, ax = plt.subplots()
    ax.set_title("中文标题")
    plt.show()
```

---

## 4. 方案二：永久修改 matplotlibrc 配置文件

### 4.1 找到配置文件路径

```python
import matplotlib
print(matplotlib.matplotlib_fname())
# 输出类似：/path/to/matplotlib/mpl-data/matplotlibrc
```

### 4.2 Windows 系统

#### 方法 1：Python 脚本自动修改

```python
import re
import shutil
from pathlib import Path
import matplotlib

# 1. 找到配置文件
mpl_rc = Path(matplotlib.get_data_path()) / 'matplotlibrc'
print(f"配置文件路径: {mpl_rc}")

# 2. 备份原文件
bak = mpl_rc.with_suffix('.bak')
if not bak.exists():
    shutil.copy2(mpl_rc, bak)
    print(f"备份文件: {bak}")

# 3. 读取并修改
text = mpl_rc.read_text(encoding='utf-8')

# 移除已有的中文字体配置（避免重复）
text = re.sub(r'Microsoft YaHei,\s*', '', text, flags=re.IGNORECASE)

# 在 DejaVu Sans 前面添加 Microsoft YaHei
text = re.sub(r'(\bDejaVu Sans,\s*)', r'Microsoft YaHei, \1', text, flags=re.IGNORECASE)

# 修复负号显示
text = text.replace('#axes.unicode_minus  : True', 'axes.unicode_minus  : False')

# 4. 写回
mpl_rc.write_text(text, encoding='utf-8')
print("配置已更新！")

# 5. 清除字体缓存
import matplotlib.font_manager as fm
fm._load_fontmanager(try_read_cache=False)
```

#### 方法 2：手动编辑

1. 找到 `matplotlibrc` 文件
2. 用文本编辑器打开
3. 找到 `font.sans-serif` 行，添加 `Microsoft YaHei`：
   ```
   font.sans-serif : Microsoft YaHei, DejaVu Sans, Bitstream Vera Sans, ...
   ```
4. 找到 `axes.unicode_minus` 行，改为：
   ```
   axes.unicode_minus  : False
   ```
5. 保存文件

### 4.3 Linux 系统

```bash
# 1. 安装中文字体
# Ubuntu/Debian:
sudo apt install fonts-noto-cjk
# CentOS/RHEL:
sudo yum install google-noto-sans-cjk-ttc-fonts
# 或使用 conda:
conda install -c conda-forge font-ttf-noto-cjk

# 2. 找到 matplotlibrc 路径
python -c "import matplotlib; print(matplotlib.matplotlib_fname())"

# 3. 使用 sed 修改配置
MPL_RC=$(python -c "import matplotlib; print(matplotlib.matplotlib_fname())")
sed -i 's/DejaVu Sans,/Noto Sans CJK SC, DejaVu Sans,/g' "$MPL_RC"
sed -i 's/#axes.unicode_minus  : True/axes.unicode_minus  : False/' "$MPL_RC"

# 4. 清除缓存
rm -rf ~/.cache/matplotlib
```

### 4.4 macOS 系统

```bash
# 1. 安装中文字体
# macOS 自带 "PingFang SC"（苹方）字体
# 或使用 Homebrew 安装 Noto 字体：
brew install --cask font-noto-sans-cjk

# 2. 找到 matplotlibrc 路径
python -c "import matplotlib; print(matplotlib.matplotlib_fname())"

# 3. 修改配置
MPL_RC=$(python -c "import matplotlib; print(matplotlib.matplotlib_fname())")
# macOS 使用 PingFang SC
sed -i '' 's/DejaVu Sans,/PingFang SC, DejaVu Sans,/g' "$MPL_RC"
sed -i '' 's/#axes.unicode_minus  : True/axes.unicode_minus  : False/' "$MPL_RC"

# 4. 清除缓存
rm -rf ~/.matplotlib
```

---

## 5. 方案三：使用 Conda 安装字体 + 配置（推荐）

### 5.1 安装字体

```bash
# 安装 Noto CJK 字体（跨平台通用）
conda install -c conda-forge font-ttf-noto-cjk -y

# 安装 cartopy 离线地图数据（可选）
conda install -c conda-forge cartopy_offlinedata -y
```

### 5.2 Python 脚本自动配置

```python
import os
import matplotlib
import matplotlib.font_manager as fm
from pathlib import Path

# 1. 定位 Conda 环境的 fonts 目录
conda_prefix = Path(os.environ.get("CONDA_PREFIX", ""))
if not conda_prefix:
    raise RuntimeError("请激活 Conda 环境后再运行！")

# Windows 与 Unix 路径差异
if os.name == "nt":          # Windows
    fonts_dir = conda_prefix / "fonts"
else:                        # Linux / macOS
    fonts_dir = conda_prefix / "share" / "fonts"

# 2. 找到 Noto CJK 字体文件
noto_files = []
for ext in ("*.ttf", "*.ttc", "*.otf"):
    noto_files.extend(fonts_dir.glob(ext))

noto_files = [f for f in noto_files if "noto" in f.name.lower() and "cjk" in f.name.lower()]
if not noto_files:
    raise FileNotFoundError(f"在 {fonts_dir} 下找不到 Noto CJK 字体！")

print(f"找到字体文件: {noto_files}")

# 3. 注册到 Matplotlib
for fp in noto_files:
    fm.fontManager.addfont(str(fp))

# 4. 设置默认中文字体
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Noto Sans CJK SC']
matplotlib.rcParams['axes.unicode_minus'] = False

# 5. 验证
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.set_title("中文测试：你好，世界！")
ax.set_xlabel("横轴")
ax.set_ylabel("纵轴")
ax.text(0.5, 0.5, '中文字体测试', fontsize=20, ha='center', va='center', transform=ax.transAxes)
plt.show()
```

---

## 6. 各平台推荐字体

### 6.1 常用中文字体

| 字体名称 | 平台 | 说明 |
|----------|------|------|
| `Microsoft YaHei` | Windows | 微软雅黑，Windows 自带 |
| `SimHei` | Windows | 黑体，Windows 自带 |
| `SimSun` | Windows | 宋体，Windows 自带 |
| `PingFang SC` | macOS | 苹方，macOS 自带 |
| `STHeiti` | macOS | 华文黑体，macOS 自带 |
| `Noto Sans CJK SC` | 全平台 | Google Noto 字体，需安装 |
| `WenQuanYi Micro Hei` | Linux | 文泉驿微米黑，需安装 |
| `Source Han Sans SC` | 全平台 | 思源黑体，需安装 |

### 6.2 字体安装方法

#### Windows

```bash
# Noto 字体（推荐）
conda install -c conda-forge font-ttf-noto-cjk -y

# 或手动安装：
# 1. 下载字体文件
# 2. 右键 → 为所有用户安装
```

#### Linux

```bash
# Ubuntu/Debian
sudo apt install fonts-noto-cjk fonts-wqy-microhei

# CentOS/RHEL
sudo yum install google-noto-sans-cjk-ttc-fonts wqy-microhei-fonts

# 或使用 conda
conda install -c conda-forge font-ttf-noto-cjk -y
```

#### macOS

```bash
# macOS 自带 PingFang SC，无需额外安装
# 如需安装 Noto 字体：
brew install --cask font-noto-sans-cjk

# 或使用 conda
conda install -c conda-forge font-ttf-noto-cjk -y
```

---

## 7. 验证配置

### 7.1 查看可用字体

```python
import matplotlib.font_manager as fm

# 列出所有中文字体
for f in fm.fontManager.ttflist:
    if any(keyword in f.name for keyword in ['CJK', 'Hei', 'Song', 'YaHei', 'PingFang', 'Noto', 'WenQuanYi']):
        print(f"字体名: {f.name}")
        print(f"  文件: {f.fname}")
        print()
```

### 7.2 测试中文显示

```python
import matplotlib.pyplot as plt
import matplotlib

# 设置字体
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'Noto Sans CJK SC', 'PingFang SC']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建测试图
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# 左图：简单折线图
ax1 = axes[0]
ax1.plot([1, 2, 3, 4], [1, 4, 2, 3])
ax1.set_title("温度变化图")
ax1.set_xlabel("时间（小时）")
ax1.set_ylabel("温度（℃）")

# 右图：散点图
ax2 = axes[1]
ax2.scatter([1, 2, 3, 4, 5], [2, 4, 1, 5, 3])
ax2.set_title("观测数据分布")
ax2.set_xlabel("高度（米）")
ax2.set_ylabel("风速（米/秒）")

plt.tight_layout()
plt.savefig("chinese_test.png", dpi=150, bbox_inches='tight')
plt.show()
print("测试图片已保存为 chinese_test.png")
```

---

## 8. 常见问题

### Q1: 设置后仍然显示方框

**解决方案**：
1. 清除 matplotlib 字体缓存：
   ```bash
   # 查看缓存位置
   python -c "import matplotlib; print(matplotlib.get_cachedir())"
   
   # 删除缓存目录
   rm -rf ~/.cache/matplotlib          # Linux
   rm -rf ~/.matplotlib                # macOS
   # Windows: 删除 %USERPROFILE%\.matplotlib 目录
   ```

2. 重启 Python 进程

3. 确认字体名称正确（区分大小写）

### Q2: 负号显示为方框

这是因为 matplotlib 默认使用 Unicode 负号（U+2212），而某些字体不包含该字符。

```python
matplotlib.rcParams['axes.unicode_minus'] = False  # 使用 ASCII 减号
```

### Q3: Linux 服务器上没有图形界面

```python
# 使用非交互式后端
import matplotlib
matplotlib.use('Agg')  # 必须在 import plt 之前设置
import matplotlib.pyplot as plt

# 正常绘图，使用 savefig 保存
fig, ax = plt.subplots()
ax.set_title("中文标题")
plt.savefig("output.png", dpi=150, bbox_inches='tight')
```

### Q4: Jupyter Notebook 中设置不生效

在 Notebook 的**第一个 Cell**中设置：

```python
%matplotlib inline
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False
```

### Q5: 如何恢复默认配置

```python
import matplotlib
matplotlib.rcdefaults()  # 恢复所有默认设置
```

或者删除自定义配置文件，使用备份文件恢复：

```bash
# 找到配置文件
python -c "import matplotlib; print(matplotlib.matplotlib_fname())"

# 用备份文件恢复
cp matplotlibrc.bak matplotlibrc
```

---

## 9. 参考资源

- [matplotlib 字体管理官方文档](https://matplotlib.org/stable/users/explain/text/fonts.html)
- [matplotlib 配置文件说明](https://matplotlib.org/stable/users/explain/customizing.html)
- [Google Noto 字体项目](https://fonts.google.com/noto)
- [文泉驿字体项目](http://wenq.org/)
- [思源字体项目](https://github.com/adobe-fonts/source-han-sans)
