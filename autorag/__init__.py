"""AutoRAG Router: task-adaptive retrieval orchestration."""
__version__ = "0.1.0"
from .engine import AutoRAGEngine
from .router import route

__all__ = ["AutoRAGEngine", "route"]
