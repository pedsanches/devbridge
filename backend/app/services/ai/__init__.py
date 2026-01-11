"""
AI Services Package.

Modular AI services for text generation, analysis, and translation.

Exports a unified AIService facade that maintains backward compatibility
while delegating to specialized modules internally.
"""

from app.services.ai.activity_analyzer import ActivityAnalyzer
from app.services.ai.base import BaseAIService, get_temporal_context
from app.services.ai.business_translator import BusinessTranslator
from app.services.ai.conversation import ConversationAI
from app.services.ai.developer_analyzer import DeveloperAnalyzer
from app.services.ai.facade import AIService, ai_service

__all__ = [
    # Main facade
    "AIService",
    "ai_service",
    # Individual modules
    "BaseAIService",
    "ConversationAI",
    "ActivityAnalyzer",
    "BusinessTranslator",
    "DeveloperAnalyzer",
    # Utilities
    "get_temporal_context",
]
