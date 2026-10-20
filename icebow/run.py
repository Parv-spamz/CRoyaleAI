"""Bootstrap: add src/ to sys.path and dispatch to the CLI."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

BANNER = r"""
  +-------------------------------------------------------------+
  |                        CROYALE-AI                           |
  |         Neural Imitation & Reinforcement Learning Suite     |
  +-------------------------------------------------------------+
"""

from clashrl.cli import main  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) <= 1 or any(h in sys.argv for h in ("--help", "-h", "models")):
        print(BANNER)
    main()
