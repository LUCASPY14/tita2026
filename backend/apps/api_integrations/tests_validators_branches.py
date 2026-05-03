"""
Tests de ramas faltantes en api_integrations/validators.py
Cubre branches no alcanzados por los tests principales.
"""

from datetime import date, datetime

from django.core.exceptions import ValidationError

import pytest

from apps.api_integrations.validators import (
    validar_created_at_webhook,
    validar_payload_webhook,
    validar_url_log,
)


class TestValidarUrlLogBranches:
    """Branch 437->438: string de solo espacios → strip → len < 1 → raises."""

    def test_whitespace_only_raises(self):
        """Solo espacios → strip → vacío → raises."""
        with pytest.raises(ValidationError, match="vacía"):
            validar_url_log("   ")

    def test_tab_only_raises(self):
        with pytest.raises(ValidationError, match="vacía"):
            validar_url_log("\t\n")


class TestValidarPayloadWebhookBranches:
    """Branch 785->786: string de solo espacios → strip → len == 0 → raises."""

    def test_whitespace_only_raises(self):
        """Solo espacios → strip → vacío → raises."""
        with pytest.raises(ValidationError, match="vacío"):
            validar_payload_webhook("   ")

    def test_tab_only_raises(self):
        with pytest.raises(ValidationError, match="vacío"):
            validar_payload_webhook("\t\n  ")


class TestValidarCreatedAtWebhookBranches:
    """Branch 1030->1031: None → raises. Branch 1033->1034: no datetime → raises."""

    def test_none_raises(self):
        """Branch 1030->1031: valor is None → raises."""
        with pytest.raises(ValidationError, match="requerida"):
            validar_created_at_webhook(None)

    def test_string_raises(self):
        """Branch 1033->1034: no es datetime → raises."""
        with pytest.raises(ValidationError, match="objeto datetime"):
            validar_created_at_webhook("2024-01-01")

    def test_date_not_datetime_raises(self):
        """date (no datetime) también cubre el isinstance check."""
        with pytest.raises(ValidationError, match="objeto datetime"):
            validar_created_at_webhook(date(2024, 1, 1))
