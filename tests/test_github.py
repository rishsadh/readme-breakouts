import base64
import json
import unittest
from unittest import mock

from readme_breakouts import github
from readme_breakouts.github import ApiError, Client, decode_readme


class Transport(unittest.TestCase):
    def client(self, **kw):
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "x"}, clear=False):
            return Client(delay=0, backoff=0, transport="token", log=lambda m: None, **kw)

    def test_ok(self):
        c = self.client()
        with mock.patch.object(c, "_urllib", return_value=(200, b'{"a": 1}')):
            self.assertEqual(c.get_json("/x"), {"a": 1})
        self.assertEqual(c.calls, 1)

    def test_404_raises_without_retry(self):
        c = self.client()
        m = mock.Mock(return_value=(404, b'{"message": "Not Found"}'))
        with mock.patch.object(c, "_urllib", m):
            with self.assertRaises(ApiError) as cm:
                c.get_json("/x")
        self.assertEqual(cm.exception.status, 404)
        self.assertEqual(m.call_count, 1)

    def test_403_waits_and_retries(self):
        c = self.client()
        m = mock.Mock(side_effect=[(403, b"{}"), (429, b"{}"), (200, b'{"ok": true}')])
        with mock.patch.object(c, "_urllib", m), mock.patch.object(github.time, "sleep") as sl:
            self.assertEqual(c.get_json("/x"), {"ok": True})
        self.assertEqual(m.call_count, 3)
        self.assertEqual(sl.call_count, 2)

    def test_403_gives_up(self):
        c = self.client(retries=1)
        m = mock.Mock(return_value=(403, b'{"message": "rate"}'))
        with mock.patch.object(c, "_urllib", m), mock.patch.object(github.time, "sleep"):
            with self.assertRaises(ApiError):
                c.get_json("/x")
        self.assertEqual(m.call_count, 2)

    def test_delay_between_calls(self):
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "x"}):
            c = Client(delay=3, transport="token", log=lambda m: None)
        with mock.patch.object(c, "_urllib", return_value=(200, b"{}")), mock.patch.object(github.time, "sleep") as sl:
            c.get_json("/a")
            c.get_json("/b")
        self.assertTrue(any(call.args[0] > 2 for call in sl.call_args_list))

    def test_auto_transport_prefers_token_then_gh(self):
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "x"}):
            self.assertEqual(Client(log=lambda m: None).transport, "token")
        with mock.patch.dict("os.environ", {}, clear=True), mock.patch.object(github.shutil, "which", return_value=None):
            self.assertEqual(Client(log=lambda m: None).transport, "anon")


class Decode(unittest.TestCase):
    def test_decode_readme(self):
        payload = {"content": base64.b64encode("héllo".encode()).decode(), "encoding": "base64", "name": "README.md", "sha": "abc"}
        self.assertEqual(decode_readme(payload), ("héllo", "README.md", "abc"))

    def test_decode_non_base64(self):
        self.assertEqual(decode_readme({"encoding": "none"})[0], "")


if __name__ == "__main__":
    unittest.main()
