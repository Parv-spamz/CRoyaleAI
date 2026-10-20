"""Resolve the selected live checkpoint. Experiment recency is not acceptance."""
from dataclasses import dataclass
import hashlib
from pathlib import Path


@dataclass(frozen=True)
class LiveCheckpoint:
    path: Path
    source: str
    pointer: Path | None
    sha256: str
    root: Path

    def changed(self) -> bool:
        if self.pointer is None:
            return False
        # A removed/empty/broken deployment pointer is also a change: never
        # continue to another match on a silently stale deployment.
        try:
            return _selected_path(self.pointer, self.root) != self.path
        except (OSError, ValueError):
            return True

def _absolute(value, root):
    path = Path(value).expanduser()
    return (root / path).resolve() if not path.is_absolute() else path.resolve()


def _selected_path(pointer, root):
    value = pointer.read_text(encoding='utf-8-sig').strip()
    if not value or len(value.splitlines()) != 1:
        raise ValueError(f'Live checkpoint selection is empty or malformed: {pointer}')
    return _absolute(value, root)


def resolve_checkpoint(explicit, pointer, root):
    """An explicit argument wins; otherwise require the owner-selected pointer."""
    root = Path(root).resolve()
    pointer = _absolute(pointer, root) if pointer else None
    if explicit:
        path, source, followed = _absolute(explicit, root), 'explicit --ckpt', None
    else:
        if pointer is None or not pointer.is_file():
            raise ValueError(f'No selected live checkpoint at {pointer}; supply --ckpt or update CKPT_OVERRIDE')
        path, source, followed = _selected_path(pointer, root), str(pointer), pointer
    if not path.is_file():
        raise ValueError(f'Selected checkpoint does not exist: {path} (source: {source})')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return LiveCheckpoint(path, source, followed, digest, root)
