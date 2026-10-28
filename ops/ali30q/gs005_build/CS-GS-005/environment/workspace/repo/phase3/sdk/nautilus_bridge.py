"""
Nautilus Bridge — Drop-in integration for any project.

Copy this ONE file to your project. Zero dependencies beyond stdlib.

Usage (创投雷达):
    from nautilus_bridge import nautilus
    report = nautilus.submit_and_wait("Generate VC daily report", events_json, task_type="vc_daily_report")

Usage (禅心AI):
    from nautilus_bridge import nautilus
    result = nautilus.submit_and_wait("Expand quantum interpretation for 金刚经第一品", content, task_type="research_synthesis")

Usage (batch):
    tasks = nautilus.submit_batch([
        {"title": "金刚经第1品", "description": "...", "task_type": "research_synthesis"},
        {"title": "金刚经第2品", "description": "...", "task_type": "research_synthesis"},
    ])
    results = nautilus.wait_batch(tasks)
"""
import json
import os
import time
import urllib.request
import urllib.error

NAUTILUS_URL = os.getenv("NAUTILUS_URL", "https://www.nautilus.social")
NAUTILUS_TENANT_KEY = os.getenv("NAUTILUS_TENANT_KEY", "")


def _post(path, data, headers=None):
    h = {"Content-Type": "application/json"}
    if NAUTILUS_TENANT_KEY:
        h["X-Tenant-Key"] = NAUTILUS_TENANT_KEY
    if headers:
        h.update(headers)
    req = urllib.request.Request(
        f"{NAUTILUS_URL}{path}",
        json.dumps(data, ensure_ascii=False).encode("utf-8"),
        h,
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body[:200]}"}
    except Exception as e:
        return {"error": str(e)}


def _get(path):
    h = {}
    if NAUTILUS_TENANT_KEY:
        h["X-Tenant-Key"] = NAUTILUS_TENANT_KEY
    req = urllib.request.Request(f"{NAUTILUS_URL}{path}", headers=h)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read())
    except Exception as e:
        return {"error": str(e)}


class NautilusBridge:
    """One-line integration with Nautilus platform."""

    def submit_task(self, title, description, task_type="general_computation"):
        """Submit a task. Returns task_id or None."""
        resp = _post("/api/academic/submit", {
            "title": title[:200],
            "description": description[:5000],
            "task_type": task_type,
        })
        return resp.get("task_id")

    def get_task(self, task_id):
        """Get task status and result."""
        resp = _get(f"/api/academic/{task_id}")
        data = resp.get("data", resp)
        return {
            "status": data.get("status", "unknown"),
            "result": data.get("result_output") or data.get("result"),
            "quality": data.get("quality_rating"),
        }

    def submit_and_wait(self, title, description, task_type="general_computation",
                        timeout=600, poll_interval=10):
        """Submit task and wait for completion. Returns result text or None."""
        task_id = self.submit_task(title, description, task_type)
        if not task_id:
            return None

        deadline = time.time() + timeout
        while time.time() < deadline:
            info = self.get_task(task_id)
            if info["status"] == "completed":
                return info["result"]
            if info["status"] == "failed":
                return None
            time.sleep(poll_interval)

        return None  # timeout

    def submit_batch(self, tasks, delay=2):
        """Submit multiple tasks. Returns list of task_ids.

        tasks: [{"title": str, "description": str, "task_type": str}, ...]
        """
        ids = []
        for t in tasks:
            tid = self.submit_task(
                t.get("title", ""),
                t.get("description", ""),
                t.get("task_type", "general_computation"),
            )
            ids.append(tid)
            if delay:
                time.sleep(delay)
        return ids

    def wait_batch(self, task_ids, timeout=1800, poll_interval=15):
        """Wait for all tasks to complete. Returns {task_id: result_text}."""
        results = {}
        deadline = time.time() + timeout

        while time.time() < deadline:
            pending = [tid for tid in task_ids if tid and tid not in results]
            if not pending:
                break

            for tid in pending:
                info = self.get_task(tid)
                if info["status"] in ("completed", "failed"):
                    results[tid] = info["result"]

            if len(results) < len([t for t in task_ids if t]):
                time.sleep(poll_interval)

        return results

    def generate_vc_report(self, report_date, events):
        """Shortcut for VC Radar daily report generation."""
        resp = _post("/api/vc-radar/generate", {
            "report_date": report_date,
            "events": events,
        })
        data = resp.get("data", resp)
        job_id = data.get("job_id")
        if not job_id:
            return None

        # Poll for completion
        for _ in range(60):
            time.sleep(10)
            result = _get(f"/api/vc-radar/job/{job_id}")
            job_data = result.get("data", result)
            if job_data.get("status") == "completed":
                return job_data.get("assembled_report")
            if job_data.get("status") == "failed":
                return None

        return None

    def health(self):
        """Get platform health score."""
        resp = _get("/api/platform/health")
        data = resp.get("data", resp)
        return data.get("health_score")

    def session_start(self, project="nautilus"):
        """Get session context for a Claude Code session."""
        return _post("/api/session/start", {"project": project})


# Global singleton
nautilus = NautilusBridge()
