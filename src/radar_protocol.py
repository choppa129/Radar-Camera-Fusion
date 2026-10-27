"""Pure-Python decoder for the project's 0x60A/0x60B radar CAN stream.

Separate from PyQt, NumPy and the vendor DLL so recorded CAN packets can be
unit-tested without a Windows workstation or connected radar.
"""

from math import atan2, cos, sin

SCAN_HEADER_ID = 0x60A
TARGET_ID = 0x60B


def decode_target(payload):
    """Decode one target payload to (lateral_x, forward_y, radial_velocity).

    Byte layout and scale factors follow the original SR73F integration. The
    component-to-radial projection assumes X is lateral and Y is forward;
    verify the sign convention against the physical radar before deployment.
    """
    if len(payload) < 7:
        raise ValueError("Radar target payload requires at least seven bytes")
    b1, b2, b3, b4, b5, b6 = (int(payload[i]) for i in range(1, 7))
    x = ((b2 & 0x07) * 256 + b3) * 0.2 - 204.6
    y = (b1 * 32 + (b2 >> 3)) * 0.2 - 500.0
    vy = (b4 * 4 + (b5 >> 6)) * 0.25 - 128.0
    vx = ((b5 & 0x3F) * 8 + (b6 >> 5)) * 0.25 - 64.0
    bearing = atan2(x, y)
    return x, y, vy * cos(bearing) + vx * sin(bearing)


class RadarScanAssembler:
    """Accumulate target frames after a header, across receive batches.

    feed() returns None when there is no scan update, or the complete set of
    targets received so far for the current scan. A new header clears the
    previous targets (including an empty scan).
    """

    def __init__(self):
        self._active = False
        self._targets = []

    def feed(self, frames):
        updated = False
        for frame_id, payload in frames:
            if int(frame_id) == SCAN_HEADER_ID:
                self._active = True
                self._targets = []
                updated = True
            elif int(frame_id) == TARGET_ID and self._active:
                try:
                    target = decode_target(payload)
                except (TypeError, ValueError, IndexError):
                    continue
                self._targets.append(target)
                updated = True
        return tuple(self._targets) if updated else None
