#!/usr/bin/env python3
import subprocess, sys, os
from xml.etree import ElementTree as ET

cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
xml = os.path.join(cwd, "_judge", "j.xml")
os.makedirs(os.path.dirname(xml), exist_ok=True)
subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-q", f"--junitxml={xml}"],
    capture_output=True, text=True, cwd=cwd,
)
try:
    root = ET.parse(xml).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    t = sum(int(s.attrib.get("tests", 0) or 0) for s in suites)
    f = sum(
        int(s.attrib.get("failures", 0) or 0) + int(s.attrib.get("errors", 0) or 0)
        for s in suites
    )
    print(round((t - f) / t, 4) if t else 0.0)
except Exception:
    print(0.0)
