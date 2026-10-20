"""Dependency-free arithmetic and secret-printing self-checks."""
import ast
from pathlib import Path

import discord_clip


assert discord_clip.clip_window(200, 60) == (140, 60)
assert discord_clip.clip_window(45, 60) == (0, 45)
assert discord_clip.clip_window(60, 60) == (0, 60)
assert discord_clip.clip_window(200, 15.5) == (184.5, 15.5)
assert discord_clip.clip_window(200, 90) == (140, 60)
assert discord_clip.bitrate_kbps(60) == 1228
assert discord_clip.bitrate_kbps(45) == 1638

for invalid in (0, -1, float("nan"), float("inf")):
    for function, arguments in (
        (discord_clip.clip_window, (invalid, 60)),
        (discord_clip.clip_window, (60, invalid)),
        (discord_clip.bitrate_kbps, (invalid,)),
    ):
        try:
            function(*arguments)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid duration accepted")

source = Path(discord_clip.__file__).read_text(encoding="utf-8")
tree = ast.parse(source)
assert any(isinstance(node, ast.Name) and node.id == "webhook_url" for node in ast.walk(tree))
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and (
        isinstance(node.func, ast.Name) and node.func.id == "print"
        or isinstance(node.func, ast.Attribute) and node.func.attr == "print"
    ):
        assert not any(isinstance(child, ast.Name) and child.id in {"webhook_url", "url"}
                       for child in ast.walk(node)), "Webhook URL passed to print()"

print("discord_clip self-checks passed")
