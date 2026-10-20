"""New public hand successor controls; no past experiment is rerun."""
import subprocess
import sys

p=subprocess.run([sys.executable,'-m','pytest','-q','pipeline/tests/test_hand_integration.py'])
if p.returncode:raise SystemExit(p.returncode)
print('HAND_SUCCESSOR_VERIFIED')
