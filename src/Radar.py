from PyQt5 import QtCore
from PyQt5.QtCore import QObject,QTimer
import numpy as np
from zlgcan import *
from radar_protocol import RadarScanAssembler, unpack_frames

MAX_RCV_NUM     = 10
class Worker(QObject):
    progress = QtCore.pyqtSignal(object)
    startRequested=QtCore.pyqtSignal()
    finished=QtCore.pyqtSignal()
    def __init__(self,zcan,canhandle):
        super().__init__()
        self.is_running = False
        self._zcan=zcan
        self._can_handle=canhandle
        self.view=[]
        self._decoder = RadarScanAssembler()

        self.startRequested.connect(self.run)

        self.timer=QTimer(self)  # follows the worker to its QThread
        self.timer.timeout.connect(self.work)
    def run(self):
        self.is_running = True
        self.timer.start(100)

    def work(self):
        # try:
            if  self.is_running:
                can_num = self._zcan.GetReceiveNum(self._can_handle, ZCAN_TYPE_CAN)
                canfd_num = self._zcan.GetReceiveNum(self._can_handle, ZCAN_TYPE_CANFD)
                if not can_num and not canfd_num:
                    return

                if can_num:
                    while can_num and self.is_running:
                        read_cnt = MAX_RCV_NUM if can_num >= MAX_RCV_NUM else can_num
                        can_msgs, act_num = self._zcan.Receive(self._can_handle, read_cnt, MAX_RCV_NUM)
                        if act_num:
                                # update data
                            self.RadarDataRev(can_msgs, act_num, False)
                        else:
                            break
                        can_num -= act_num
                if canfd_num:
                    while canfd_num and self.is_running:
                        read_cnt = MAX_RCV_NUM if canfd_num >= MAX_RCV_NUM else canfd_num
                        canfd_msgs, act_num = self._zcan.ReceiveFD(self._can_handle, read_cnt, MAX_RCV_NUM)
                        if act_num:
                                # update data
                            self.RadarDataRev(canfd_msgs, act_num, True)
                        else:
                            break
                        canfd_num -= act_num
        # except:
        #       print("Error occurred while read CAN(FD) data!")
    def RadarDataRev(self, msgs, msgs_num, is_canfd=False):
        """Parse a received CAN batch and preserve scans spanning batches."""
        current_scan = self._decoder.feed(unpack_frames(msgs, msgs_num, is_canfd))
        if current_scan is not None:
            self.view = np.asarray(current_scan, dtype=np.float64).reshape(-1, 3)
            # Empty scans are emitted too, clearing old detections in the UI.
            self.progress.emit(self.view)

    @QtCore.pyqtSlot()
    def stop(self):
        self.is_running = False
        self.timer.stop()