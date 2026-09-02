"""Pacer core for bin/op25-pcm-pace — the thing that keeps Icecast fed between calls.

Why it exists (docs/AUDIO.md): Icecast disconnects a source after its socket
timeout when no bytes arrive, and OP25 only emits PCM during a call. The pacer
turns bursty UDP PCM into a continuous 8 kHz s16le stream: real audio when
buffered, digital silence otherwise, bounded latency.
"""
import importlib.machinery
import importlib.util
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = HERE.parent / "bin" / "op25-pcm-pace"


def load():
    loader = importlib.machinery.SourceFileLoader("op25_pcm_pace", str(SCRIPT))
    spec = importlib.util.spec_from_loader("op25_pcm_pace", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


FRAME = 320  # 20 ms of 8 kHz s16le mono


class PacerTests(unittest.TestCase):
    def setUp(self):
        self.m = load()
        self.p = self.m.Pacer(frame_bytes=FRAME, max_buffer_bytes=4 * FRAME)

    def test_silence_when_nothing_buffered(self):
        self.assertEqual(self.p.next_frame(), b"\x00" * FRAME)

    def test_passes_audio_through_in_order(self):
        a, b = bytes(range(160)) * 2, bytes(range(160, 0, -1)) * 2
        self.p.feed(a)
        self.p.feed(b)
        self.assertEqual(self.p.next_frame(), a)
        self.assertEqual(self.p.next_frame(), b)
        self.assertEqual(self.p.next_frame(), b"\x00" * FRAME)

    def test_partial_frame_is_padded_with_silence(self):
        self.p.feed(b"\x01" * 100)
        self.assertEqual(self.p.next_frame(), b"\x01" * 100 + b"\x00" * 220)

    def test_two_byte_control_packets_are_dropped(self):
        # sockaudio.py treats a 2-byte datagram as a command, not PCM
        self.p.feed(b"\x00\x01")
        self.assertEqual(self.p.next_frame(), b"\x00" * FRAME)

    def test_odd_byte_datagram_is_dropped(self):
        self.p.feed(b"\x01" * 3)
        self.assertEqual(self.p.next_frame(), b"\x00" * FRAME)

    def test_latency_is_bounded_by_dropping_oldest(self):
        for i in range(10):
            self.p.feed(bytes([i]) * FRAME)
        # only the newest max_buffer_bytes (4 frames) survive
        self.assertEqual(self.p.next_frame(), bytes([6]) * FRAME)
        self.assertEqual(self.p.buffered, 3 * FRAME)


class ArgTests(unittest.TestCase):
    def test_defaults_match_op25(self):
        m = load()
        a = m.parse_args([])
        self.assertEqual((a.port, a.rate, a.frame_ms), (23456, 8000, 20))


if __name__ == "__main__":
    unittest.main()
