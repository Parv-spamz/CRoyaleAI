"""CPU checks against the prepared or installed entry, with no device inputs."""
import importlib
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
sys.path[:0] = [str(ROOT), str(ROOT/'scratchpad/gauntlet/L68/live_reader')]
entry = importlib.import_module(sys.argv[1])
sys.modules['live_play'] = entry
import hashlib
print('ENTRY_SOURCE_SHA256', hashlib.sha256(Path(entry.__file__).read_bytes()).hexdigest(), flush=True)
import pytest
raise SystemExit(pytest.main([
    'pipeline/tests/test_live_checkpoint.py',
    'scratchpad/gauntlet/L68/live_reader/test_live_entry.py',
    'scratchpad/gauntlet/L68/live_reader/test_live_play_clock.py',
    'scratchpad/gauntlet/L68/live_reader/test_friend_nav.py',
    'pipeline/tests/test_live_mem.py',
    'pipeline/tests/test_live_gen_afford.py',
    'pipeline/tests/test_decision_options.py', '-q',
]))
