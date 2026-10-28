"""
Database connection pool monitoring utilities.
"""
import logging
from sqlalchemy import event
from sqlalchemy.pool import Pool

logger = logging.getLogger(__name__)


class PoolMonitor:
    """Monitor database connection pool statistics."""

    def __init__(self):
        self.checkouts = 0
        self.checkins = 0
        self.connects = 0
        self.disconnects = 0
        self.invalidations = 0

    def setup_listeners(self, engine):
        """Setup event listeners for pool monitoring."""

        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            self.checkouts += 1

        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            self.checkins += 1

        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            self.connects += 1
            logger.debug(f"New database connection created (total: {self.connects})")

        @event.listens_for(engine, "close")
        def receive_close(dbapi_conn, connection_record):
            self.disconnects += 1
            logger.debug(f"Database connection closed (total: {self.disconnects})")

        @event.listens_for(Pool, "invalidate")
        def receive_invalidate(dbapi_conn, connection_record, exception):
            self.invalidations += 1
            logger.warning(f"Connection invalidated: {exception}")

    def get_stats(self, engine):
        """Get current pool statistics."""
        pool = engine.pool

        return {
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_checkouts": self.checkouts,
            "total_checkins": self.checkins,
            "total_connects": self.connects,
            "total_disconnects": self.disconnects,
            "total_invalidations": self.invalidations,
            "active_connections": self.checkouts - self.checkins
        }

    def reset_stats(self):
        """Reset all statistics."""
        self.checkouts = 0
        self.checkins = 0
        self.connects = 0
        self.disconnects = 0
        self.invalidations = 0


# Global pool monitor instance
_pool_monitor = None


def get_pool_monitor() -> PoolMonitor:
    """Get global pool monitor instance."""
    return _pool_monitor


def init_pool_monitor(engine):
    """Initialize pool monitoring."""
    global _pool_monitor
    _pool_monitor = PoolMonitor()
    _pool_monitor.setup_listeners(engine)
    logger.info("Database pool monitoring initialized")
    return _pool_monitor
