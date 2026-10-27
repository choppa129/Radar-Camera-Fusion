# Windows environment setup

The graphical application depends on the **Windows x64 ZLG CAN DLL** and has
been developed with **Python 3.10**. Conda commands below work from **Anaconda
Prompt**, regardless of where the repository is cloned.

## Install

1. Create/activate the environment:

   ```bat
   conda create -n fusion python=3.10 -y
   conda activate fusion
   ```

2. Install PyTorch 2.5.1 and torchvision 0.20.1. For NVIDIA CUDA 12.4:

   ```bat
   python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124
   ```

   On non-CUDA Windows machines, install the corresponding **CPU wheels**
   instead. The app can be slower on CPU; the GPU check in `tools/check_env.py`
   reports CUDA absence as a failure.

3. Install the remaining packages from the repository root:

   ```bat
   python -m pip install -r env\requirements.txt
   ```

4. Check the environment, then launch the GUI:

   ```bat
   python tools\check_env.py
   run.bat
   ```

## Hardware dependencies

- Camera: a connected USB camera, normally index 0.
- Radar: the project's 77 GHz radar and compatible ZLG USB-to-CAN interface.
- Vendor runtime: `driver/zlgcan.dll` **and** its accompanying
  `driver/kerneldlls/` directory. Keep them together.
- Calibration: `config/calibration_data.json` reflects the original
  test setup; real deployments require calibration for the actual camera and mount.

## Compatibility notes

| Package | Known development version | Reason |
| --- | --- | --- |
| Python | 3.10 x64 | Supported interpreter for the included Windows driver |
| PyTorch | 2.5.1 | Avoids the changed torch.load default in newer versions with Ultralytics 8.2.40 |
| torchvision | 0.20.1 | Matching PyTorch version |
| ultralytics | 8.2.40 | YOLOv8 inference and tracking |
| OpenCV | 4.10.0.84 | Frame acquisition, camera calibration and projection |
| PyQt5 | 5.15.11 | GUI and worker threads |
| NumPy | 1.26.4 | Known compatibility with the pinned stack |

The CI unit tests exercise the radar protocol only, using standard-library
modules and no physical hardware. They do **not** validate the camera model,
vendor driver or real-time performance.

## Non-hardware tests

```bat
python -m unittest discover -s tests -v
```
