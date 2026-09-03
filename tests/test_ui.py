"""Logic behind bin/mcfrs-ui: call tracking from OP25's status feed, and
radio-ID / talkgroup labelling. Pure functions; the HTTP layer is thin."""
import importlib.machinery
import importlib.util
import pathlib
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "bin" / "mcfrs-ui"


def load():
    loader = importlib.machinery.SourceFileLoader("mcfrs_ui", str(SCRIPT))
    spec = importlib.util.spec_from_loader("mcfrs_ui", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def op25(tgid=0, tag="", srcaddr=0, grpaddr=0, encrypted=0, freq=0):
    """Shape of one poll of OP25's http terminal (json_type list)."""
    return [
        {"json_type": "change_freq", "tgid": tgid or None, "tag": tag, "freq": freq, "tdma": None},
        {"json_type": "trunk_update", "srcaddr": srcaddr, "grpaddr": grpaddr, "encrypted": encrypted, "nac": 2274},
    ]


class TalkgroupLabelTests(unittest.TestCase):
    def setUp(self):
        self.m = load()

    def test_splits_op25_tag_into_zone_channel_and_name(self):
        self.assertEqual(self.m.split_tag("MCFR 7A2 Disp"), ("7A2", "Disp"))
        self.assertEqual(self.m.split_tag("MCFR 7A4 Inc 10"), ("7A4", "Inc 10"))
        self.assertEqual(self.m.split_tag("MCFR Station 14"), ("", "Station 14"))
        self.assertEqual(self.m.split_tag("MCFR 7H4 Holy Cross Germantown [ENC]"), ("7H4", "Holy Cross Germantown [ENC]"))

    def test_unknown_tag_shows_the_number(self):
        self.assertEqual(self.m.split_tag("", tgid=6025), ("", "TG 6025"))


class RadioAliasTests(unittest.TestCase):
    def setUp(self):
        self.m = load()
        self.book = self.m.AliasBook.from_lines([
            "# comment",
            "2501234\tA714 Driver",
            "2501235\tE714 Officer",
            "re:^25019(\\d\\d)$\tBattalion Chief \\1",
        ])

    def test_exact_alias(self):
        self.assertEqual(self.book.alias(2501234), "A714 Driver")

    def test_pattern_alias(self):
        self.assertEqual(self.book.alias(2501905), "Battalion Chief 05")

    def test_unknown_is_the_raw_id(self):
        self.assertEqual(self.book.alias(2509999), "2509999")

    def test_zero_is_blank(self):
        self.assertEqual(self.book.alias(0), "")


class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.m = load()
        self.t = self.m.Tracker(idle_seconds=2.0)

    def test_idle_has_no_current_call(self):
        self.t.observe(op25(), now=100.0)
        self.assertIsNone(self.t.current())
        self.assertEqual(self.t.history(), [])

    def test_call_starts_and_records_radio(self):
        self.t.observe(op25(4005, "MCFR 7A2 Disp", srcaddr=2501234, grpaddr=4005), now=100.0)
        c = self.t.current()
        self.assertEqual((c["tgid"], c["zone"], c["name"]), (4005, "7A2", "Disp"))
        self.assertEqual(c["radios"], [2501234])
        self.assertEqual(c["start"], 100.0)

    def test_second_radio_on_same_call_is_appended_once(self):
        self.t.observe(op25(4015, "MCFR 7A4 Inc 10", srcaddr=2501234, grpaddr=4015), now=100.0)
        self.t.observe(op25(4015, "MCFR 7A4 Inc 10", srcaddr=2501235, grpaddr=4015), now=101.0)
        self.t.observe(op25(4015, "MCFR 7A4 Inc 10", srcaddr=2501234, grpaddr=4015), now=102.0)
        self.assertEqual(self.t.current()["radios"], [2501234, 2501235])
        self.assertEqual(self.t.current()["radio"], 2501234)  # the one talking now

    def test_call_ends_after_idle_and_moves_to_history(self):
        self.t.observe(op25(4005, "MCFR 7A2 Disp", srcaddr=2501234, grpaddr=4005), now=100.0)
        self.t.observe(op25(), now=101.0)          # back on the control channel
        self.assertIsNotNone(self.t.current())     # grace period
        self.t.observe(op25(), now=103.5)
        self.assertIsNone(self.t.current())
        h = self.t.history()
        self.assertEqual(len(h), 1)
        self.assertEqual((h[0]["tgid"], h[0]["start"], h[0]["end"]), (4005, 100.0, 100.0))  # end = last voice seen

    def test_talkgroup_change_closes_previous_call(self):
        self.t.observe(op25(4005, "MCFR 7A2 Disp", srcaddr=1, grpaddr=4005), now=100.0)
        self.t.observe(op25(4000, "MCFR 7A1 Ops 1", srcaddr=2, grpaddr=4000), now=100.5)
        self.assertEqual(self.t.current()["tgid"], 4000)
        self.assertEqual([h["tgid"] for h in self.t.history()], [4005])

    def test_srcaddr_zero_does_not_add_a_radio(self):
        self.t.observe(op25(4005, "MCFR 7A2 Disp", srcaddr=0, grpaddr=4005), now=100.0)
        self.assertEqual(self.t.current()["radios"], [])

    def test_history_is_newest_first_and_bounded(self):
        for i in range(60):
            self.t.observe(op25(4000 + i, "MCFR x", srcaddr=1, grpaddr=4000 + i), now=100.0 + i)
        self.t.observe(op25(), now=200.0)
        h = self.t.history()
        self.assertEqual(len(h), 50)
        self.assertEqual(h[0]["tgid"], 4059)

    def test_same_talkgroup_soon_after_reopens_the_conversation(self):
        # transmissions on one talkgroup arrive with gaps of tens of seconds (measured
        # 2026-09-03); one conversation, not one row per PTT
        self.t = self.m.Tracker(idle_seconds=2.0, merge_seconds=30.0)
        self.t.observe(op25(4000, "MCFR 7A1 Ops 1", srcaddr=2500531, grpaddr=4000), now=100.0)
        self.t.observe(op25(), now=103.0)
        self.assertEqual(len(self.t.history()), 1)
        self.t.observe(op25(4000, "MCFR 7A1 Ops 1", srcaddr=67, grpaddr=4000), now=124.0)
        c = self.t.current()
        self.assertEqual((c["start"], c["radios"], c["radio"]), (100.0, [2500531, 67], 67))
        self.assertEqual(self.t.history(), [])
        self.t.observe(op25(), now=127.0)
        self.assertEqual(len(self.t.history()), 1)
        self.assertEqual(self.t.history()[0]["end"], 124.0)

    def test_same_talkgroup_after_the_merge_window_is_a_new_conversation(self):
        self.t = self.m.Tracker(idle_seconds=2.0, merge_seconds=30.0)
        self.t.observe(op25(4000, "MCFR 7A1 Ops 1", srcaddr=1, grpaddr=4000), now=100.0)
        self.t.observe(op25(), now=103.0)
        self.t.observe(op25(4000, "MCFR 7A1 Ops 1", srcaddr=2, grpaddr=4000), now=140.0)
        self.assertEqual(self.t.current()["radios"], [2])
        self.assertEqual(len(self.t.history()), 1)

    def test_state_is_json_ready(self):
        import json
        self.t.observe(op25(4005, "MCFR 7A2 Disp", srcaddr=2501234, grpaddr=4005, encrypted=0), now=100.0)
        s = self.t.state(now=100.5)
        json.dumps(s)
        self.assertEqual(s["current"]["elapsed"], 0.5)
        self.assertIn("history", s)


if __name__ == "__main__":
    unittest.main()
