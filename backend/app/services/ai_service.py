"""
AI Service.

This module now imports from the modular ai/ package.
Maintained for backward compatibility with existing imports.

For new code, prefer importing from app.services.ai directly:
    from app.services.ai import AIService, ai_service
"""

# Re-export from the new modular package
from app.services.ai import AIService, ai_service
from app.services.ai.base import get_temporal_context

__all__ = ["AIService", "ai_service", "get_temporal_context"]
