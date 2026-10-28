"""
Agent state persistence using PostgreSQL and Redis.

Enhanced with:
- State versioning
- Automatic backup and recovery
- Learning progress tracking
- Comprehensive error handling
"""
import json
import redis
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import hashlib
import pickle

from models.database import Agent, Task
from utils.database import get_db_context

logger = logging.getLogger(__name__)

# State version for compatibility tracking
STATE_VERSION = "1.0.0"


class StatePersistence:
    """
    Manage agent state persistence.

    Uses:
    - PostgreSQL: Long-term state (task history, earnings, learning progress)
    - Redis: Short-term state (current task, execution progress, temporary data)
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize state persistence.

        Args:
            redis_url: Redis connection URL
        """
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("StatePersistence initialized successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing StatePersistence: {e}")
            raise

    def save_agent_state(self, agent_id: int, state: Dict[str, Any], create_backup: bool = True):
        """
        Save agent state to Redis with versioning and backup.

        Args:
            agent_id: Agent ID
            state: State dictionary
            create_backup: Whether to create a backup of previous state
        """
        try:
            # Add metadata
            state_with_meta = {
                "version": STATE_VERSION,
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": agent_id,
                "data": state,
                "checksum": self._calculate_checksum(state)
            }

            key = f"agent:{agent_id}:state"

            # Create backup of existing state if requested
            if create_backup:
                existing_state = self.redis_client.get(key)
                if existing_state:
                    backup_key = f"agent:{agent_id}:state:backup:{datetime.utcnow().timestamp()}"
                    self.redis_client.set(backup_key, existing_state, ex=86400)  # 24 hour backup
                    logger.debug(f"Created backup for agent {agent_id}")

            # Save new state
            self.redis_client.set(key, json.dumps(state_with_meta), ex=3600)  # 1 hour expiry

            # Keep track of state history
            self._add_to_history(agent_id, state_with_meta)

            logger.info(f"Saved state for agent {agent_id} (version {STATE_VERSION})")

        except Exception as e:
            logger.error(f"Failed to save state for agent {agent_id}: {e}")
            raise

    def load_agent_state(self, agent_id: int, verify_checksum: bool = True) -> Optional[Dict[str, Any]]:
        """
        Load agent state from Redis with verification.

        Args:
            agent_id: Agent ID
            verify_checksum: Whether to verify state integrity

        Returns:
            State dictionary or None
        """
        try:
            key = f"agent:{agent_id}:state"
            state_json = self.redis_client.get(key)

            if not state_json:
                logger.debug(f"No state found for agent {agent_id}")
                return None

            state_with_meta = json.loads(state_json)

            # Verify version compatibility
            if state_with_meta.get("version") != STATE_VERSION:
                logger.warning(f"State version mismatch for agent {agent_id}: {state_with_meta.get('version')} vs {STATE_VERSION}")

            # Verify checksum if requested
            if verify_checksum and "checksum" in state_with_meta:
                data = state_with_meta.get("data", {})
                expected_checksum = state_with_meta.get("checksum")
                actual_checksum = self._calculate_checksum(data)

                if expected_checksum != actual_checksum:
                    logger.error(f"Checksum mismatch for agent {agent_id}, attempting recovery")
                    return self._recover_from_backup(agent_id)

            return state_with_meta.get("data", {})

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode state for agent {agent_id}: {e}")
            return self._recover_from_backup(agent_id)
        except Exception as e:
            logger.error(f"Failed to load state for agent {agent_id}: {e}")
            return None

    def save_task_progress(self, agent_id: int, task_id: int, progress: Dict[str, Any]):
        """
        Save task execution progress to Redis.

        Args:
            agent_id: Agent ID
            task_id: Task ID
            progress: Progress dictionary
        """
        key = f"agent:{agent_id}:task:{task_id}:progress"
        self.redis_client.set(key, json.dumps(progress), ex=7200)  # 2 hours expiry
        logger.debug(f"Saved progress for task {task_id}")

    def load_task_progress(self, agent_id: int, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Load task execution progress from Redis.

        Args:
            agent_id: Agent ID
            task_id: Task ID

        Returns:
            Progress dictionary or None
        """
        key = f"agent:{agent_id}:task:{task_id}:progress"
        progress_json = self.redis_client.get(key)

        if progress_json:
            return json.loads(progress_json)
        return None

    def save_to_database(self, agent_id: int, task_id: int, result: Dict[str, Any]):
        """
        Save task result to PostgreSQL.

        Args:
            agent_id: Agent ID
            task_id: Task ID
            result: Result dictionary
        """
        with get_db_context() as db:
            # Update agent statistics
            agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
            if agent:
                if result.get("success"):
                    agent.completed_tasks += 1
                    agent.total_earnings += result.get("reward", 0)
                else:
                    agent.failed_tasks += 1

                agent.current_tasks = max(0, agent.current_tasks - 1)
                db.commit()
                logger.info(f"Updated agent {agent_id} statistics")

            # Update task status
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.result = result.get("output")
                task.completed_at = datetime.utcnow()
                db.commit()
                logger.info(f"Updated task {task_id} result")

    def restore_agent_state(self, agent_id: int) -> Dict[str, Any]:
        """
        Restore agent state from both Redis and PostgreSQL.

        Args:
            agent_id: Agent ID

        Returns:
            Complete agent state
        """
        # Load short-term state from Redis
        redis_state = self.load_agent_state(agent_id)

        # Load long-term state from PostgreSQL
        with get_db_context() as db:
            agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()

            if not agent:
                raise ValueError(f"Agent {agent_id} not found")

            db_state = {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "reputation": agent.reputation,
                "completed_tasks": agent.completed_tasks,
                "failed_tasks": agent.failed_tasks,
                "total_earnings": agent.total_earnings,
                "current_tasks": agent.current_tasks
            }

        # Merge states
        state = {**db_state, **(redis_state or {})}

        logger.info(f"Restored state for agent {agent_id}")
        return state

    def clear_agent_state(self, agent_id: int):
        """
        Clear agent state from Redis.

        Args:
            agent_id: Agent ID
        """
        key = f"agent:{agent_id}:state"
        self.redis_client.delete(key)
        logger.debug(f"Cleared state for agent {agent_id}")

    def sync_to_database(self, agent_id: int):
        """
        Sync Redis state to PostgreSQL.

        Args:
            agent_id: Agent ID
        """
        state = self.load_agent_state(agent_id)

        if not state:
            return

        with get_db_context() as db:
            agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()

            if agent:
                # Update agent from state
                if "current_tasks" in state:
                    agent.current_tasks = state["current_tasks"]

                db.commit()
                logger.info(f"Synced state to database for agent {agent_id}")

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """
        Calculate checksum for state data.

        Args:
            data: State data

        Returns:
            SHA256 checksum
        """
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _add_to_history(self, agent_id: int, state_with_meta: Dict[str, Any]):
        """
        Add state to history list.

        Args:
            agent_id: Agent ID
            state_with_meta: State with metadata
        """
        try:
            history_key = f"agent:{agent_id}:state:history"
            # Store only timestamp and checksum in history
            history_entry = {
                "timestamp": state_with_meta["timestamp"],
                "checksum": state_with_meta["checksum"]
            }
            self.redis_client.lpush(history_key, json.dumps(history_entry))
            # Keep only last 10 entries
            self.redis_client.ltrim(history_key, 0, 9)
            self.redis_client.expire(history_key, 86400)  # 24 hours
        except Exception as e:
            logger.warning(f"Failed to add to history for agent {agent_id}: {e}")

    def _recover_from_backup(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """
        Recover state from most recent backup.

        Args:
            agent_id: Agent ID

        Returns:
            Recovered state or None
        """
        try:
            # Find most recent backup
            pattern = f"agent:{agent_id}:state:backup:*"
            backup_keys = self.redis_client.keys(pattern)

            if not backup_keys:
                logger.warning(f"No backups found for agent {agent_id}")
                return None

            # Sort by timestamp (in key name)
            backup_keys.sort(reverse=True)
            latest_backup = backup_keys[0]

            backup_json = self.redis_client.get(latest_backup)
            if backup_json:
                backup_state = json.loads(backup_json)
                logger.info(f"Recovered state from backup for agent {agent_id}")
                return backup_state.get("data", {})

        except Exception as e:
            logger.error(f"Failed to recover from backup for agent {agent_id}: {e}")

        return None

    def save_learning_progress(self, agent_id: int, learning_data: Dict[str, Any]):
        """
        Save agent learning progress to database.

        Args:
            agent_id: Agent ID
            learning_data: Learning progress data (model weights, metrics, etc.)
        """
        try:
            with get_db_context() as db:
                agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()

                if not agent:
                    raise ValueError(f"Agent {agent_id} not found")

                # Store learning data as JSON in agent's metadata
                # Note: In production, consider using a separate table for large learning data
                if not hasattr(agent, 'learning_progress'):
                    # If column doesn't exist, store in Redis instead
                    key = f"agent:{agent_id}:learning"
                    self.redis_client.set(
                        key,
                        json.dumps({
                            "timestamp": datetime.utcnow().isoformat(),
                            "data": learning_data
                        }),
                        ex=604800  # 7 days
                    )
                    logger.info(f"Saved learning progress to Redis for agent {agent_id}")
                else:
                    agent.learning_progress = json.dumps(learning_data)
                    db.commit()
                    logger.info(f"Saved learning progress to database for agent {agent_id}")

        except Exception as e:
            logger.error(f"Failed to save learning progress for agent {agent_id}: {e}")
            raise

    def load_learning_progress(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """
        Load agent learning progress.

        Args:
            agent_id: Agent ID

        Returns:
            Learning progress data or None
        """
        try:
            # Try Redis first
            key = f"agent:{agent_id}:learning"
            learning_json = self.redis_client.get(key)

            if learning_json:
                learning_data = json.loads(learning_json)
                return learning_data.get("data")

            # Try database
            with get_db_context() as db:
                agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()

                if agent and hasattr(agent, 'learning_progress') and agent.learning_progress:
                    return json.loads(agent.learning_progress)

            return None

        except Exception as e:
            logger.error(f"Failed to load learning progress for agent {agent_id}: {e}")
            return None

    def get_state_history(self, agent_id: int) -> List[Dict[str, Any]]:
        """
        Get state change history for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of history entries
        """
        try:
            history_key = f"agent:{agent_id}:state:history"
            history_entries = self.redis_client.lrange(history_key, 0, -1)

            return [json.loads(entry) for entry in history_entries]

        except Exception as e:
            logger.error(f"Failed to get state history for agent {agent_id}: {e}")
            return []

    def cleanup_old_backups(self, agent_id: int, keep_hours: int = 24):
        """
        Clean up old backup states.

        Args:
            agent_id: Agent ID
            keep_hours: Number of hours to keep backups
        """
        try:
            pattern = f"agent:{agent_id}:state:backup:*"
            backup_keys = self.redis_client.keys(pattern)

            cutoff_time = datetime.utcnow().timestamp() - (keep_hours * 3600)
            deleted_count = 0

            for key in backup_keys:
                # Extract timestamp from key
                timestamp_str = key.split(":")[-1]
                try:
                    timestamp = float(timestamp_str)
                    if timestamp < cutoff_time:
                        self.redis_client.delete(key)
                        deleted_count += 1
                except ValueError:
                    continue

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old backups for agent {agent_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup backups for agent {agent_id}: {e}")
