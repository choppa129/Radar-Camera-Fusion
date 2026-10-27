# Camera–Radar Fusion for Field-Robot Perception

A **77 GHz mmWave radar + monocular camera** perception prototype for robots operating in outdoor field environments. YOLOv8 detects objects in camera images; radar supplies range and velocity measurements. A calibrated geometric projection and nearest-neighbor association join the two modalities so that image detections can display radar-derived motion estimates.

**Python · YOLOv8 · OpenCV · 77 GHz radar · CAN/CAN FD · PyQt5 · NumPy**

[English](#overview) · [中文简介](#中文简介) · [Personal portfolio](https://choppa129.github.io/projects/radar-camera-fusion/)

## Overview

| | |
| --- | --- |
| **Problem** | RGB cameras recognize objects but do not directly measure object range or radial velocity. Radar adds motion and depth information under challenging outdoor conditions. |
| **Approach** | Decision-level fusion: YOLOv8 detections + decoded radar target measurements + extrinsic projection into the image plane. |
| **Association** | Nearest projected radar return to a detection-box center, with a configurable **100 px** maximum-distance gate in the current implementation. |
| **Display** | Live camera detections and optional radar velocity labels, alongside a radar scatter plot and calibration controls. |
| **Experiment context** | Field-robot evaluation explored targets within roughly **±5 m laterally** and **12 m forward**, depending on the test arrangement. |
| **Important timing note** | Camera acquisition is **scheduled** at a 33 ms timer interval. This is **not** a measured 30 FPS end-to-end fusion throughput claim. |

## Processing pipeline

1. **Camera & detection:** obtain USB-camera frames and run the YOLOv8n detector/tracker.
2. **Radar transport:** read CAN/CAN-FD frames using the ZLG interface. A `0x60A` header starts a scan and `0x60B` records contain target information.
3. **Radar decoding:** convert packed fields into lateral/forward coordinates and radial velocity.
4. **Calibration:** use camera intrinsics, lens distortion and radar-to-camera extrinsics to project radar targets into image coordinates. Normal detection uses undistorted camera frames, so its radar projection uses corresponding undistorted coordinates.
5. **Association:** find the nearest projected radar point to each YOLO bounding-box center. If the pixel distance is inside the gate, append that radar target's velocity; otherwise show **Unknown**.
6. **Visualization:** display the annotated video and a radar-space plot within the PyQt5 GUI.

This is a **decision-level sensor fusion baseline**, not a learned end-to-end fusion model. Association is spatial-only; the current pipeline does not implement explicit multi-sensor clock synchronization, temporal filtering or uncertainty-weighted data association.

## Technical contributions

- Integrated an image detector/tracker with a real mmWave radar receive path for field-robot perception.
- Implemented camera calibration, radar-frame decoding and radar-to-image coordinate projection.
- Built a PyQt5 interface for live detections, radar scatter plots, sensor setup and interactive calibration.
- Separated radar packet decoding from the device driver so core math and split-packet handling can be regression-tested without hardware.

## Reproducing the project

**Required for the full demo:** Windows x64, Python 3.10, a supported ZLG USB-to-CAN device with its vendor runtime, the radar and a USB camera. A discrete NVIDIA GPU is recommended but not required for the program logic. The included calibration file corresponds to the original device arrangement; **recalibrate for any different camera, lens, resolution or sensor mounting**.

Open **Anaconda Prompt** in a clone of the repository:

```bat
git clone https://github.com/choppa129/Radar-Camera-Fusion.git
cd Radar-Camera-Fusion
conda create -n fusion python=3.10 -y
conda activate fusion
python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124
python -m pip install -r env\requirements.txt
python tools\check_env.py
run.bat
```

The PyTorch command above installs **CUDA 12.4 wheels**. See [env/README.md](env/README.md) for alternatives, package compatibility and environment checks. Run from the repository root; `run.bat` no longer assumes an `F:` installation directory.

### Test the protocol without sensors

```sh
python -m unittest discover -s tests -v
```

These unit tests cover packed radar values, CAN versus CAN-FD frame lengths, truncated packets and scan assembly across multiple receive batches. They **do not** replace physical-device integration tests.

## Calibration

**Camera intrinsics:** capture at least 10 chessboard observations using the **11 × 8 inner-corner** pattern expected by the current implementation. The board's physical square size must match the value used in `src/Camera.py` (currently the value `3`, in the chosen physical unit). For a different board, update the size and rerun calibration.

**Radar extrinsics:** adjust the radar-to-camera translation and ensure points align with camera observations. The calibration file stores `R`, `tvec`, camera matrix and lens distortion. Verify axis directions and velocity signs using a target with known motion before relying on measurements.

## Repository map

```text
Radar-Camera-Fusion/
├── src/
│   ├── detect.py           # PyQt5 UI and device controls
│   ├── Camera.py           # capture, YOLO tracking, calibration, fusion
│   ├── Radar.py            # CAN receive loop and worker
│   ├── radar_protocol.py   # hardware-independent packet decoder
│   ├── zlgcan.py           # vendor DLL ctypes wrapper
│   └── paths.py            # repository-relative resource paths
├── tests/                  # pure-Python protocol regression tests
├── config/                 # sample calibration values
├── driver/                 # ZLG driver and companion DLL assets
├── models/yolov8n.pt       # existing YOLOv8n weights
├── env/                    # installation guide and pinned dependencies
├── tools/check_env.py      # hardware/software environment check
└── run.bat                 # Windows launcher
```

## Limitations & next steps

- **Hardware verification:** the automated tests cannot verify USB camera capture, DLL loading or on-site CAN communication.
- **Data association:** the current 100 px matching threshold is heuristic. A useful next experiment is calibrated gating with 3D uncertainty and time synchronization.
- **Field performance:** no precision/recall, velocity RMSE, latency percentiles or real FPS benchmark is provided here without a reproducible evaluation dataset.
- **Visual evidence:** add an actual field test photograph or UI screenshot when available. No synthetic experiment screenshots or AI-generated images are used.
- **Vendor code:** files in `driver/` include third-party DLLs; verify upstream redistribution/licensing terms before repackaging them.

## 中文简介

本项目面向**田间作业机器人**的感知需求，将 **YOLOv8 相机目标检测**与 **77 GHz 毫米波雷达测距、测速**结合。雷达 CAN 数据解码后，经相机标定参数投影至图像坐标系，并使用 **100 像素门控的最近邻匹配**为检测框补充雷达速度信息。PyQt5 界面展示视频、雷达点云及标定控制。

项目包含真实硬件使用的代码路径。新增的协议单元测试可在没有雷达的电脑上运行，但**不能替代真实硬件联调**。代码中的 33 ms 是相机定时器设定值，不代表已测得的完整融合流水线帧率。

有关环境配置，详见 [env/README.md](env/README.md)；项目介绍也收录于 [个人作品集](https://choppa129.github.io/projects/radar-camera-fusion/)。
