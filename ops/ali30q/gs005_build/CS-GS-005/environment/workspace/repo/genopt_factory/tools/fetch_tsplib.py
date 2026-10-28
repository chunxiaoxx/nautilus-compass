"""TSPLIB symmetric TSP instance fetcher.

Downloads from http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/ (legacy mirror)
and the official Reinelt archive. Uses stable SHA-256 + SOURCE.txt provenance.

Selected instances (mixed sizes; small for quick eval, large for Hard grading):
  - ts225           (225 cities, TSPLIB mid)
  - pr1002          (1002 cities, TSPLIB large)
  - d2103           (2103 cities, TSPLIB large)
  - rl5915          (5915 cities, TSPLIB very large)
  - burma14         (14 cities, classic toy)
  - ulysses22       (22 cities, classic small)

Known optimal tour lengths come from TSPLIB official optimal tours file:
http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/STSP.html
"""

import hashlib
import json
import os
import sys
import urllib.request


# Selected (name, url, optimum_length)
INSTANCES = [
    ("burma14",  "http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/burma14.tsp.gz",  3323.0),
    ("ulysses22","http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/ulysses22.tsp.gz",  7013.0),
    ("ts225",    "http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/ts225.tsp.gz",     126643.0),
    ("pr1002",   "http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pr1002.tsp.gz",    259045.0),
    ("d2103",    "http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/d2103.tsp.gz",     80450.0),
    ("rl5915",   "http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/rl5915.tsp.gz",    565530.0),
]


def _parse_gz_tsp(path_gz):
    import gzip
    with gzip.open(path_gz, "rt", encoding="utf-8") as f:
        text = f.read()

    node_coords = []
    in_nodes = False
    for line in text.splitlines():
        line = line.strip()
        if line.upper() == "NODE_COORD_SECTION":
            in_nodes = True
            continue
        if in_nodes:
            if not line or line.upper() == "EOF":
                break
            parts = line.split()
            if len(parts) >= 3:
                # parts[0] = id (1-indexed in TSPLIB), parts[1]=x, parts[2]=y
                x, y = float(parts[1]), float(parts[2])
                node_coords.append((x, y))
    return node_coords


def _write_source(out_dir, sources):
    src_path = os.path.join(out_dir, "SOURCE.txt")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write("Provenance: TSPLIB symmetric TSP instances (Reinelt 1991)\n")
        f.write("Mirror: http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/\n\n")
        for name, url, sha256 in sources:
            f.write(f"{name}\t{sha256}\t{url}\n")


def main():
    if len(sys.argv) >= 2:
        out_dir = os.path.abspath(sys.argv[1])
    else:
        out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                               "..", "data"))
    os.makedirs(out_dir, exist_ok=True)
    inst_dir = os.path.join(out_dir, "instances")
    os.makedirs(inst_dir, exist_ok=True)

    optima = {}
    sources = []
    for name, url, optimum in INSTANCES:
        cache = os.path.join(out_dir, f"{name}.tsp.gz")
        if not os.path.exists(cache):
            print(f"downloading {name} from {url} ...", flush=True)
            try:
                urllib.request.urlretrieve(url, cache)
            except Exception as exc:
                print(f"  download failed: {exc}", file=sys.stderr)
                continue
        sha = hashlib.sha256(open(cache, "rb").read()).hexdigest()
        sources.append((name, url, sha))
        coords = _parse_gz_tsp(cache)
        # Re-index to 0-based (TSPLIB is 1-based, we use 0-based internally)
        instance = {
            "name": name,
            "dimension": len(coords),
            "node_coords": coords,
        }
        with open(os.path.join(inst_dir, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(instance, f, ensure_ascii=False)
        optima[name] = optimum
        print(f"  {name}: {len(coords)} cities · optimum={optimum}", flush=True)

    with open(os.path.join(out_dir, "optima.json"), "w", encoding="utf-8") as f:
        json.dump(optima, f, indent=1, ensure_ascii=False)
    _write_source(out_dir, sources)
    print(f"wrote optima.json + {len(optima)} instances to {out_dir}")


if __name__ == "__main__":
    main()