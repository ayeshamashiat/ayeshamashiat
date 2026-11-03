#!/usr/bin/env python3
"""
Local only. Replaces the placeholder lines in data/mom-lines.json with lines from the
Touch Grass, Babu Mom GGUF, run through llama.cpp's llama-server. CI never runs this.

  python scripts/mom_lines.py                                  # every bucket, 15 lines each
  python scripts/mom_lines.py --buckets busy,streak --per-bucket 15
  python scripts/mom_lines.py --dry-run --per-bucket 2         # print, write nothing
  MOM_GGUF=/path/to/mom-v2-q4_k_m.gguf LLAMA_SERVER=/path/to/llama-server python scripts/mom_lines.py

Same setup as mom/make_starter_bank.py in Touch-Grass-Babu: no system prompt (the persona
is distilled into the weights), thinking off, one user turn that starts with a context tag,
then the situation in the kid's words. The situations below are about coding instead of
scrolling; change them with --prompts my-prompts.json ({"busy": "i made 14 commits today", ...}).

A bucket's placeholders are only replaced once it has --per-bucket good lines, so a short
run never leaves a bucket half-done. 15 per bucket lets the README go 14 days without a repeat.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from activity import BUCKETS, LINE_MAX, DataError, ROOT, load_lines  # noqa: E402

MODEL = os.environ.get("MOM_GGUF", "/mnt/data/Documents/Hackathon/HACKTOBERFEST_2026/week1/mom/models/mom-v2-q4_k_m.gguf")
SERVER = os.environ.get("LLAMA_SERVER", "/mnt/data/devtools/llama.cpp/build/bin/llama-server")

TAG = "[time: 18:40 | app: GitHub | today: 0h20m]"
SITUATIONS = {  # what the kid tells Mom, one per bucket
    "quiet_short": "i haven't pushed any code for two days",
    "quiet_long": "i haven't committed anything to github in nine days",
    "quiet_extreme": "i haven't written a single line of code in three weeks",
    "steady": "i pushed a couple of small commits today, nothing big",
    "busy": "i made 14 commits today and fixed a lot of bugs",
    "streak": "i've committed code every single day for eight days straight",
    "shipped": "i just published a new release of my project on github",
}

# A line has to be about coding, fit in a README line, and sound like Mom, not like a model.
CODING = re.compile(r"\b(code|coding|commit\w*|push\w*|github|repo\w*|bug\w*|laptop|keyboard|release\w*|"
                    r"ship\w*|project\w*|deploy\w*|terminal|branch\w*|program\w*|computer|screen|version)\b", re.I)
BAD = re.compile(r"<think>|</think>|<\|im_|\bas an ai\b|[\U0001F300-\U0001FAFF]", re.I)


def prompt_for(situation, tag=TAG):
    return f"<|im_start|>user\n{tag} {situation}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


def is_good(text):
    return 20 <= len(text) <= LINE_MAX and not BAD.search(text) and bool(CODING.search(text))


def start_server(model, server, port, threads):
    if not Path(model).is_file():
        raise SystemExit(f"model not found: {model}\n(set MOM_GGUF or pass --model)")
    if not Path(server).is_file():
        raise SystemExit(f"llama-server not found: {server}\n(set LLAMA_SERVER or pass --server)")
    proc = subprocess.Popen([server, "-m", model, "-c", "1024", "-np", "1", "-t", str(threads), "--port", str(port)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    for _ in range(180):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2)
            return proc
        except Exception:
            if proc.poll() is not None:
                raise SystemExit("llama-server exited while loading the model")
            time.sleep(1)
    proc.kill()
    raise SystemExit("llama-server did not start")


def generate(port, prompt):
    # Sampling from the model card: temperature 0.85, top_k 40, top_p 0.95, ~100 tokens.
    body = json.dumps({"prompt": prompt, "n_predict": 100, "temperature": 0.85, "top_k": 40, "top_p": 0.95,
                       "stop": ["<|im_end|>"], "cache_prompt": False}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}/completion", body, {"Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(req, timeout=300).read())["content"]
    return " ".join(out.split()).strip('"').strip()


def lines_for(port, bucket, situation, n, tag=TAG, tries_each=6):
    got, tries = [], 0
    while len(got) < n and tries < n * tries_each:
        tries += 1
        try:
            text = generate(port, prompt_for(situation, tag))
        except Exception as e:
            print(f"  ({bucket}: {e})", flush=True)
            time.sleep(3)
            continue
        if is_good(text) and text not in got:
            got.append(text)
            print(f"[{bucket} {len(got)}/{n}] {text}", flush=True)
    return got


def save(path, doc):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    load_lines(tmp)  # never write a file the nightly job would reject
    tmp.replace(path)


def main():
    ap = argparse.ArgumentParser(description="Swap Mom's placeholder lines for real model lines (local only).")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--server", default=SERVER)
    ap.add_argument("--port", type=int, default=8089)
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--buckets", default=",".join(BUCKETS))
    ap.add_argument("--per-bucket", type=int, default=15)
    ap.add_argument("--tag", default=TAG, help="context tag the app puts before the kid's words (its today: field "
                    "is screen time, which Mom may quote back)")
    ap.add_argument("--prompts", type=Path, help="JSON {bucket: situation} to override the built-in ones")
    ap.add_argument("--lines", type=Path, default=ROOT / "data/mom-lines.json")
    ap.add_argument("--dry-run", action="store_true", help="print lines, don't touch the file")
    args = ap.parse_args()

    buckets = [b.strip() for b in args.buckets.split(",") if b.strip()]
    unknown = set(buckets) - set(BUCKETS)
    if unknown:
        raise SystemExit(f"unknown bucket(s): {sorted(unknown)}")
    situations = {**SITUATIONS, **(json.loads(args.prompts.read_text()) if args.prompts else {})}
    doc = json.loads(args.lines.read_text(encoding="utf-8"))

    server = start_server(args.model, args.server, args.port, args.threads)
    short = []
    try:
        for b in buckets:
            got = lines_for(args.port, b, situations[b], args.per_bucket, args.tag)
            if len(got) < args.per_bucket:
                short.append(f"{b} ({len(got)}/{args.per_bucket})")
                continue
            if args.dry_run:
                continue
            doc["lines"] = [ln for ln in doc["lines"] if ln["bucket"] != b] + [
                {"id": f"{b}-m{i:02d}", "bucket": b, "text": t, "source": "model"} for i, t in enumerate(got, 1)]
            try:
                save(args.lines, doc)
            except DataError as e:
                raise SystemExit(f"refusing to write {args.lines}: {e}")
            print(f"  replaced {b}", flush=True)
    finally:
        server.terminate()

    if short:
        print(f"kept placeholders for: {', '.join(short)}; rerun with --buckets for those")
    left = sum(ln["source"] == "placeholder" for ln in doc["lines"])
    print(f"{left} placeholder line(s) left" + ("" if left else "; the README will now credit the model"))


if __name__ == "__main__":
    main()
