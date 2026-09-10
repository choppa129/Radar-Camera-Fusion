# CAN 驱动目录

这个目录来自周立功（ZLG）USBCANFD 驱动包，**不要拆开**：

- `zlgcan.dll`：上层 API 库，`src\zlgcan.py` 通过 ctypes 加载它；
- `kerneldlls\`：驱动的内核库（各型号设备的具体实现），`zlgcan.dll` 运行时会去加载它，
  因此必须与 dll 保持同级目录；
- `dev_info.json`：设备类型、通道数、波特率表，主程序据此填充界面下拉框。

代码侧的处理：`src\zlgcan.py` 在加载 dll 前会调用 `os.add_dll_directory(driver 目录)`，
把本目录加入 DLL 搜索路径，保证 `kerneldlls` 能被找到。路径统一由 `src\paths.py` 提供。

接上 CAN 盒后，可用 `python tools\zlgcan_demo.py` 单独验证驱动是否工作。
