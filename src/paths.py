# -*- coding: utf-8 -*-
"""
Fusion 项目统一路径定义。

所有路径都由本文件的位置推算，因此无论从哪个目录启动程序都能正确定位，
不再依赖硬编码的绝对路径，也不依赖当前工作目录。

目录约定（详见项目根目录 README.md）:
    src\      源代码
    driver\   周立功 CAN 驱动（zlgcan.dll + kerneldlls，两者必须同目录）
    models\   YOLO 权重
    config\   标定参数
    data\     采集/训练数据
    outputs\  程序运行产物
"""

import os

SRC_DIR      = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)

DRIVER_DIR  = os.path.join(PROJECT_ROOT, "driver")
MODELS_DIR  = os.path.join(PROJECT_ROOT, "models")
CONFIG_DIR  = os.path.join(PROJECT_ROOT, "config")
DATA_DIR    = os.path.join(PROJECT_ROOT, "data")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")

# 周立功 CAN 驱动
ZLG_DLL_PATH    = os.path.join(DRIVER_DIR, "zlgcan.dll")
KERNEL_DLLS_DIR = os.path.join(DRIVER_DIR, "kerneldlls")
DEV_INFO_PATH   = os.path.join(DRIVER_DIR, "dev_info.json")

# 模型与标定参数
YOLO_MODEL_PATH  = os.path.join(MODELS_DIR, "yolov8n.pt")
CALIBRATION_PATH = os.path.join(CONFIG_DIR, "calibration_data.json")
