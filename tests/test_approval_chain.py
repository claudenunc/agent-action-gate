import json
import unittest

from tests.helpers import make_runtime_root
from approval_log import append, approval_chain_path, verify


class ApprovalChainTests(unittest.TestCase):
    def setUp(self):
        self.root = make_runtime_root()

    def test_append_two_entries_and_verify_chain(self):
        append("act_1", "human", "approved", "email_notify", {"subject": "A"}, root=self.root)
        append("act_2", "human", "rejected", "sms_email_notify", {"message": "B"}, root=self.root)

        ok, message = verify(self.root)
        self.assertTrue(ok, message)
        self.assertIn("OK", message)

    def test_tampering_middle_entry_breaks_chain(self):
        append("act_1", "human", "approved", "email_notify", {"subject": "A"}, root=self.root)
        append("act_2", "human", "rejected", "sms_email_notify", {"message": "B"}, root=self.root)
        append("act_3", "human", "rejected", "ifttt_notify", {"title": "C"}, root=self.root)

        path = approval_chain_path(self.root)
        lines = path.read_text(encoding="utf-8").splitlines()
        middle = json.loads(lines[1])
        middle["decision"] = "approved"
        lines[1] = json.dumps(middle, sort_keys=True, separators=(",", ":"))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        ok, message = verify(self.root)
        self.assertFalse(ok)
        self.assertIn("line 2", message)
        self.assertIn("curr_hash mismatch", message)


if __name__ == "__main__":
    unittest.main()
