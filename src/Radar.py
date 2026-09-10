from PyQt5 import QtCore
from PyQt5.QtCore import QObject,QTimer
import numpy as np
from zlgcan import *

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

        self.startRequested.connect(self.run)

        self.timer=QTimer()
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
                    time.sleep(0.005)  # wait 5ms
                    #continue

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
    def Xtrans(self, raw):
        raw_3 = int(raw[2], 16)
        raw_4 = int(raw[3], 16)
        return ((raw_3 & 0x07) * 256 + raw_4) * 0.2 - 204.6

    def Ytrans(self, raw):
        raw_2 = int(raw[1], 16)
        raw_3 = int(raw[2], 16)
        return (raw_2 * 32 + (raw_3 >> 3)) * 0.2 - 500

    def Velocity(self, raw,X,Y):
        raw_5 = int(raw[4], 16)
        raw_6 = int(raw[5], 16)
        raw_7 = int(raw[6], 16)
        vy=(raw_5*4+(raw_6>>6))*0.25-128
        vx=((raw_6&0x3f)*8+(raw_7>>5))*0.25-64
        angle=np.arctan2(X,Y)
        return vy*np.cos(angle)+vx*np.sin(angle)


    def RadarDataRev(self, msgs, msgs_num, is_canfd=False):
        if is_canfd:
            view = []
            raw = []
            i = 1
            if hex(msgs[0].frame.can_id)[2:] == '60a':
                while (i < msgs_num and hex(msgs[i].frame.can_id)[2:] == '60b'):
                    for o in range(msgs[i].frame.can_len):
                        raw.append(hex(msgs[i].frame.data[o])[2:])
                    view.append(self.Xtrans(raw))
                    view.append(self.Ytrans(raw))
                    view.append(self.Velocity(raw,view[-1],view[-2]))
                    raw = []
                    i += 1
            else:
                return
            self.view = np.array(view, dtype=np.float64).reshape(-1, 3)
            self.progress.emit(self.view)
        else:
            view = []
            raw = []
            i = 1
            if hex(msgs[0].frame.can_id)[2:] == '60a':
                while (i < msgs_num and hex(msgs[i].frame.can_id)[2:] == '60b'):
                    for o in range(msgs[i].frame.can_dlc):
                        raw.append(hex(msgs[i].frame.data[o])[2:])
                    view.append(self.Xtrans(raw))
                    view.append(self.Ytrans(raw))
                    view.append(self.Velocity(raw, view[-1], view[-2]))
                    raw = []
                    i += 1
            else:
                return
            self.view = np.array(view, dtype=np.float64).reshape(-1, 3)
            if(self.view.size!=0):
                self.progress.emit(self.view)


    def stop(self):
        self.is_running = False
        self.timer.stop()