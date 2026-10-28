"""
Custom logging formatter with sensitive data filtering.
"""
import logging
import re
from utils.security_validators import sanitize_log_data


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter to remove sensitive information from log messages.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record to sanitize sensitive data.

        Args:
            record: Log record to filter

        Returns:
            True (always allow the record, but sanitize it first)
        """
        # Sanitize the message
        if isinstance(record.msg, str):
            record.msg = sanitize_log_data(record.msg)

        # Sanitize arguments
        if record.args:
            if isinstance(record.args, dict):
                record.args = sanitize_log_data(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(sanitize_log_data(list(record.args)))

        return True


def setup_sensitive_data_filtering():
    """
    Setup sensitive data filtering for all loggers.
    """
    # Get root logger
    root_logger = logging.getLogger()

    # Add filter to root logger
    sensitive_filter = SensitiveDataFilter()
    root_logger.addFilter(sensitive_filter)

    # Add filter to all existing handlers
    for handler in root_logger.handlers:
        handler.addFilter(sensitive_filter)

    logging.info("Sensitive data filtering enabled for all loggers")
