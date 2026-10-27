from PyQt5.QtGui import QImage
from PyQt5.QtCore import QObject,QTimer
from PyQt5 import QtCore
import os
import cv2
import numpy as np
from ultralytics import YOLO
import json

import paths

img_size=(640, 480)
class Worker(QObject):
    image = QtCore.pyqtSignal(object)
    captureRequested = QtCore.pyqtSignal()
    calibrateRequested=QtCore.pyqtSignal()
    saveRequested=QtCore.pyqtSignal()
    saveRequested1=QtCore.pyqtSignal()
    startRequested=QtCore.pyqtSignal()
    stopRequested = QtCore.pyqtSignal()
    updateRequested=QtCore.pyqtSignal(object,object)

    def __init__(self, camera_index=0,mode=0):
        super().__init__()
        self.camera_index = camera_index
        self.mode=mode

        self.captureRequested.connect(self.capture_image)
        self.calibrateRequested.connect(self.calibrate_camera)
        self.saveRequested.connect(self.save_calibration)
        self.saveRequested1.connect(self.save_calibration1)
        self.startRequested.connect(self.run)
        self.stopRequested.connect(self.stop)
        self.updateRequested.connect(lambda index, value: self.update_RT(index,value))

        # 定义棋盘大小 (9x6)
        self.chessboard_size = (11, 8)
        self.objpoints = []  # 3D 点在现实世界空间
        self.imgpoints = []  # 2D 点在图像平面

        # 准备棋盘的3D点 (例如(0,0,0), (1,0,0), (2,0,0), ...)
        self.objp = np.zeros((self.chessboard_size[0] * self.chessboard_size[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:self.chessboard_size[0], 0:self.chessboard_size[1]].T.reshape(-1, 2)
        self.objp = self.objp * 3

        # 模型路径：项目内 models/yolov8n.pt（由 src/paths.py 统一定义）
        self.model_path = paths.YOLO_MODEL_PATH
        self.model=YOLO(self.model_path)

        calibration_data = self.load_calibration_data()
        self.mtx = calibration_data['mtx']
        self.dist = calibration_data['dist']
        self.R=calibration_data['R']
        self.rvec, _ = cv2.Rodrigues(self.R)
        self.tvec = calibration_data['tvec']

        self.timer = QTimer(self)  # move with the worker into the camera thread
        self.timer.timeout.connect(self.update_Frame)

        self.point = []
        self.velocity = np.empty(0)
        self.cap = None
        self.isrunning = False
        self.ret = False
        self.calibration_size = None
        self.threshold = 100

    def load_calibration_data(self,file_path=None):
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

    def run(self):
        if self.isrunning:
            return
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print(f"Unable to open camera index {self.camera_index}")
            self.cap.release()
            self.cap = None
            return
        self.isrunning = True
        self.timer.start(33)  # requested frame interval, not measured inference FPS

    def update_Frame(self):
        if not self.isrunning or self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return  # avoid accessing frame.shape after a device read failure

        if self.mode == 0:
            frame = cv2.undistort(frame, self.mtx, self.dist)
            frame = self.track_objects(frame)

        if len(self.point) > 0:
            for p in self.point:
                x, y, d = int(p[0]), int(p[1]), p[2]
                if 0 <= x < frame.shape[1] and 0 <= y < frame.shape[0]:
                    blue = int(max(0, min(255, 255 - float(d) * 3)))
                    cv2.circle(frame, (x, y), 5, (blue, 0, 0), -1)
        self.point = []

        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
        self.image.emit(qt_image.copy())  # detach from temporary NumPy frame buffer

    def process_radar_data(self, radar_data):
        radar_data = np.asarray(radar_data)
        if radar_data.ndim != 2 or radar_data.shape[1] < 3 or len(radar_data) == 0:
            self.point = []
            self.velocity = np.empty(0)
            return

        self.velocity = radar_data[:, -1]
        points = np.column_stack((
            radar_data[:, 0],
            radar_data[:, 1],
            np.zeros(len(radar_data))
        )).astype(np.float32)
        # Normal detection operates on UNDISTORTED images. Project into the
        # same undistorted pixel coordinates; calibration mode uses raw frames.
        distortion = self.dist if self.mode != 0 else np.zeros_like(self.dist)
        projected, _ = cv2.projectPoints(
            points, self.rvec, self.tvec, self.mtx, distortion
        )
        projected = projected.reshape(-1, 2)
        self.point = np.column_stack((projected, radar_data[:, 1]))

    def track_objects(self, frame):
        results = self.model.track(source=frame, persist=True, show=False)  # 执行追踪
        tracked_frame = results[0].orig_img  # 获取追踪后的帧
        for result in results[0].boxes:
            x1, y1, x2, y2 = map(int, result.xyxy[0])  # 提取锚框的坐标
            confidence = result.conf[0]  # 提取置信度
            label = result.cls[0]  # 提取类别标签

            bbox_center = np.array([(x1 + x2) / 2, (y1 + y2) / 2],dtype=np.float32)  # 计算锚框中心
            closest_point, distance = self.find_closest_point(self.point, bbox_center)
            if closest_point is not None and distance < self.threshold:
                velocity_value = self.velocity[closest_point]
            else:
                velocity_value = "Unknown"
            # 绘制矩形框
            cv2.rectangle(tracked_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 绘制标签和置信度
            text = f"{self.model.names[int(label)]}: {confidence:.2f},Vel: {velocity_value}"
            cv2.putText(tracked_frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return tracked_frame

    def find_closest_point(self,radar_points, point):
        if len(radar_points) == 0:
            return None, None
        distances = np.linalg.norm(radar_points[:, :2] - point, axis=1)
        min_index = np.argmin(distances)
        return min_index, distances[min_index]

    def capture_image(self):
        ret, frame = self.cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.calibration_size = gray.shape[::-1]
            ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)

            if ret:
                self.objpoints.append(self.objp)
                self.imgpoints.append(corners)
                # 显示检测到的棋盘角点
                cv2.drawChessboardCorners(frame, self.chessboard_size, corners, ret)
                print("成功拍下棋盘照片")
            else:
                print("未找到棋盘")

    def calibrate_camera(self):
        if len(self.objpoints) < 10:
            print("没有足够的图片用于标定，请拍摄至少10张照片")
            return

        self.ret, self.mtx, self.dist, rvecs, tvecs = cv2.calibrateCamera(
            self.objpoints, self.imgpoints, self.calibration_size or img_size, None, None
        )

        if self.ret:
            print(f"相机矩阵: \n{self.mtx}")
            print(f"畸变系数: \n{self.dist}")
        else:
            print("标定失败")

    def save_calibration(self):
        if not self.ret:
            return

        calibration_data = {}
        try:
            try:
                with open(paths.CALIBRATION_PATH, 'r') as f:
                    calibration_data = json.load(f)
            except FileNotFoundError:
                pass  # 文件不存在，初始化为空字典

            # 将 NumPy 数组转换为列表以保存到 JSON 文件中
            data_to_save = {
                'camera_matrix': self.mtx.tolist(),
                'distortion_coefficients': self.dist.tolist()
            }
            for key, value in data_to_save.items():
                calibration_data[key] = value  # 如果键存在则覆盖，否则添加新的键值对
            with open(paths.CALIBRATION_PATH, 'w') as f:
                json.dump(calibration_data, f, indent=4)

            print("标定数据已成功保存")
        except Exception as e:
            print(f"保存标定数据时发生错误: {str(e)}")

    def save_calibration1(self):
        calibration_data = {}
        try:
            try:
                with open(paths.CALIBRATION_PATH, 'r') as f:
                    calibration_data = json.load(f)
            except FileNotFoundError:
                pass  # 文件不存在，初始化为空字典


            # 将 NumPy 数组转换为列表以保存到 JSON 文件中
            data_to_save = {
                'R': self.R.tolist(),
                'tvec': self.tvec.tolist()
            }
            for key, value in data_to_save.items():
                calibration_data[key] = value  # 如果键存在则覆盖，否则添加新的键值对

            with open(paths.CALIBRATION_PATH, 'w') as f:
                json.dump(calibration_data, f, indent=4)

            print("标定数据已成功保存")
        except Exception as e:
            print(f"保存标定数据时发生错误: {str(e)}")

    def update_RT(self,index,value):
        self.tvec[index]=value

    @QtCore.pyqtSlot()
    def stop(self):
        self.isrunning = False
        self.timer.stop()
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
