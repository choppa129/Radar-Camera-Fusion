# Radar-Camera Fusion

**English** | [中文](#中文说明)

A radar–camera fusion system for object detection and velocity estimation.
YOLOv8 handles visual detection and tracking, while a mmWave radar supplies each
target's range and velocity. Radar points are projected onto the image plane with
the camera calibration and matched to the detection boxes by nearest neighbour,
so every box can be annotated with the radar-measured velocity.

## Repository layout

```
F:\Radar-Camera-Fusion\
├─ run.bat              one-click launcher (activates the conda env and starts the app)
├─ README.md            this file
├─ .gitignore
├─ src\                 source code
│   ├─ detect.py        main app (PyQt5 UI: video, radar scatter plot, control and calibration panels)
│   ├─ Camera.py        camera thread, YOLOv8 detection/tracking, projection + fusion, camera calibration
│   ├─ Radar.py         radar thread (polls targets from the CAN channel on a timer)
│   ├─ zlgcan.py        ZLG CAN driver wrapper (ctypes)
│   └─ paths.py         single source of truth for every path in the project
├─ driver\              ZLG CAN driver (keep together, do not split)
│   ├─ zlgcan.dll
│   ├─ kerneldlls\      driver kernel libraries, must stay in the same folder as zlgcan.dll
│   └─ dev_info.json    device types / channels / baud rate table
├─ models\              YOLO weights
│   └─ yolov8n.pt
├─ config\              calibration parameters
│   └─ calibration_data.json    intrinsics, distortion, radar-camera extrinsics R/tvec
├─ tools\               utilities
│   ├─ check_env.py     environment and path self-check
│   └─ zlgcan_demo.py   ZLG's official CAN demo GUI (test the CAN box without the camera)
├─ env\                 environment docs and dependency list
│   └─ requirements.txt
├─ data\                data (hymenoptera_data is the YOLO tutorial dataset, safe to delete)
├─ outputs\             runtime artefacts: logs\ (training logs), runs\ (inference output)
├─ docs\                documents
└─ archive\             non-essential: ultralytics-main source, old PyCharm config, old caches
```

## Environment

A conda environment named `fusion` is already set up on this machine
(`F:\anaconda3\envs\fusion`, Python 3.10.21, 64-bit). See [env/README.md](env/README.md)
for the install steps, version constraints and the commands needed to rebuild it from scratch.

Two hard requirements:

- a **64-bit** Python, because `driver\zlgcan.dll` is x64;
- **torch pinned to 2.5.x** — ultralytics 8.2.40 is incompatible with torch ≥ 2.6.

## Running

Double-click `run.bat`, or:

```
conda activate fusion
cd /d F:\Radar-Camera-Fusion
python src\detect.py
```

Run the self-check first if you want to verify the setup (it checks dependencies, GPU,
driver, model and calibration file):

```
python tools\check_env.py
```

## Hardware and workflow

- Camera: a USB webcam, index 0 in the code. Radar: a ZLG USBCANFD-series CAN box.
- In the UI: pick the device type and channel → open the device → start detection. The
  camera view is overlaid with detection boxes and radar velocities, and the radar point
  cloud is plotted on the right.
- Camera calibration: capture at least 10 images of an **11×8** inner-corner chessboard
  (the code assumes a square size of 3 — the unit is whatever you measured your squares
  in), then press 计算结果 (compute) followed by 保存 (save). Intrinsics and distortion
  coefficients are written to `config\calibration_data.json`.
- Radar calibration: adjust tvec until the projected radar points line up with the targets
  in the image, then press 保存 (save) to write the extrinsics R/tvec back to the same file.
- To test the CAN box without the camera, run `tools\zlgcan_demo.py`.

## Troubleshooting

- **No camera or radar connected**: the app still starts, but 打开设备 (open device) and
  开始检测 (start detection) will fail. That is expected.
- **PyCharm**: point the run configuration at `src\detect.py` and set the working directory
  to the project root `F:\Radar-Camera-Fusion`. The old `.idea` was moved to
  `archive\ide-config\`, so simply create a new run configuration.
- **Legacy absolute paths**: the code used to hard-code paths from an old machine
  (`C:\Users\94580\Desktop\prp\...`). Everything is derived from `src\paths.py` now, so the
  project works regardless of machine, folder or working directory.

---

# 中文说明

[English](#radar-camera-fusion) | **中文**

相机 + 毫米波雷达的目标检测与测速程序：YOLOv8 负责视觉检测与跟踪，
雷达提供目标的距离与速度；雷达点经相机标定参数投影到像素平面后，
与视觉检测框做最近邻匹配，把雷达速度补充到检测框上。

## 目录结构

```
F:\Radar-Camera-Fusion\
├─ run.bat              一键启动（激活 conda 环境并运行主程序）
├─ README.md            本文件
├─ .gitignore
├─ src\                 源代码
│   ├─ detect.py        主程序（PyQt5 界面：视频 + 雷达散点图 + 控制/标定面板）
│   ├─ Camera.py        相机线程、YOLOv8 检测跟踪、坐标投影与融合、相机标定
│   ├─ Radar.py         雷达线程（定时从 CAN 通道读取目标）
│   ├─ zlgcan.py        周立功 CAN 卡驱动封装（ctypes）
│   └─ paths.py         全部路径的统一出口，其余代码都从这里取路径
├─ driver\              周立功 CAN 驱动（打包在一起，不要拆开）
│   ├─ zlgcan.dll
│   ├─ kerneldlls\      驱动的内核库，必须与 zlgcan.dll 同目录
│   └─ dev_info.json    设备类型/通道/波特率配置
├─ models\              YOLO 权重
│   └─ yolov8n.pt
├─ config\              标定参数
│   └─ calibration_data.json    内参、畸变系数、雷达-相机外参 R/tvec
├─ tools\               辅助工具
│   ├─ check_env.py     环境与路径自检
│   └─ zlgcan_demo.py   周立功官方 CAN 调试界面（不接相机也能单独测 CAN）
├─ env\                 运行环境说明与依赖清单
│   └─ requirements.txt
├─ data\                数据（hymenoptera_data 为 YOLO 教程数据集，可删）
├─ outputs\             程序运行产物：logs\（训练日志）runs\（推理输出）
├─ docs\                文档
└─ archive\             非主线内容：ultralytics-main 源码、旧 PyCharm 配置、旧缓存
```

## 环境

已在本机创建好 conda 环境 `fusion`（位置 `F:\anaconda3\envs\fusion`，Python 3.10.21，64 位）。
安装步骤、版本约束和从零复现的命令见 [env/README.md](env/README.md)。

两点硬性要求：

- 必须是 **64 位** Python，`driver\zlgcan.dll` 是 x64 的；
- **torch 固定在 2.5.x**，ultralytics 8.2.40 与 torch ≥ 2.6 不兼容。

## 运行

双击 `run.bat`，或者：

```
conda activate fusion
cd /d F:\Radar-Camera-Fusion
python src\detect.py
```

运行前可先自检（会检查依赖、GPU、驱动、模型、标定文件）：

```
python tools\check_env.py
```

## 硬件与操作流程

- 相机：USB 摄像头，代码中索引 0；雷达：周立功 USBCANFD 系列 CAN 盒。
- 界面上选设备类型和通道 → 打开设备 → 开始检测：相机画面叠加检测框与雷达速度，右侧是雷达点云散点图。
- 相机标定：用 **11×8** 内角点棋盘拍摄 ≥10 张（代码里方格尺寸按 3 计算，单位取决于你实测时的方格边长），点「计算结果」再「保存」，内参与畸变系数写入 `config\calibration_data.json`。
- 雷达标定：调整 tvec 使雷达点投影与画面目标对齐，点「保存」把外参 R/tvec 写回同一文件。
- 只测 CAN 不测相机时，可直接跑 `tools\zlgcan_demo.py`。

## 常见问题

- **没有接相机/雷达时**：程序能启动，但「打开设备」「开始检测」会失败，这是正常的。
- **PyCharm**：运行配置指向 `src\detect.py`，工作目录设为项目根目录 `F:\Radar-Camera-Fusion`；旧的 `.idea` 已移入 `archive\ide-config\`，重新打开工程后新建运行配置即可。
- **历史的绝对路径**：代码原先硬编码了旧电脑的 `C:\Users\94580\Desktop\prp\...`，现已全部改为由 `src\paths.py` 推算，换机器、换目录、换工作目录都不受影响。
