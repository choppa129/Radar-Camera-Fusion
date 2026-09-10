# -*- coding: utf-8 -*-
"""
Fusion 项目自检脚本。

用法（在 fusion 环境里）:
    python F:\\Radar-Camera-Fusion\\tools\\check_env.py

检查内容：
    1. Python 位数与版本（zlgcan.dll 是 64 位，必须是 64 位解释器）
    2. 关键依赖能否导入（torch / opencv / PyQt5 / matplotlib / ultralytics / lapx）
    3. GPU 是否可用
    4. driver / models / config 下的必需文件是否都在
    5. CAN 驱动 dll 能否加载
    6. YOLO 权重能否加载并跑通一次推理
全部通过才会打印 ALL CHECKS PASSED。
"""

import os
import sys
import platform

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
sys.path.insert(0, SRC_DIR)

failures = []


def check(title, fn):
    try:
        detail = fn()
        print("[ OK ] %-28s %s" % (title, detail if detail else ""))
    except Exception as e:
        failures.append(title)
        print("[FAIL] %-28s %s: %s" % (title, type(e).__name__, e))


def check_python():
    bits = platform.architecture()[0]
    if bits != "64bit":
        raise RuntimeError("64-bit Python required, got %s" % bits)
    return "Python %s (%s)" % (sys.version.split()[0], bits)


def check_imports():
    import torch, cv2, numpy, matplotlib, PyQt5, ultralytics, lap
    return "torch %s | cv2 %s | numpy %s | ultralytics %s" % (
        torch.__version__, cv2.__version__, numpy.__version__, ultralytics.__version__)


def check_gpu():
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA not available - would fall back to CPU (much slower)")
    return torch.cuda.get_device_name(0)


def check_files():
    import paths
    missing = []
    for name in ("ZLG_DLL_PATH", "DEV_INFO_PATH", "KERNEL_DLLS_DIR",
                 "YOLO_MODEL_PATH", "CALIBRATION_PATH"):
        p = getattr(paths, name)
        if not os.path.exists(p):
            missing.append("%s -> %s" % (name, p))
    if missing:
        raise RuntimeError("missing file(s): " + "; ".join(missing))
    return "project root = %s" % paths.PROJECT_ROOT


def check_driver():
    import ctypes
    import paths
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(paths.DRIVER_DIR)
    dll = ctypes.WinDLL(paths.ZLG_DLL_PATH)
    if not hasattr(dll, "ZCAN_OpenDevice"):
        raise RuntimeError("dll loaded but ZCAN_OpenDevice not found")
    return "zlgcan.dll loaded (kerneldlls: %s)" % paths.KERNEL_DLLS_DIR


def check_model():
    from ultralytics import YOLO
    import numpy as np
    import paths
    model = YOLO(paths.YOLO_MODEL_PATH)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    results = model.track(source=frame, persist=True, verbose=False)
    return "yolov8n inference ok, %d box(es) on blank frame, %d classes" % (
        len(results[0].boxes), len(model.names))


if __name__ == "__main__":
    print("Fusion environment self-check\n" + "-" * 60)
    check("Python version/arch", check_python)
    check("Dependencies", check_imports)
    check("GPU", check_gpu)
    check("Project files", check_files)
    check("CAN driver", check_driver)
    check("YOLO model + inference", check_model)
    print("-" * 60)
    if failures:
        print("%d check(s) FAILED: %s" % (len(failures), ", ".join(failures)))
        sys.exit(1)
    print("ALL CHECKS PASSED")
