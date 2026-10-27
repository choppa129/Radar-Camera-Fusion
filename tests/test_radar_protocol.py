"""Hardware-free regression tests: python -m unittest discover -s tests -v."""

import math
from types import SimpleNamespace
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from radar_protocol import RadarScanAssembler, decode_target, unpack_frames


class DecoderTests(unittest.TestCase):
    def test_coordinate_and_radial_velocity(self):
        payload = [0, 100, 0x34, 20, 120, 0x80, 0xA0, 0]
        x, y, velocity = decode_target(payload)
        self.assertAlmostEqual(x, ((0x34 & 7) * 256 + 20) * .2 - 204.6)
        self.assertAlmostEqual(y, (100 * 32 + (0x34 >> 3)) * .2 - 500)
        expected_vy = (120 * 4 + (0x80 >> 6)) * .25 - 128
        expected_vx = ((0x80 & 0x3f) * 8 + (0xA0 >> 5)) * .25 - 64
        self.assertAlmostEqual(
            velocity,
            expected_vy * math.cos(math.atan2(x, y)) +
            expected_vx * math.sin(math.atan2(x, y))
        )

    def test_rejects_truncated_target(self):
        with self.assertRaises(ValueError):
            decode_target([0, 1, 2])

    def test_vendor_can_and_canfd_length_fields(self):
        payload = [0, 100, 0x34, 20, 120, 0x80, 0xA0, 0]
        can = SimpleNamespace(frame=SimpleNamespace(
            can_id=0x60B, can_dlc=8, data=payload
        ))
        canfd = SimpleNamespace(frame=SimpleNamespace(
            can_id=0x60B, len=8, data=payload + [0] * 56
        ))
        self.assertEqual(list(unpack_frames([can], 1)), [(0x60B, bytes(payload))])
        self.assertEqual(
            list(unpack_frames([canfd], 1, is_canfd=True)),
            [(0x60B, bytes(payload))]
        )

    def test_scan_split_across_batches(self):
        decoder = RadarScanAssembler()
        target = bytes([0, 100, 0x34, 20, 120, 0x80, 0xA0, 0])
        self.assertIsNone(decoder.feed([(0x60B, target)]))
        self.assertEqual(decoder.feed([(0x60A, b"\x00")]), ())
        self.assertEqual(len(decoder.feed([(0x60B, target)])), 1)
        self.assertIsNone(decoder.feed([(0x123, b"foo")]))
        self.assertEqual(len(decoder.feed([(0x60B, target)])), 2)
        self.assertEqual(decoder.feed([(0x60A, b"\x00")]), ())

    def test_ignores_bad_frames_but_continues(self):
        decoder = RadarScanAssembler()
        self.assertEqual(decoder.feed([(0x60A, b""), (0x60B, b"abc")]), ())
        target = bytes([0, 100, 52, 20, 120, 128, 160])
        self.assertEqual(len(decoder.feed([(0x60B, target)])), 1)


if __name__ == "__main__":
    unittest.main()
