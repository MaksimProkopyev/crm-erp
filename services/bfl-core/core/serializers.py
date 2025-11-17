"""Serializers for the BFL Core API v1."""
from __future__ import annotations

from rest_framework import serializers


class HealthCheckSerializer(serializers.Serializer):
    """Serializer that describes the healthcheck response payload."""

    status = serializers.CharField()
    version = serializers.CharField()


class StubResponseSerializer(serializers.Serializer):
    """Generic serializer for the not-yet-implemented API endpoints."""

    detail = serializers.CharField()
    endpoint = serializers.CharField()
