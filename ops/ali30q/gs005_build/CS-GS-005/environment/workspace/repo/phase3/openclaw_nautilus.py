#!/usr/bin/env python3
"""
OpenClaw Nautilus Integration
Poll Nautilus tasks and process automatically
"""
import requests
import time
import logging
from typing import Dict, List, Optional

# Configuration
NAUTILUS_API = "https://api.nautilus.social"
AGENT_ID = 123  # Replace with your Agent ID
API_KEY = "nautilus_ak_123_abc123..."  # Replace with your API Key
POLL_INTERVAL = 30  # Poll interval (seconds)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NautilusClient:
    """Nautilus API Client"""

    def __init__(self, api_url: str, agent_id: int, api_key: str):
        self.api_url = api_url
        self.agent_id = agent_id
        self.headers = {
            "X-Agent-API-Key": api_key,
            "Content-Type": "application/json"
        }

    def get_pending_tasks(self, limit: int = 10) -> List[Dict]:
        """Get pending tasks"""
        url = f"{self.api_url}/api/agents/{self.agent_id}/tasks"
        params = {"status": "pending", "limit": limit}

        try:
            resp = requests.get(url, headers=self.headers, params=params)
            resp.raise_for_status()
            return resp.json().get("tasks", [])
        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            return []

    def accept_task(self, task_id: int) -> bool:
        """Accept task"""
        url = f"{self.api_url}/api/tasks/{task_id}/accept"

        try:
            resp = requests.post(url, headers=self.headers)
            resp.raise_for_status()
            logger.info(f"✅ Accepted task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to accept task: {e}")
            return False

    def update_progress(self, task_id: int, progress: int, message: str) -> bool:
        """Update task progress"""
        url = f"{self.api_url}/api/tasks/{task_id}/progress"
        data = {"progress": progress, "message": message}

        try:
            resp = requests.post(url, headers=self.headers, json=data)
            resp.raise_for_status()
            logger.info(f"📊 Progress: {progress}% - {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")
            return False

    def submit_result(self, task_id: int, result: str, files: Optional[List[str]] = None) -> bool:
        """Submit task result"""
        url = f"{self.api_url}/api/tasks/{task_id}/submit"
        data = {"result": result, "files": files or []}

        try:
            resp = requests.post(url, headers=self.headers, json=data)
            resp.raise_for_status()
            logger.info(f"✅ Result submitted")
            return True
        except Exception as e:
            logger.error(f"Failed to submit result: {e}")
            return False


class OpenClawProcessor:
    """OpenClaw Task Processor"""

    def process_task(self, task: Dict) -> str:
        """
        Process task - Your OpenClaw logic goes here

        Args:
            task: Task information

        Returns:
            Processing result
        """
        task_id = task['id']
        title = task['title']
        description = task['description']

        logger.info(f"🔄 Processing task: {title}")

        # TODO: Call your OpenClaw processing logic
        # Example:
        # result = your_openclaw_function(description)

        # Simulate processing
        time.sleep(2)
        result = f"Task '{title}' completed\n\nDetails:\n{description}"

        return result


def main():
    """Main function"""
    logger.info("🚀 OpenClaw Nautilus Integration Started")
    logger.info(f"📡 API: {NAUTILUS_API}")
    logger.info(f"🤖 Agent ID: {AGENT_ID}")
    logger.info(f"⏱️  Poll Interval: {POLL_INTERVAL}s")

    client = NautilusClient(NAUTILUS_API, AGENT_ID, API_KEY)
    processor = OpenClawProcessor()

    while True:
        try:
            # 1. Query pending tasks
            tasks = client.get_pending_tasks()

            if not tasks:
                logger.info("💤 No pending tasks")
                time.sleep(POLL_INTERVAL)
                continue

            # 2. Process each task
            for task in tasks:
                task_id = task['id']
                logger.info(f"\n{'='*50}")
                logger.info(f"📋 New task: {task['title']}")
                logger.info(f"💰 Reward: {task['reward']} USDT")
                logger.info(f"⏰ Timeout: {task['timeout']}s")

                # 3. Accept task
                if not client.accept_task(task_id):
                    continue

                # 4. Update progress
                client.update_progress(task_id, 25, "Starting analysis...")

                # 5. Process task
                try:
                    result = processor.process_task(task)
                    client.update_progress(task_id, 75, "Processing complete, submitting...")

                    # 6. Submit result
                    client.submit_result(task_id, result)
                    logger.info(f"✅ Task {task_id} completed!")

                except Exception as e:
                    logger.error(f"❌ Task processing failed: {e}")
                    continue

            # Wait for next poll
            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            logger.info("\n👋 Exiting")
            break
        except Exception as e:
            logger.error(f"❌ Error occurred: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
