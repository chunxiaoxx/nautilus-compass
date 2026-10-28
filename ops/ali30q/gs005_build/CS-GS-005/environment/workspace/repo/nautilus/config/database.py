"""
Database configuration for Nautilus project.

PostgreSQL connection settings.
"""

# PostgreSQL Configuration
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5433,  # Non-default port
    'database': 'nautilus',
    'user': 'nautilus_user',
    'password': 'nautilus_pass',
    'options': '-c client_encoding=UTF8'
}

# Connection string
POSTGRES_URL = f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"

# Redis Configuration (from Phase 1)
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'decode_responses': True
}

# EverMemOS Configuration (from Phase 1)
EVERMEMOS_CONFIG = {
    'base_url': 'http://localhost:8000',
    'timeout': 30
}
