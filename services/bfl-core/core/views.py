"""API views for BFL Core v1."""
from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import HealthCheckSerializer, StubResponseSerializer


class HealthCheckView(APIView):
    """Simple unauthenticated health endpoint."""

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]

    def get(self, request):
        data = {"status": "ok", "version": "v1"}
        serializer = HealthCheckSerializer(data)
        return Response(serializer.data)


class _StubAPIView(APIView):
    """Base class for not-yet-implemented endpoints."""

    endpoint_description: str = ""

    def _stub_response(self) -> Response:
        payload = {
            "detail": "Endpoint implementation is pending",
            "endpoint": self.endpoint_description,
        }
        serializer = StubResponseSerializer(payload)
        return Response(serializer.data, status=status.HTTP_501_NOT_IMPLEMENTED)


class CaseImportView(_StubAPIView):
    endpoint_description = "POST /api/v1/cases/import-from-lead"

    def post(self, request):
        return self._stub_response()


class CaseStageUpdateView(_StubAPIView):
    endpoint_description = "POST /api/v1/cases/{id}/set-stage"

    def post(self, request, case_id: int):  # noqa: ARG002 - placeholder for future logic
        return self._stub_response()


class PaymentRecordView(_StubAPIView):
    endpoint_description = "POST /api/v1/payments/record"

    def post(self, request):
        return self._stub_response()


class TaskCreateView(_StubAPIView):
    endpoint_description = "POST /api/v1/tasks"

    def post(self, request):
        return self._stub_response()


class EventCreateView(_StubAPIView):
    endpoint_description = "POST /api/v1/events"

    def post(self, request):
        return self._stub_response()


class CaseSummaryView(_StubAPIView):
    endpoint_description = "GET /api/v1/cases/{id}/summary"

    def get(self, request, case_id: int):  # noqa: ARG002 - placeholder for future logic
        return self._stub_response()
