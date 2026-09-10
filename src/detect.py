import sys
import os
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QGroupBox,QComboBox,QMessageBox,QDoubleSpinBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QThread, QTimer
from zlgcan import *
import json
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import Radar
import Camera
import paths

MAX_RCV_NUM     = 10

USBCANFD_TYPE    = (41, 42, 43)
USBCAN_XE_U_TYPE = (20, 21, 31)
USBCAN_I_II_TYPE = (3, 4)

img_size=(640, 480)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("目标检测")

        # 相机
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(img_size[0],img_size[1])

        # 雷达
        self.DeviceInit()

        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        # 创建一个子图
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title('Radar Data Visualization')
        self.ax.set_xlabel('X (units)')
        self.ax.set_ylabel('Y (units)')
        self.ax.set_xlim(-5, 5)  # 设置 x 轴范围
        self.ax.set_ylim(0, 12)  # 设置 y 轴范围

        # 创建一个散点图
        self.scatter = self.ax.scatter([], [], c='blue', label='Radar Data')
        self.annotations=[]

        self._dev_info = None
        # 设备信息文件：项目内 driver/dev_info.json（由 src/paths.py 统一定义）
        with open(paths.DEV_INFO_PATH, "r") as fd:
            self._dev_info = json.load(fd)
        if self._dev_info == None:
            print("device info no exist!")
            return

        self.DeviceInfoInit()
        self.initUI()
        self.ChnInfoUpdate(self._isOpen)

    def initUI(self):
        up_layout=QHBoxLayout()
        up_layout.addWidget(self.ControlWidget())
        up_layout.addWidget(self.RadarConnectWidgets())
        up_layout.addWidget(self.CameraCalibrationWidget())
        bottom_layout=QHBoxLayout()
        bottom_layout.addWidget(self.video_label)
        bottom_layout.addWidget(self.canvas)
        main_layout = QVBoxLayout()
        main_layout.addLayout(up_layout)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def DeviceInit(self):
        self.Cam_isOpen =False

        self._zcan       = ZCAN()
        self._dev_handle = INVALID_DEVICE_HANDLE
        self._can_handle = INVALID_CHANNEL_HANDLE

        self._isOpen = False
        self._isChnOpen = False

        #current device info
        self._is_canfd = False
        self._res_support = False

    def DeviceInfoInit(self):
        self.cmbDevType=QComboBox()
        self.cmbDevType.addItems(tuple([dev_name for dev_name in self._dev_info]))
        self.cmbDevType.setCurrentIndex(0)

    def ControlWidget(self):
        control_widget=QGroupBox("控制")
        control_layout=QVBoxLayout()
        self.btnCtrl=QPushButton('开始检测',self)
        self.btnCtrl.clicked.connect(self.BtnOpenCAN_Click)
        self.btnCtrl.setEnabled(False)
        control_layout.addWidget(self.btnCtrl)
        control_widget.setLayout(control_layout)
        return control_widget

    def RadarConnectWidgets(self):
        Radar=QGroupBox("设备选择")
        Radar_layout=QVBoxLayout()
        Radar_layout.addWidget(QLabel("设备类型"))
        Radar_layout.addWidget(self.cmbDevType)
        Radar_layout.addWidget(QLabel("设备索引"))
        self.cmbDevIdx=QComboBox()
        self.cmbDevIdx.addItems([str(i) for i in range(4)])
        self.cmbDevIdx.setCurrentIndex(0)
        Radar_layout.addWidget(self.cmbDevIdx)
        self.btnDevCtrl=QPushButton("打开设备")
        self.btnDevCtrl.clicked.connect(self.BtnOpenDev_Click)
        Radar_layout.addWidget(self.btnDevCtrl)
        Radar_layout.addWidget(QLabel("CAN通道"))
        self.cmbCANChn=QComboBox()
        Radar_layout.addWidget(self.cmbCANChn)
        Radar_layout.addWidget(QLabel("波特率"))
        self.cmbBaudrate=QComboBox()
        Radar_layout.addWidget(self.cmbBaudrate)
        Radar.setLayout(Radar_layout)
        return Radar

    def CameraCalibrationWidget(self):
        Calibration=QGroupBox("标定")
        self.btnCal=QPushButton("相机标定")
        self.btnCal.clicked.connect(self.camera_calibration)
        self.chess_capture=QPushButton("捕捉棋盘")
        self.chess_capture.setEnabled(False)
        self.result_calibration=QPushButton("计算结果")
        self.result_calibration.setEnabled(False)
        self.save_calibration=QPushButton("保存")
        self.save_calibration.setEnabled(False)
        self.btnCalibration=QPushButton("雷达标定")
        self.btnCalibration.clicked.connect(self.radar_calibration)
        self.btnCalibration.setEnabled(False)
        self.save_calibration1=QPushButton("保存")
        self.save_calibration1.setEnabled(False)
        self.x=QDoubleSpinBox(self)
        self.x.setRange(-100.00, 100.00)
        self.y=QDoubleSpinBox(self)
        self.y.setRange(-100.00, 100.00)
        self.z=QDoubleSpinBox(self)
        self.z.setRange(-100.00, 100.00)
        self.x.setEnabled(False)
        self.y.setEnabled(False)
        self.z.setEnabled(False)

        layout1=QHBoxLayout()
        layout1.addWidget(self.chess_capture)
        layout1.addWidget(self.result_calibration)
        layout1.addWidget(self.save_calibration)

        layout2 = QHBoxLayout()
        layout2.addWidget(self.x)
        layout2.addWidget(self.y)
        layout2.addWidget(self.z)

        Calibration_layout = QVBoxLayout()
        Calibration_layout.addWidget(self.btnCal)
        Calibration_layout.addLayout(layout1)
        Calibration_layout.addWidget(self.btnCalibration)
        Calibration_layout.addWidget(self.save_calibration1)
        Calibration_layout.addLayout(layout2)
        Calibration.setLayout(Calibration_layout)
        return Calibration
###
###函数
    def ChnInfoUpdate(self, is_open):
        # 通道信息获取
        cur_dev_info = self._dev_info[self.cmbDevType.currentText()]
        cur_chn_info = cur_dev_info["chn_info"]

        if is_open:
            # 通道
            self.cmbCANChn.addItems(tuple([str(i) for i in range(cur_dev_info["chn_num"])]))
            self.cmbCANChn.setCurrentIndex(0)
            self.cmbCANChn.setEnabled(True)
            # 只听模式
            self.cmbCANMode=0

            # 波特率
            self.cmbBaudrate.addItems(tuple([brt for brt in cur_chn_info["baudrate"].keys()]))
            self.cmbBaudrate.setCurrentIndex(self.cmbBaudrate.count() - 1)
            self.cmbBaudrate.setEnabled(True)

            if cur_chn_info["is_canfd"] == True:
                # 数据域波特率
                self.cmbDataBaudrate_tuple = tuple([brt for brt in cur_chn_info["data_baudrate"].keys()])
                self.cmbDataBaudrate = self.cmbDataBaudrate_tuple[0]

            if cur_chn_info["sf_res"] == True:
                self.cmbResEnable= 0

            self.btnCtrl.setEnabled(True)
        else:
            self.cmbCANChn.setEnabled(False)
            self.cmbBaudrate.setEnabled(False)

            self.btnCtrl.setEnabled(False)

###
###事件
    def BtnOpenDev_Click(self):
        if self._isOpen:
            # Close Channel
            if self._isChnOpen:
                self.btnCtrl.click()
            # Close Device
            self._zcan.CloseDevice(self._dev_handle)

            self.btnDevCtrl.setText("打开设备")
            self.cmbDevType.setEnabled(True)
            self.cmbDevIdx.setEnabled(True)
            self.btnCalibration.setEnabled(False)
            self._isOpen = False
        else:
            self._cur_dev_info = self._dev_info[self.cmbDevType.currentText()]

            # Open Device
            self._dev_handle = self._zcan.OpenDevice(self._cur_dev_info["dev_type"],
                                                     self.cmbDevIdx.currentIndex(), 0)
            if self._dev_handle == INVALID_DEVICE_HANDLE:
                # Open failed
                QMessageBox.critical(self,"打开设备","打开设备失败")
                return


            self._is_canfd = self._cur_dev_info["chn_info"]["is_canfd"]
            self._res_support = self._cur_dev_info["chn_info"]["sf_res"]

            self.btnDevCtrl.setText("关闭设备")
            self.cmbDevType.setEnabled(False)
            self.cmbDevIdx.setEnabled(False)
            self.btnCalibration.setEnabled(True)
            self._isOpen = True
        self.ChnInfoUpdate(self._isOpen)

    def BtnOpenCAN_Click(self):
        if self._isChnOpen:
            # Close channel
            self.stop_radar()
            self.stop_camera()
            self._zcan.ResetCAN(self._can_handle)
            self.btnCal.setEnabled(True)
            self.btnCalibration.setEnabled(True)
            self.btnCtrl.setText("开始检测")
            self._isChnOpen = False
        else:
            # Initial channel
            if self._res_support:  # resistance enable
                ip = self._zcan.GetIProperty(self._dev_handle)
                self._zcan.SetValue(ip,
                                    str(self.cmbCANChn.currentIndex()) + "/initenal_resistance",
                                    '1' if self.cmbResEnable == 0 else '0')
                self._zcan.ReleaseIProperty(ip)

            # set usbcan-e-u baudrate
            if self._cur_dev_info["dev_type"] in USBCAN_XE_U_TYPE:
                ip = self._zcan.GetIProperty(self._dev_handle)
                self._zcan.SetValue(ip,
                                    str(self.cmbCANChn.currentIndex()) + "/baud_rate",
                                    self._cur_dev_info["chn_info"]["baudrate"][self.cmbBaudrate.currentText()])
                self._zcan.ReleaseIProperty(ip)

            # set usbcanfd clock
            if self._cur_dev_info["dev_type"] in USBCANFD_TYPE:
                ip = self._zcan.GetIProperty(self._dev_handle)
                self._zcan.SetValue(ip, str(self.cmbCANChn.current()) + "/clock", "60000000")
                self._zcan.ReleaseIProperty(ip)

            chn_cfg = ZCAN_CHANNEL_INIT_CONFIG()
            chn_cfg.can_type = ZCAN_TYPE_CANFD if self._is_canfd else ZCAN_TYPE_CAN
            if self._is_canfd:
                chn_cfg.config.canfd.mode = self.cmbCANMode
                chn_cfg.config.canfd.abit_timing = self._cur_dev_info["chn_info"]["baudrate"][self.cmbBaudrate.currentText()]
                chn_cfg.config.canfd.dbit_timing = self._cur_dev_info["chn_info"]["data_baudrate"][
                    self.cmbDataBaudrate.currentText()]
            else:
                chn_cfg.config.can.mode = self.cmbCANMode
                if self._cur_dev_info["dev_type"] in USBCAN_I_II_TYPE:
                    brt = self._cur_dev_info["chn_info"]["baudrate"][self.cmbBaudrate.currentText()]
                    chn_cfg.config.can.timing0 = brt["timing0"]
                    chn_cfg.config.can.timing1 = brt["timing1"]
                    chn_cfg.config.can.acc_code = 0
                    chn_cfg.config.can.acc_mask = 0xFFFFFFFF

            self._can_handle = self._zcan.InitCAN(self._dev_handle, self.cmbCANChn.currentIndex(), chn_cfg)
            if self._can_handle == INVALID_CHANNEL_HANDLE:
                QMessageBox.critical(self,"打开通道", "初始化通道失败!")
                return

            ret = self._zcan.StartCAN(self._can_handle)
            if ret != ZCAN_STATUS_OK:
                QMessageBox.critical(title="打开通道", message="打开通道失败!")
                return

            self.start_camera()
            self.start_radar()

            self.btnCtrl.setText("停止检测")
            self.btnCal.setEnabled(False)
            self.btnCalibration.setEnabled(False)
            self._isChnOpen = True

    def update_image(self,qt_image):
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def update_axe(self,point):
        self.scatter.set_offsets(point[:,0:2])
        for ann in self.annotations:
            ann.remove()
        self.annotations.clear()

        # Add new annotations for speed
        for i, (x, y, speed) in enumerate(point):
            ann = self.ax.annotate(f'{speed:.2f}',
                                   xy=(x, y),
                                   xytext=(5, 5),  # Offset from the point
                                   textcoords='offset points',
                                   ha='left',
                                   va='top')
            self.annotations.append(ann)

        # Redraw the canvas
        self.canvas.draw_idle()

    def camera_calibration(self):
        if self.chess_capture.isEnabled():
            self.chess_capture.setEnabled(False)
            self.result_calibration.setEnabled(False)
            self.save_calibration.setEnabled(False)
            if self._isOpen:
                self.btnCtrl.setEnabled(True)
                self.btnCalibration.setEnabled(True)
            self.stop_camera()
        else:
            self.chess_capture.setEnabled(True)
            self.result_calibration.setEnabled(True)
            self.save_calibration.setEnabled(True)
            self.btnCalibration.setEnabled(False)
            self.btnCtrl.setEnabled(False)
            self.start_camera(mode=1)
            self.chess_capture.clicked.connect(self.worker_camera.captureRequested.emit)
            self.result_calibration.clicked.connect(self.worker_camera.calibrateRequested.emit)
            self.save_calibration.clicked.connect(self.worker_camera.saveRequested.emit)

    def radar_calibration(self):
        if self._isChnOpen:
            # Close channel
            self.stop_radar()
            self.stop_camera()
            self._zcan.ResetCAN(self._can_handle)
            self.btnCal.setEnabled(True)
            self.x.setEnabled(False)
            self.y.setEnabled(False)
            self.z.setEnabled(False)
            self.save_calibration1.setEnabled(False)
            self.btnDevCtrl.setEnabled(True)
            self.btnCtrl.setEnabled(True)
            self._isChnOpen = False
        else:
            # Initial channel
            if self._res_support:  # resistance enable
                ip = self._zcan.GetIProperty(self._dev_handle)
                self._zcan.SetValue(ip,
                                    str(self.cmbCANChn.currentIndex()) + "/initenal_resistance",
                                    '1' if self.cmbResEnable == 0 else '0')
                self._zcan.ReleaseIProperty(ip)

            # set usbcan-e-u baudrate
            if self._cur_dev_info["dev_type"] in USBCAN_XE_U_TYPE:
                ip = self._zcan.GetIProperty(self._dev_handle)
                self._zcan.SetValue(ip,
                                    str(self.cmbCANChn.currentIndex()) + "/baud_rate",
                                    self._cur_dev_info["chn_info"]["baudrate"][self.cmbBaudrate.currentText()])
                self._zcan.ReleaseIProperty(ip)

            # set usbcanfd clock
            if self._cur_dev_info["dev_type"] in USBCANFD_TYPE:
                ip = self._zcan.GetIProperty(self._dev_handle)
                self._zcan.SetValue(ip, str(self.cmbCANChn.current()) + "/clock", "60000000")
                self._zcan.ReleaseIProperty(ip)

            chn_cfg = ZCAN_CHANNEL_INIT_CONFIG()
            chn_cfg.can_type = ZCAN_TYPE_CANFD if self._is_canfd else ZCAN_TYPE_CAN
            if self._is_canfd:
                chn_cfg.config.canfd.mode = self.cmbCANMode
                chn_cfg.config.canfd.abit_timing = self._cur_dev_info["chn_info"]["baudrate"][
                    self.cmbBaudrate.currentText()]
                chn_cfg.config.canfd.dbit_timing = self._cur_dev_info["chn_info"]["data_baudrate"][
                    self.cmbDataBaudrate.currentText()]
            else:
                chn_cfg.config.can.mode = self.cmbCANMode
                if self._cur_dev_info["dev_type"] in USBCAN_I_II_TYPE:
                    brt = self._cur_dev_info["chn_info"]["baudrate"][self.cmbBaudrate.currentText()]
                    chn_cfg.config.can.timing0 = brt["timing0"]
                    chn_cfg.config.can.timing1 = brt["timing1"]
                    chn_cfg.config.can.acc_code = 0
                    chn_cfg.config.can.acc_mask = 0xFFFFFFFF

            self._can_handle = self._zcan.InitCAN(self._dev_handle, self.cmbCANChn.currentIndex(), chn_cfg)
            if self._can_handle == INVALID_CHANNEL_HANDLE:
                QMessageBox.critical(self, "打开通道", "初始化通道失败!")
                return

            ret = self._zcan.StartCAN(self._can_handle)
            if ret != ZCAN_STATUS_OK:
                QMessageBox.critical(title="打开通道", message="打开通道失败!")
                return

            # start radar thread
            self.start_camera()
            self.start_radar()

            self.btnCal.setEnabled(False)
            self._isChnOpen = True

            self.x.setEnabled(True)
            self.y.setEnabled(True)
            self.z.setEnabled(True)
            self.save_calibration1.setEnabled(True)
            self.btnCtrl.setEnabled(False)
            self.btnDevCtrl.setEnabled(False)

            calibration_data = self.load_calibration_data()
            self.tvec = calibration_data['tvec']
            self.x.setValue(self.tvec[0])
            self.y.setValue(self.tvec[1])
            self.z.setValue(self.tvec[2])

            self.save_calibration1.clicked.connect(self.worker_camera.saveRequested1.emit)
            self.x.valueChanged.connect(lambda value: self.worker_camera.updateRequested.emit(0,value))
            self.y.valueChanged.connect(lambda value: self.worker_camera.updateRequested.emit(1,value))
            self.z.valueChanged.connect(lambda value: self.worker_camera.updateRequested.emit(2,value))

        return

    def load_calibration_data(self, file_path=None):
        file_path = file_path or paths.CALIBRATION_PATH
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return {
                    'mtx': np.array(data.get('camera_matrix', np.eye(3, dtype=np.float32))),
                    'dist': np.array(data.get('distortion_coefficients', np.zeros((5, 1), dtype=np.float32))),
                    'R': np.array(data.get('R',np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]],dtype=np.float32))),
                    'tvec': np.array(data.get('tvec', np.array([0, 0, 0],dtype=np.float32)))
                }
        except FileNotFoundError:
            print(f"Calibration file not found: {file_path}")
        except json.JSONDecodeError:
            print(f"Failed to decode JSON from {file_path}")
        except Exception as e:
            print(f"Unexpected error while loading calibration data: {e}")

        # 返回默认值
        return {
            'mtx': np.eye(3, dtype=np.float32),
            'dist': np.zeros((5, 1), dtype=np.float32),
            'R': np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=np.float32),
            'tvec': np.array([0, 0, 0], dtype=np.float32)
        }

    def start_radar(self):
        self.thread_radar = QThread()
        self.worker_radar = Radar.Worker(self._zcan, self._can_handle)
        self.worker_radar.moveToThread(self.thread_radar)

        # 连接信号和槽
        self.thread_radar.started.connect(self.worker_radar.startRequested.emit)
        self.worker_radar.progress.connect(self.update_axe)
        self.worker_radar.progress.connect(self.worker_camera.process_radar_data)

        # 启动线程
        self.thread_radar.start()

    def stop_radar(self):
        if hasattr(self, 'worker_radar'):
            self.worker_radar.stop()
        if hasattr(self, 'thread_radar') and self.thread_radar.isRunning():
            self.thread_radar.quit()
            self.thread_radar.wait()

    def start_camera(self,index=0,mode=0):
        self.thread_camera = QThread()
        self.worker_camera = Camera.Worker(camera_index=index,mode=mode)
        self.worker_camera.moveToThread(self.thread_camera)
        # 连接信号和槽
        self.worker_camera.image.connect(self.update_image)
        self.thread_camera.started.connect(self.worker_camera.startRequested.emit)
        # 启动线程
        self.thread_camera.start()

    def stop_camera(self):
        if self.worker_camera.isrunning:
            self.worker_camera.stopRequested.emit()
            QTimer.singleShot(100, lambda: (self.thread_camera.quit(), self.thread_camera.wait()))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
