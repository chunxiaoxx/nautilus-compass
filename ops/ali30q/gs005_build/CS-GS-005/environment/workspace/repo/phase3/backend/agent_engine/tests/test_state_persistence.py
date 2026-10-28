"""
Tests for enhanced state persistence.
"""
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from core.state_persistence import StatePersistence, STATE_VERSION


class TestStatePersistence:
    """Test suite for StatePersistence class."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis_mock = Mock()
        redis_mock.ping.return_value = True
        redis_mock.get.return_value = None
        redis_mock.set.return_value = True
        redis_mock.delete.return_value = True
        redis_mock.lpush.return_value = True
        redis_mock.ltrim.return_value = True
        redis_mock.expire.return_value = True
        redis_mock.lrange.return_value = []
        redis_mock.keys.return_value = []
        return redis_mock

    @pytest.fixture
    def persistence(self, mock_redis):
        """Create StatePersistence instance with mocked Redis."""
        with patch('redis.from_url', return_value=mock_redis):
            return StatePersistence()

    def test_initialization_success(self, mock_redis):
        """Test successful initialization."""
        with patch('redis.from_url', return_value=mock_redis):
            persistence = StatePersistence()
            assert persistence.redis_client == mock_redis
            mock_redis.ping.assert_called_once()

    def test_initialization_failure(self):
        """Test initialization failure handling."""
        with patch('redis.from_url', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception):
                StatePersistence()

    def test_save_agent_state_with_metadata(self, persistence, mock_redis):
        """Test saving agent state with version and checksum."""
        agent_id = 1
        state = {"current_task": 5, "progress": 0.5}

        persistence.save_agent_state(agent_id, state)

        # Verify Redis set was called
        assert mock_redis.set.called
        call_args = mock_redis.set.call_args[0]

        # Verify key format
        assert call_args[0] == f"agent:{agent_id}:state"

        # Verify state structure
        saved_state = json.loads(call_args[1])
        assert saved_state["version"] == STATE_VERSION
        assert saved_state["agent_id"] == agent_id
        assert saved_state["data"] == state
        assert "checksum" in saved_state
        assert "timestamp" in saved_state

    def test_save_agent_state_with_backup(self, persistence, mock_redis):
        """Test backup creation when saving state."""
        agent_id = 1
        existing_state = json.dumps({
            "version": STATE_VERSION,
            "data": {"old": "state"}
        })
        mock_redis.get.return_value = existing_state

        persistence.save_agent_state(agent_id, {"new": "state"}, create_backup=True)

        # Verify backup was created
        backup_calls = [call for call in mock_redis.set.call_args_list
                       if "backup" in str(call)]
        assert len(backup_calls) > 0

    def test_load_agent_state_success(self, persistence, mock_redis):
        """Test loading agent state successfully."""
        agent_id = 1
        state_data = {"current_task": 5}
        state_with_meta = {
            "version": STATE_VERSION,
            "agent_id": agent_id,
            "data": state_data,
            "checksum": persistence._calculate_checksum(state_data),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        mock_redis.get.return_value = json.dumps(state_with_meta)

        loaded_state = persistence.load_agent_state(agent_id)

        assert loaded_state == state_data

    def test_load_agent_state_checksum_verification(self, persistence, mock_redis):
        """Test checksum verification on load."""
        agent_id = 1
        state_data = {"current_task": 5}
        state_with_meta = {
            "version": STATE_VERSION,
            "agent_id": agent_id,
            "data": state_data,
            "checksum": "invalid_checksum",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        mock_redis.get.return_value = json.dumps(state_with_meta)

        # Should attempt recovery when checksum fails
        with patch.object(persistence, '_recover_from_backup', return_value=None):
            loaded_state = persistence.load_agent_state(agent_id, verify_checksum=True)
            persistence._recover_from_backup.assert_called_once()

    def test_load_agent_state_not_found(self, persistence, mock_redis):
        """Test loading non-existent state."""
        mock_redis.get.return_value = None

        loaded_state = persistence.load_agent_state(1)

        assert loaded_state is None

    def test_calculate_checksum_consistency(self, persistence):
        """Test checksum calculation is consistent."""
        data = {"key": "value", "number": 42}

        checksum1 = persistence._calculate_checksum(data)
        checksum2 = persistence._calculate_checksum(data)

        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA256 hex length

    def test_calculate_checksum_different_data(self, persistence):
        """Test different data produces different checksums."""
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}

        checksum1 = persistence._calculate_checksum(data1)
        checksum2 = persistence._calculate_checksum(data2)

        assert checksum1 != checksum2

    def test_save_task_progress(self, persistence, mock_redis):
        """Test saving task progress."""
        agent_id = 1
        task_id = 5
        progress = {"step": 3, "total": 10}

        persistence.save_task_progress(agent_id, task_id, progress)

        mock_redis.set.assert_called()
        call_args = mock_redis.set.call_args[0]
        assert f"agent:{agent_id}:task:{task_id}:progress" in call_args[0]

    def test_load_task_progress(self, persistence, mock_redis):
        """Test loading task progress."""
        agent_id = 1
        task_id = 5
        progress = {"step": 3, "total": 10}
        mock_redis.get.return_value = json.dumps(progress)

        loaded_progress = persistence.load_task_progress(agent_id, task_id)

        assert loaded_progress == progress

    def test_clear_agent_state(self, persistence, mock_redis):
        """Test clearing agent state."""
        agent_id = 1

        persistence.clear_agent_state(agent_id)

        mock_redis.delete.assert_called_with(f"agent:{agent_id}:state")

    def test_get_state_history(self, persistence, mock_redis):
        """Test retrieving state history."""
        agent_id = 1
        history_entries = [
            json.dumps({"timestamp": "2026-02-21T00:00:00", "checksum": "abc123"}),
            json.dumps({"timestamp": "2026-02-21T01:00:00", "checksum": "def456"})
        ]
        mock_redis.lrange.return_value = history_entries

        history = persistence.get_state_history(agent_id)

        assert len(history) == 2
        assert history[0]["checksum"] == "abc123"
        assert history[1]["checksum"] == "def456"

    def test_cleanup_old_backups(self, persistence, mock_redis):
        """Test cleaning up old backups."""
        agent_id = 1
        old_timestamp = (datetime.now(timezone.utc).timestamp() - 86400 * 2)  # 2 days ago
        recent_timestamp = datetime.now(timezone.utc).timestamp()

        backup_keys = [
            f"agent:{agent_id}:state:backup:{old_timestamp}",
            f"agent:{agent_id}:state:backup:{recent_timestamp}"
        ]
        mock_redis.keys.return_value = backup_keys

        persistence.cleanup_old_backups(agent_id, keep_hours=24)

        # Should delete old backup but keep recent one
        assert mock_redis.delete.called

    def test_save_learning_progress(self, persistence, mock_redis):
        """Test saving learning progress."""
        agent_id = 1
        learning_data = {
            "model_version": "1.0",
            "accuracy": 0.95,
            "training_steps": 1000
        }

        persistence.save_learning_progress(agent_id, learning_data)

        # Should save to Redis
        assert mock_redis.set.called
        call_args = mock_redis.set.call_args[0]
        assert f"agent:{agent_id}:learning" in call_args[0]

    def test_load_learning_progress(self, persistence, mock_redis):
        """Test loading learning progress."""
        agent_id = 1
        learning_data = {"accuracy": 0.95}
        mock_redis.get.return_value = json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": learning_data
        })

        loaded_data = persistence.load_learning_progress(agent_id)

        assert loaded_data == learning_data

    def test_recover_from_backup_success(self, persistence, mock_redis):
        """Test successful recovery from backup."""
        agent_id = 1
        backup_data = {
            "version": STATE_VERSION,
            "data": {"recovered": "state"}
        }

        mock_redis.keys.return_value = [f"agent:{agent_id}:state:backup:123456"]
        mock_redis.get.return_value = json.dumps(backup_data)

        recovered = persistence._recover_from_backup(agent_id)

        assert recovered == {"recovered": "state"}

    def test_recover_from_backup_no_backups(self, persistence, mock_redis):
        """Test recovery when no backups exist."""
        mock_redis.keys.return_value = []

        recovered = persistence._recover_from_backup(1)

        assert recovered is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
