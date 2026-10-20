"""Runtime pin, actual spawned actor startup, and failed-resume controls (CPU only)."""
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pipeline import royale_runtime as runtime


class _ActorResultPipe:
    """Synchronous result capture; the production feeder can drop a final error on exit."""
    def __init__(self, connection):
        self.connection = connection

    def cancel_join_thread(self):
        pass

    def put(self, message):
        self.connection.send(message)


class RuntimeFiles(unittest.TestCase):
    def test_missing_and_changed_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            file = root/'engine.py'
            file.write_bytes(b'reviewed')
            manifest = {'files': {'engine.py': hashlib.sha256(b'reviewed').hexdigest()}}
            runtime._verify_files(root, manifest)
            file.write_bytes(b'stale')
            with self.assertRaisesRegex(RuntimeError, 'changed'):
                runtime._verify_files(root, manifest)
            with self.assertRaisesRegex(RuntimeError, 'missing'):
                runtime._verify_files(root, {'files': {'missing.py': '0'}})
            with self.assertRaisesRegex(RuntimeError, 'outside'):
                runtime._verify_files(root, {'files': {'../outside.py': '0'}})

    def test_compiled_stamp_and_checkpoint_runtime_match(self):
        stamp = runtime.activate()
        self.assertEqual(stamp['pins']['RoyaleSim'], '015f9b0084afe574915e3f6ce2f0764c6dec6099')
        self.assertEqual(stamp['pins']['RoyaleGym'], '3117816366b00754da1b56c9543412e4706de62a')
        self.assertEqual(runtime.require_same(stamp), stamp)
        with self.assertRaisesRegex(RuntimeError, 'differs'):
            runtime.require_same(None)
        changed = json.loads(json.dumps(stamp))
        changed['pins']['RoyaleSim'] = 'old'
        with self.assertRaisesRegex(RuntimeError, 'differs'):
            runtime.require_same(changed)

    def test_old_preloaded_module_is_rejected_in_fresh_process(self):
        env = dict(os.environ, PYTHONPATH=str(runtime.REPO))
        result = subprocess.run([sys.executable, '-c',
            'import royalesim; from pipeline.royale_runtime import activate; activate()'],
            cwd=runtime.REPO, env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('unpinned Royale module', result.stderr)

    def test_data_override_is_rejected(self):
        with patch.dict(os.environ, ROYALESIM_DATA_DIR=str(runtime.REPO)):
            with self.assertRaisesRegex(RuntimeError, 'override'):
                runtime.activate()

    def test_standard_rl_entry_refuses_missing_runtime_before_training(self):
        from pipeline.rl_royale import main
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(runtime, 'MANIFEST', Path(folder)/'missing.json'), patch.object(runtime, '_STAMP', None):
                with self.assertRaisesRegex(RuntimeError, 'manifest missing'):
                    main(['--run', 'runtime-refusal-probe'])

    def test_checkpoint_and_actor_configuration_retain_stamp_and_refuse_old_resume(self):
        import torch
        from pipeline import rl_royale as RL
        from pipeline.tests.test_rl_royale import TestCheckpointRoundTrip, _tiny_model
        fixture = TestCheckpointRoundTrip()
        fixture.setUp()
        try:
            first = fixture._learner(_tiny_model(5))
            first.cfg = RL.load_config(runtime.REPO/'pipeline/rl_royale.yaml', [], smoke=False) | first.cfg
            first.grid = first.init_meta['args']['grid']
            first.runtime = runtime.activate()
            checkpoint = first._payload(None)
            self.assertEqual(checkpoint['rl']['runtime'], first.runtime)
            self.assertEqual(first.actor_base()['runtime'], first.runtime)
            path = fixture.tmp/'runtime.pt'
            torch.save(checkpoint, path)
            restored = fixture._learner(_tiny_model(9))
            restored.cfg = dict(first.cfg)
            restored.runtime = runtime.activate()
            restored._restore(path)
            for key, value in first.model.state_dict().items():
                self.assertTrue(torch.equal(value, restored.model.state_dict()[key]))
            del checkpoint['rl']['runtime']
            torch.save(checkpoint, path)
            with self.assertRaisesRegex(RuntimeError, 'Royale runtime differs'):
                restored._restore(path)
        finally:
            fixture.doCleanups()

    def test_actual_actor_spawn_checks_learner_stamp(self):
        from pipeline.rl_royale import actor_main
        ctx = mp.get_context('spawn')
        for expected, kind in [(runtime.activate(), 'ready'), (None, 'error')]:
            incoming = ctx.Queue()
            reader, writer = ctx.Pipe(duplex=False)
            base = dict(actor_threads=1, actor_device='cpu', d=16, layers=1,
                        gen=None, runtime=expected)
            proc = ctx.Process(target=actor_main, args=(0, 0, incoming, _ActorResultPipe(writer), base))
            proc.start()
            try:
                self.assertTrue(reader.poll(45), 'actor emitted no startup result')
                message = reader.recv()
                self.assertEqual(message[0], kind, message)
                if kind == 'error':
                    self.assertIn('Royale runtime differs', message[-1])
                else:
                    incoming.put(None)
                proc.join(timeout=15)
                self.assertFalse(proc.is_alive())
                self.assertEqual(proc.exitcode, 0)
            finally:
                if proc.is_alive():
                    proc.terminate()
                    proc.join()
                incoming.close()
                reader.close()
                writer.close()


if __name__ == '__main__':
    unittest.main()
