"""CPU-only search checks with Windows-sandbox-readable temporary directories."""
import contextlib
import json
import os
import shutil
import sys
import tempfile
import types
import uuid
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))
for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[key] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""


@contextlib.contextmanager
def task_tempdir(*args, **kwargs):
    # Python 3.13's Windows mode=0700 temp ACL excludes the sandbox identity.
    # Normal mkdir inherits this task directory's readable/writable ACL instead.
    path = HERE / ("test_tmp_" + uuid.uuid4().hex)
    path.mkdir()
    try:
        yield str(path)
    finally:
        resolved = path.resolve()
        assert resolved.parent == HERE and resolved.name.startswith("test_tmp_")
        shutil.rmtree(resolved)


def census_option_checks():
    from pipeline import search_s0 as S
    from pipeline import rl_royale as RL
    default = "scratchpad/gauntlet/L68/selfplay/loadable_decks.json"
    assert S.CENSUS == default
    init_worker = S._init_worker
    # Real CLI -> worker args, with policy loading and matches replaced by stubs.
    for selected in (None, "scratchpad/gauntlet/L70/pool_forms/loadable_decks.json",
                     str(HERE / "loadable_decks.json")):
        captured = []
        with task_tempdir() as tmp, patch.object(S, "_init_worker", side_effect=captured.append), \
                patch.object(S, "sha256", return_value="stub"):
            argv = ["--out", str(Path(tmp) / "run"), "--seeds", "0:0"]
            if selected is not None:
                argv += ["--census", selected]
            assert S.main(argv) == 0
            expected = selected or default
            assert captured[0]["census"] == expected
            metadata = json.loads((Path(tmp) / "run/run.json").read_text())
            assert metadata.get("census", default) == expected
            assert ("census" in metadata) == (expected != default)
            # Worker -> actual league loader, without models, matches, or GPU access.
            for args in (captured[0], {k: v for k, v in captured[0].items() if k != "census"}):
                expected_path = REPO / args.get("census", default)
                with patch.object(S.E, "load_policy", return_value=(None, {"grid": "lattice"})), \
                        patch.object(S, "Runner"), patch.object(S, "live_cfg", return_value={}), \
                        patch.object(RL, "league_decks", wraps=RL.league_decks) as loader:
                    init_worker(args)
                    loader.assert_called_once_with(expected_path)
                    raw = json.loads(expected_path.read_text())["decks"]
                    by_rank = {f"r{x['rank']}": x["engine"] for x in raw}
                    assert all(x["engine"] == by_rank[x["name"]] for x in S._W["census"])
        S._W.clear()
    print("CENSUS_OPTION_VERIFIED")

    # Prove omitted --census preserves default output bytes, including run metadata.
    baseline = types.ModuleType("search_s0_before")
    baseline.__file__ = str(REPO / "pipeline/search_s0.py")
    exec(compile((HERE / "search_s0.before.py.txt").read_text(), baseline.__file__, "exec"), vars(baseline))
    outputs = []
    with task_tempdir() as tmp:
        out = Path(tmp) / "run"
        for module in (baseline, S):
            with patch.object(module, "_init_worker"), patch.object(module, "sha256", return_value="stub"), \
                    patch.object(module.time, "strftime", return_value="fixed"), \
                    patch.object(module.time, "perf_counter", return_value=0.0):
                assert module.main(["--out", str(out), "--seeds", "0:0"]) == 0
            outputs.append({p.name: p.read_bytes() for p in out.iterdir()})
            for p in out.iterdir():
                p.unlink()
        assert outputs[0] == outputs[1]
    print("DEFAULT_OUTPUT_BYTES_VERIFIED")


if __name__ == "__main__":
    import pytest
    with patch.object(tempfile, "TemporaryDirectory", task_tempdir):
        result = pytest.main(["-q", "-p", "no:cacheprovider",
                              "pipeline/tests/test_search_s0.py",
                              "pipeline/tests/test_scorer_v2.py",
                              "pipeline/tests/test_royale_forms.py::TestPlumbing::test_search_s0_flag"])
    if result:
        raise SystemExit(result)
    census_option_checks()
    print("SEARCH_CHECKS_VERIFIED")
