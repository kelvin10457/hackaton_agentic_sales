"""
conftest.py — Reset completo de dependency_overrides antes de CADA test.

Solución definitiva al problema de contaminación cross-module:
cada test empieza con los overrides que su módulo estableció,
no con los residuos de módulos anteriores.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_main.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-padded-x")
os.environ.setdefault("CHAT_TOKEN_SECRET", "test-chat-secret-32-chars-padded")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("CHAT_TOKEN_EXPIRE_HOURS", "24")

import pytest


def pytest_runtest_setup(item):
    """
    Hook que corre ANTES de cada test.
    Restaura dependency_overrides al estado que el módulo del test estableció.
    Esto evita que overrides de test_upsert_idempotente contaminen test_consentimiento.
    """
    import sys
    if "app.main" not in sys.modules:
        return
    from app.main import app

    # Cada módulo de test guarda sus overrides propios en _MODULE_OVERRIDES
    module = item.module
    if hasattr(module, "_MODULE_OVERRIDES"):
        app.dependency_overrides.clear()
        app.dependency_overrides.update(module._MODULE_OVERRIDES)
