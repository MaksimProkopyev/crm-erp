"""Serializers for the BFL Core API v1."""
from __future__ import annotations

from typing import Any, Dict

from rest_framework import serializers

from .models import Case, CaseStage, Client, Event, Payment, PaymentPlan, Task


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id",
            "first_name",
            "last_name",
            "patronymic",
            "phone",
            "email",
            "region",
            "city",
            "comment",
        ]
        read_only_fields = ["id"]


class CaseStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStage
        fields = ["id", "code", "name", "order", "is_final"]
        read_only_fields = ["id"]


class CaseSerializer(serializers.ModelSerializer):
    stage = CaseStageSerializer(read_only=True)

    class Meta:
        model = Case
        fields = [
            "id",
            "client",
            "number",
            "stage",
            "opened_at",
            "closed_at",
            "comment",
            "idempotency_key",
        ]
        read_only_fields = ["id"]


class PaymentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentPlan
        fields = [
            "id",
            "case",
            "total_amount",
            "currency",
            "start_date",
            "end_date",
            "monthly_payment",
            "meta",
        ]
        read_only_fields = ["id"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "case",
            "amount",
            "date",
            "source",
            "status",
            "meta",
        ]
        read_only_fields = ["id"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "case",
            "type",
            "title",
            "description",
            "due_date",
            "status",
            "assignee",
            "completed_at",
            "meta",
        ]
        read_only_fields = ["id"]


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["id", "case", "type", "source", "payload", "occurred_at"]
        read_only_fields = ["id"]


class ImportClientSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    patronymic = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    region = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    comment = serializers.CharField(required=False, allow_blank=True)


class ImportCaseSerializer(serializers.Serializer):
    contract_number = serializers.CharField(required=False, allow_blank=True)
    opened_at = serializers.DateField(required=False)
    stage_code = serializers.CharField(required=False)
    comment = serializers.CharField(required=False, allow_blank=True)


class ImportPaymentPlanSerializer(serializers.Serializer):
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(required=False, default="RUB")
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    monthly_payment = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    meta = serializers.JSONField(required=False)


class ImportCaseFromLeadSerializer(serializers.Serializer):
    lead_source = serializers.CharField()
    lead_channel = serializers.CharField(required=False, allow_blank=True)
    lead_external_id = serializers.CharField()
    utm_source = serializers.CharField(required=False, allow_blank=True)
    utm_medium = serializers.CharField(required=False, allow_blank=True)
    utm_campaign = serializers.CharField(required=False, allow_blank=True)
    utm_content = serializers.CharField(required=False, allow_blank=True)
    utm_term = serializers.CharField(required=False, allow_blank=True)

    client = ImportClientSerializer()
    case = ImportCaseSerializer(required=False)
    payment_plan = ImportPaymentPlanSerializer(required=False)


class CaseSetStageSerializer(serializers.Serializer):
    stage = serializers.CharField()
    reason = serializers.CharField(required=False, allow_blank=True)
    meta = serializers.JSONField(required=False)


class PaymentRecordSerializer(serializers.Serializer):
    case_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    date = serializers.DateField()
    source = serializers.CharField()
    status = serializers.ChoiceField(
        choices=Payment.PaymentStatus.choices,
        default=Payment.PaymentStatus.PAID,
        required=False,
    )
    meta = serializers.JSONField(required=False)


class TaskCreateSerializer(serializers.Serializer):
    case_id = serializers.IntegerField()
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    due_date = serializers.DateField(required=False)
    status = serializers.ChoiceField(
        choices=Task.TaskStatus.choices,
        default=Task.TaskStatus.PENDING,
        required=False,
    )
    assignee = serializers.CharField(required=False, allow_blank=True)
    completed_at = serializers.DateTimeField(required=False)
    meta = serializers.JSONField(required=False)


class EventCreateSerializer(serializers.Serializer):
    case_id = serializers.IntegerField()
    type = serializers.CharField()
    source = serializers.CharField(required=False, allow_blank=True)
    payload = serializers.JSONField(required=False)
    occurred_at = serializers.DateTimeField(required=False)


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()
    version = serializers.CharField()


class ImportResponseSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    case_id = serializers.IntegerField()
    lead_id = serializers.IntegerField(allow_null=True)
    payment_plan_id = serializers.IntegerField(allow_null=True)


def serialize_meta(data: Dict[str, Any] | None) -> Dict[str, Any]:
    """Utility for ensuring meta/payload defaults."""

    return data or {}
