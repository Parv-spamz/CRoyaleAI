"""gen_v3.1 FULL public re-drive (lead, 2026-10-04; owner: "do the full re-drive NOW"). Every IL corpus job in
full_jobs.json, abilities driven, native form ids, projectiles (with target point -> exact time-to-impact per frame),
area effects (with timers), full observation before every play, one compact frame every --k ticks.
Job-level queue shared by the engine slots of ONE machine; job i writes to <out>/j<iii>/ (own summary.jsonl, so no
two slots share a file) and drops JOB_DONE there when replay_batch exits 0. Restartable: done jobs are skipped and
replay_batch skips tags already in a job's summary. Machines split the queue with --first/--last (job indices).
  VM:     nohup setsid python3 research/sandbox_tools/run_public.py --ports 37031,37032,37033,37034 --last 63 > run_public.log 2>&1 < /dev/null &
  laptop: python research/sandbox_tools/run_public.py --ports 37031,37032 --first 64 --python <venv python>"""
import argparse, json, os, queue, subprocess, sys, threading, time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--jobs", default="full_jobs.json")
ap.add_argument("--ports", required=True)
ap.add_argument("--k", type=int, default=10)
ap.add_argument("--first", type=int, default=0)
ap.add_argument("--last", type=int, default=10**9)
ap.add_argument("--python", default=sys.executable)
a = ap.parse_args()
jobs = json.loads(Path(a.jobs).read_text())
q = queue.Queue()
for i, j in enumerate(jobs):
    if a.first <= i <= a.last and not (Path(j["out"]) / ("j%03d" % i) / "JOB_DONE").exists():
        q.put((i, j))
print("queued", q.qsize(), "jobs", time.strftime("%H:%M:%S"), flush=True)


def slot(port):
    while True:
        try:
            i, j = q.get_nowait()
        except queue.Empty:
            return
        out = Path(j["out"]) / ("j%03d" % i)
        cmd = [a.python, "-u", "research/sandbox_tools/replay_batch.py", "--crawl", j["crawl"], "--plays-file",
               j["plays_file"], "--tags", j["tags"], "--out", str(out), "--port", str(port), "--seed", "424242",
               "--level", "11", "--elixir-slack", "40", "--tail-cap", "7200", "--drive-abilities", "--record-full",
               "--record-native", "--record-public-objects", "--record-every", str(a.k), "--record-plays",
               "--determinism-every", "0"]
        out.mkdir(parents=True, exist_ok=True)
        with open("run_public_%d.log" % port, "a") as log:
            log.write("=== %s job %d -> %s\n" % (time.strftime("%H:%M:%S"), i, out)); log.flush()
            rc = subprocess.call(cmd, stdout=log, stderr=subprocess.STDOUT)
            log.write("=== %s rc %d\n" % (time.strftime("%H:%M:%S"), rc))
        if rc == 0:
            (out / "JOB_DONE").write_text(time.strftime("%Y-%m-%dT%H:%M:%S"))
        print("job", i, "port", port, "rc", rc, time.strftime("%H:%M:%S"), flush=True)


ts = [threading.Thread(target=slot, args=(int(p),)) for p in a.ports.split(",")]
for t in ts: t.start()
for t in ts: t.join()
print("ALL_DONE", time.strftime("%H:%M:%S"), flush=True)
