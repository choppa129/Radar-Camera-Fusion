# 运行环境说明

本机现有环境：conda 环境名 `fusion`，位置 `F:\anaconda3\envs\fusion`，
Python 3.10.21（64 位），PyTorch 2.5.1 + CUDA 12.4，GPU 为 RTX 3050 Ti Laptop。

## 从零复现（三步）

```bat
:: 1) 建环境（必须 64 位 Python）
F:\anaconda3\Scripts\conda.exe create -p F:\anaconda3\envs\fusion python=3.10 pip -y

:: 2) 装 GPU 版 PyTorch（CUDA 12.4，约 2.5 GB）
F:\anaconda3\envs\fusion\python.exe -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124

:: 3) 装其余依赖
F:\anaconda3\envs\fusion\python.exe -m pip install -r F:\Radar-Camera-Fusion\env\requirements.txt
```

装完运行自检确认：

```bat
F:\anaconda3\envs\fusion\python.exe F:\Radar-Camera-Fusion\tools\check_env.py
```

## 版本约束（不要随意升级）

| 组件 | 版本 | 原因 |
| --- | --- | --- |
| torch / torchvision | 2.5.1 / 0.20.1 (+cu124) | torch ≥ 2.6 把 `torch.load` 默认值改成 `weights_only=True`，与 ultralytics 8.2.40 不兼容，加载权重会报错 |
| ultralytics | 8.2.40 | 与项目内原有 YOLOv8 源码（archive\ultralytics-main）同版本，行为一致 |
| lapx | 0.5.2+ | `model.track()` 跟踪必需；Ultralytics 的自动安装可能装到别的解释器里，务必手动确认装进本环境 |
| numpy | 1.26.4 | 与 torch 2.5.1、opencv 4.10、ultralytics 8.2.40 组合最稳；不要升到 2.x |
| PyQt5 | 5.15.11 | matplotlib 的 Qt5Agg 后端依赖它绘制雷达散点图 |
| opencv-python | 4.10.0.84 | 相机读取、去畸变、投影与绘图 |
