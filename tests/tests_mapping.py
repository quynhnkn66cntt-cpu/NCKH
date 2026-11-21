import json
import unittest
from pathlib import Path

import yaml


class TestEventMappingData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # tests/test_mapping.py -> thư mục gốc project
        cls.project_dir = Path(__file__).resolve().parent.parent
        cls.config_file = cls.project_dir / "config.yaml"

        # Đọc cấu hình
        with open(cls.config_file, "r", encoding="utf-8") as f:
            cls.config = yaml.safe_load(f)

        cls.hashed_event_dir = (
            cls.project_dir / cls.config["paths"]["hashed_events"]
        )

        # Tự động lấy tất cả JSON event
        cls.json_files = sorted(cls.hashed_event_dir.glob("*.json"))

        cls.events = []

        for json_file in cls.json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                cls.events.append(json.load(f))

    def test_event_files_exist(self):
        """Phải có dữ liệu event để mapping."""
        self.assertGreater(
            len(self.json_files),
            0,
            "Không tìm thấy file JSON event."
        )

    def test_event_count_is_dynamic(self):
        """Số event phải được đọc tự động từ dữ liệu."""
        self.assertEqual(
            len(self.events),
            len(self.json_files)
        )

    def test_event_id_exists_and_unique(self):
        """Mỗi event phải có eventID và không được trùng."""
        event_ids = []

        for event in self.events:
            self.assertIn("eventID", event)
            self.assertTrue(event["eventID"])
            event_ids.append(event["eventID"])

        self.assertEqual(
            len(event_ids),
            len(set(event_ids)),
            "Phát hiện eventID bị trùng."
        )

    def test_required_fields(self):
        """Kiểm tra các trường cốt lõi của mỗi event."""
        required_fields = [
            "eventID",
            "batchID",
            "eventType",
            "actorID",
            "timestamp",
            "dataHash",
            "previousEventHash",
            "currentHash"
        ]

        for event in self.events:
            for field in required_fields:
                self.assertIn(
                    field,
                    event,
                    f"{event.get('eventID', 'UNKNOWN')} thiếu {field}"
                )

                self.assertIsNotNone(
                    event[field],
                    f"{event.get('eventID', 'UNKNOWN')} có {field} = None"
                )

    def test_valid_event_type(self):
        """eventType chỉ được thuộc 7 loại sự kiện đã thiết kế."""
        valid_types = {
            "SEED_STOCKING",
            "FEEDING",
            "TREATMENT",
            "HARVEST",
            "PROCESSING",
            "SHIPPING",
            "DISTRIBUTION"
        }

        for event in self.events:
            self.assertIn(
                event["eventType"],
                valid_types,
                f"{event['eventID']} có eventType không hợp lệ."
            )

    def test_hash_fields_not_empty(self):
        """Các hash bắt buộc không được rỗng."""
        for event in self.events:
            self.assertTrue(
                event["dataHash"],
                f"{event['eventID']} thiếu dataHash."
            )

            self.assertTrue(
                event["currentHash"],
                f"{event['eventID']} thiếu currentHash."
            )

            self.assertTrue(
                event["previousEventHash"],
                f"{event['eventID']} thiếu previousEventHash."
            )

    def test_genesis_event(self):
        """EV001 phải là điểm bắt đầu của hash chain."""
        genesis = next(
            (event for event in self.events
             if event["eventID"] == "EV001"),
            None
        )

        self.assertIsNotNone(
            genesis,
            "Không tìm thấy genesis event EV001."
        )

        self.assertEqual(
            genesis["previousEventHash"],
            "GENESIS",
            "EV001 phải có previousEventHash = GENESIS."
        )

    def test_only_ev001_is_genesis(self):
        """Không event nào ngoài EV001 được dùng GENESIS."""
        for event in self.events:
            if event["eventID"] != "EV001":
                self.assertNotEqual(
                    event["previousEventHash"],
                    "GENESIS",
                    f"{event['eventID']} không được dùng GENESIS."
                )


if __name__ == "__main__":
    unittest.main()