import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from topic_history import choose_topic, record_topic


class TopicHistoryTests(unittest.TestCase):
    def test_first_run_selects_unique_topics(self):
        topics = [f"topic-{i}" for i in range(12)]
        with tempfile.TemporaryDirectory() as temp:
            history = Path(temp) / "topic_history.json"
            selected = []
            for slot in range(6):
                index = choose_topic(topics, history, "2026-11-20", slot)
                self.assertNotIn(topics[index], selected)
                selected.append(topics[index])
                record_topic(history, topics[index], "2026-11-20")
            self.assertEqual(len(selected), 6)

    def test_next_day_uses_unused_topics_before_repeating(self):
        topics = [f"topic-{i}" for i in range(12)]
        with tempfile.TemporaryDirectory() as temp:
            history = Path(temp) / "topic_history.json"
            first_day = []
            for slot in range(6):
                index = choose_topic(topics, history, "2026-11-20", slot)
                first_day.append(topics[index])
                record_topic(history, topics[index], "2026-11-20")
            second_day = []
            for slot in range(6):
                index = choose_topic(topics, history, "2026-11-21", slot)
                second_day.append(topics[index])
                record_topic(history, topics[index], "2026-11-21")
            self.assertEqual(len(set(first_day + second_day)), 12)

    def test_history_is_valid_json(self):
        with tempfile.TemporaryDirectory() as temp:
            history = Path(temp) / "topic_history.json"
            record_topic(history, "Ocean Mysteries", "2026-11-20")
            self.assertEqual(json.loads(history.read_text())["last_used"]["Ocean Mysteries"], "2026-11-20")


if __name__ == "__main__":
    unittest.main()
