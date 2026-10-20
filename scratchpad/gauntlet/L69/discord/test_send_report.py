"""Offline delivery-contract checks; never reads credentials or contacts Discord."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('send_report', Path(__file__).with_name('send_report.py'))
sender = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sender)


class Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return b'{"id":"123456789"}'


class DeliveryTests(unittest.TestCase):
    def test_confirmed_delivery_is_not_repeated(self):
        calls = []

        def fake(request, timeout):
            calls.append(request)
            self.assertIn('wait=true', request.full_url)
            self.assertEqual(json.loads(request.data)['allowed_mentions'], {'parse': []})
            return Response()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / 'dummy.txt'
            config.write_text('https://discord.com/api/webhooks/123/dummy', encoding='utf-8')
            result = sender.deliver('newsletter-2026-10-05', '**Findings**\n\nExample.', root / 'out', config, fake)
            self.assertEqual(result['chunks'][0]['message_id'], '123456789')
            sender.deliver('newsletter-2026-10-05', 'Changed draft.', root / 'out', config, fake)
            self.assertEqual(len(calls), 1)

    def test_ambiguous_second_part_blocks_resend_of_both_parts(self):
        calls = []

        def fake(request, timeout):
            calls.append(request)
            if len(calls) == 2:
                raise TimeoutError('response was lost')
            return Response()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / 'dummy.txt'
            config.write_text('https://discord.com/api/webhooks/123/dummy', encoding='utf-8')
            text = 'A' * 1700 + '\n\n' + 'B' * 1700
            with self.assertRaises(RuntimeError):
                sender.deliver('partial', text, root / 'out', config, fake)
            receipt = json.loads((root / 'out/partial/delivery.json').read_text())
            self.assertEqual([c['status'] for c in receipt['chunks']], ['delivered', 'pending'])
            with self.assertRaises(RuntimeError):
                sender.deliver('partial', text, root / 'out', config, fake)
            self.assertEqual(len(calls), 2)

    def test_unicode_limits_and_mentions(self):
        parts = sender.split_message('\U0001f3f9' * 2000)
        self.assertTrue(all(sender.units(p) <= 2000 for p in parts))
        for text in ('@everyone hello', '<@123>', 'https://discord.com/api/webhooks/123/dummy', ''):
            with self.assertRaises(ValueError):
                sender.split_message(text)


if __name__ == '__main__':
    unittest.main()
