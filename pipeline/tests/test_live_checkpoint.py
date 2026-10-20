from pathlib import Path
import pytest

from pipeline.live_checkpoint import resolve_checkpoint


def fixture(tmp_path):
    chosen = tmp_path / 'accepted.pt'
    chosen.write_bytes(b'accepted')
    pointer = tmp_path / 'CKPT_OVERRIDE'
    pointer.write_text('accepted.pt')
    return chosen, pointer


def test_selection_ignores_newer_experiment_and_resolves_from_repo(tmp_path, monkeypatch):
    chosen, pointer = fixture(tmp_path)
    (tmp_path / 'new_rejected.pt').write_bytes(b'newer is not better')
    monkeypatch.chdir(tmp_path.parent)
    result = resolve_checkpoint(None, pointer, tmp_path)
    assert result.path == chosen and len(result.sha256) == 64 and not result.changed()
    pointer.write_text(str(chosen))  # same file with absolute spelling
    assert not result.changed()
    pointer.write_text('new_rejected.pt')
    assert result.changed()


def test_explicit_checkpoint_wins_and_ignores_deployment_changes(tmp_path):
    chosen, pointer = fixture(tmp_path)
    explicit = tmp_path / 'explicit.pt'
    explicit.write_bytes(b'explicit')
    result = resolve_checkpoint('explicit.pt', pointer, tmp_path)
    assert result.path == explicit and result.source == 'explicit --ckpt'
    pointer.unlink()
    assert not result.changed()


@pytest.mark.parametrize('contents', [None, '', 'missing.pt', 'one.pt\ntwo.pt'])
def test_broken_selection_never_falls_back(tmp_path, contents):
    chosen, pointer = fixture(tmp_path)
    if contents is None:
        pointer.unlink()
    else:
        pointer.write_text(contents)
    with pytest.raises(ValueError):
        resolve_checkpoint(None, pointer, tmp_path)


def test_removed_pointer_ends_default_run(tmp_path):
    chosen, pointer = fixture(tmp_path)
    result = resolve_checkpoint(None, pointer, tmp_path)
    pointer.unlink()
    assert result.changed()


def test_missing_explicit_fails_even_with_good_pointer(tmp_path):
    chosen, pointer = fixture(tmp_path)
    with pytest.raises(ValueError, match='does not exist'):
        resolve_checkpoint('missing.pt', pointer, tmp_path)
