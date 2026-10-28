"""Fetch & parse OR-Library job-shop instances into per-instance JSON files.

Source: J.E. Beasley's OR-Library, file jobshop1.txt
  http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/jobshop1.txt

The file bundles the classic ft/la/abz/orb/swv/yn instances in the standard
"n m" + n rows of (machine, duration) pairs format, each preceded by a
"instance <name>" marker line.

Usage:
    python fetch_orlib_jssp.py --out <task>/data --names ft06 ft10 la01 la16 la21 la36

Writes:  <out>/instances/<name>.json  +  sha256 of the raw source into <out>/SOURCE.txt
Optima (proven) for the classic set are embedded below and written to optima.json.
"""

import argparse
import hashlib
import json
import os
import re
import urllib.request

URL = "http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/jobshop1.txt"

# Proven optimal makespans (Beasley OR-Library / literature, all long-settled).
KNOWN_OPTIMA = {
    "ft06": 55, "ft10": 930, "ft20": 1165,
    "la01": 666, "la02": 655, "la03": 597, "la04": 590, "la05": 593,
    "la06": 926, "la07": 890, "la08": 863, "la09": 951, "la10": 958,
    "la11": 1222, "la12": 1039, "la13": 1150, "la14": 1292, "la15": 1207,
    "la16": 945, "la17": 784, "la18": 848, "la19": 842, "la20": 902,
    "la21": 1046, "la22": 927, "la23": 1032, "la24": 935, "la25": 977,
    "la26": 1218, "la27": 1235, "la28": 1216, "la29": 1152, "la30": 1355,
    "la31": 1784, "la32": 1850, "la33": 1719, "la34": 1721, "la35": 1888,
    "la36": 1268, "la37": 1397, "la38": 1196, "la39": 1233, "la40": 1222,
    "abz5": 1234, "abz6": 943, "orb01": 1059, "orb02": 888, "orb03": 1005,
    "orb04": 1005, "orb05": 887, "orb06": 1010, "orb07": 397, "orb08": 899,
    "orb09": 934, "orb10": 944,
}


def fetch(url=URL, cache=".orlib_jobshop1.txt"):
    if os.path.exists(cache):
        raw = open(cache, "rb").read()
    else:
        raw = urllib.request.urlopen(url, timeout=60).read()
        open(cache, "wb").write(raw)
    return raw


def parse(raw_text):
    """Return {name: instance_dict} for every instance in jobshop1.txt."""
    lines = raw_text.splitlines()
    instances = {}
    i = 0
    current_name = None
    while i < len(lines):
        line = lines[i].strip()
        m = re.match(r"instance\s+(\S+)", line)
        if m:
            current_name = m.group(1)
            # skip separator/description lines until the "n m" header
            i += 1
            while i < len(lines):
                header = lines[i].strip()
                if re.fullmatch(r"\d+\s+\d+", header):
                    break
                i += 1
            n, mm = map(int, lines[i].split())
            jobs = []
            for r in range(1, n + 1):
                nums = list(map(int, lines[i + r].split()))
                ops = [[nums[c], nums[c + 1]] for c in range(0, 2 * mm, 2)]
                jobs.append(ops)
            instances[current_name] = {
                "name": current_name,
                "num_jobs": n,
                "num_machines": mm,
                "jobs": jobs,
            }
            i += n
        i += 1
    return instances


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--names", nargs="+", required=True)
    args = ap.parse_args()

    raw = fetch()
    sha = hashlib.sha256(raw).hexdigest()
    all_instances = parse(raw.decode("utf-8", errors="replace"))

    inst_dir = os.path.join(args.out, "instances")
    os.makedirs(inst_dir, exist_ok=True)
    optima = {}
    for name in args.names:
        if name not in all_instances:
            raise SystemExit(f"instance {name!r} not found in {URL}")
        if name not in KNOWN_OPTIMA:
            raise SystemExit(f"no proven optimum recorded for {name!r}")
        with open(os.path.join(inst_dir, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(all_instances[name], f, indent=1)
        optima[name] = KNOWN_OPTIMA[name]

    with open(os.path.join(args.out, "optima.json"), "w", encoding="utf-8") as f:
        json.dump(optima, f, indent=1)
    with open(os.path.join(args.out, "SOURCE.txt"), "w", encoding="utf-8") as f:
        f.write(f"source: {URL}\nsha256(jobshop1.txt) = {sha}\n"
                "optima: proven optimal makespans from OR-Library / JSSP literature\n")
    print(f"wrote {len(optima)} instances to {inst_dir}; sha256={sha[:16]}...")


if __name__ == "__main__":
    main()
