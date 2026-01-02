"""
Application Constants.

Central place for all constant values used across the application.
"""

# ============================================================
# Translation Categories
# ============================================================
TRANSLATION_CATEGORIES = {
    "feature": "Nova Funcionalidade",
    "bugfix": "Correção de Bug",
    "refactor": "Refatoração",
    "docs": "Documentação",
    "test": "Testes",
    "chore": "Manutenção",
    "perf": "Performance",
    "security": "Segurança",
}

# ============================================================
# Business Impact Levels
# ============================================================
IMPACT_LEVELS = {
    "high": {"label": "Alto Impacto", "emoji": "🔴", "weight": 3},
    "medium": {"label": "Médio Impacto", "emoji": "🟡", "weight": 2},
    "low": {"label": "Baixo Impacto", "emoji": "🟢", "weight": 1},
}

# ============================================================
# API Limits
# ============================================================
MAX_COMMITS_PER_REQUEST = 100
MAX_TRANSLATIONS_PER_DAY = 1000
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ============================================================
# Cache TTL (seconds)
# ============================================================
CACHE_TTL_SHORT = 60 * 5  # 5 minutes
CACHE_TTL_MEDIUM = 60 * 30  # 30 minutes
CACHE_TTL_LONG = 60 * 60 * 24  # 24 hours

# ============================================================
# LLM Limits
# ============================================================
MAX_TOKENS_PER_REQUEST = 4096
MAX_CONTEXT_TOKENS = 100000
EMBEDDING_DIMENSION = 1536
