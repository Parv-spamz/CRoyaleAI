"""Run the new reader tests plus relevant unchanged public observer contracts."""
import subprocess
import sys

result = subprocess.run([sys.executable, '-m', 'pytest', '-q',
    'pipeline/tests/test_opponent_hand.py', 'pipeline/tests/test_public_observation.py'], check=False)
if result.returncode:
    raise SystemExit(result.returncode)
print('OPPONENT_HAND_TESTS_PASSED')
