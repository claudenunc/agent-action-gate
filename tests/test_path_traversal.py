import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.helpers import make_runtime_root
from action_queue import ActionQueue


class PathTraversalTests(unittest.TestCase):
    def setUp(self):
        self.root = make_runtime_root()
        self.queue = ActionQueue(self.root)

    def write_action(self, action_id: str, status: str = "pending"):
        data = {
            "id": action_id,
            "status": status,
            "created_at": "2026-04-25T00:00:00Z",
            "skill_name": "email_notify",
            "args": {"subject": "Hello", "body": "World"},
            "agent": "caller",
            "source": "test",
            "risk": "medium",
        }
        self.queue._path_for(action_id).write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    def test_rejects_malformed_action_ids(self):
        bad_ids = [
            "../../etc/passwd",
            "..%2F..%2Fsecret",
            "action/../../x",
            "./valid",
            "valid.json",
            "valid/action",
            "valid\\action",
            "valid.action",
            "action..id",
        ]
        for action_id in bad_ids:
            with self.subTest(action_id=action_id):
                with self.assertRaises(ValueError):
                    self.queue.get(action_id)
                with self.assertRaises(ValueError):
                    self.queue.update(action_id, status="rejected")

    def test_create_get_update_and_list_valid_action(self):
        action = self.write_action("test_valid", status="pending")

        loaded = self.queue.get(action["id"])
        self.assertEqual(loaded["id"], action["id"])

        updated = self.queue.update(action["id"], status="updated")
        self.assertEqual(updated["status"], "updated")

        listed = self.queue.list("updated")
        self.assertEqual([item["id"] for item in listed], [action["id"]])

    def test_list_rejects_invalid_pending_action_filename(self):
        bad_path = self.queue.dir / "valid.json.json"
        with patch.object(Path, "glob", return_value=[bad_path]):
            with self.assertRaises(ValueError):
                self.queue.list("all")


if __name__ == "__main__":
    unittest.main()
