"""nautilus_compass.sdk · client-side helpers for cross-agent memory.

Re-exports the public surface so users can do::

    from nautilus_compass.sdk import attach_memory

instead of digging into submodules.
"""

from .attach_memory import attach_memory

__all__ = ["attach_memory"]
