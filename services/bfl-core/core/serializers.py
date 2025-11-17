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


class ClientInputSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    patronymic = serializers.CharField(required=False, allow_blank=True, default="")
    phone = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    region = serializers.CharField(required=False, allow_blank=True, default="")
    city = serializers.CharField(required=False, allow_blank=True, default="")
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class CaseInputSerializer(serializers.Serializer):
    contract_number = serializers.CharField(required=False, allow_blank=True, default="")
    opened_at = serializers.DateField(required=False, allow_null=True)
    stage_code = serializers.CharField(required=False, allow_blank=True, default="")
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class PaymentPlanInputSerializer(serializers.Serializer):
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(required=False, default="RUB")
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    monthly_payment = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    meta = serializers.DictField(child=serializers.JSONField(), required=False, default=dict)


class CaseImportSerializer(serializers.Serializer):
    lead_source = serializers.CharField()
    lead_channel = serializers.CharField(required=False, allow_blank=True, default="")
    lead_external_id = serializers.CharField()
    utm_source = serializers.CharField(required=False, allow_blank=True, default="")
    utm_medium = serializers.CharField(required=False, allow_blank=True, default="")
    utm_campaign = serializers.CharField(required=False, allow_blank=True, default="")
    utm_content = serializers.CharField(required=False, allow_blank=True, default="")
    utm_term = serializers.CharField(required=False, allow_blank=True, default="")
    client = ClientInputSerializer()
    case = CaseInputSerializer(required=False)
    payment_plan = PaymentPlanInputSerializer(required=False)


class CaseStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStage
        fields = ["code", "name", "order", "is_final"]


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


class PaymentRecordSerializer(serializers.Serializer):
    case_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    date = serializers.DateField()
    source = serializers.CharField()
    status = serializers.ChoiceField(
        choices=Payment.PaymentStatus.choices, required=False, default=Payment.PaymentStatus.PAID
    )
    meta = serializers.DictField(required=False, default=dict)


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


class TaskCreateSerializer(serializers.Serializer):
    case_id = serializers.IntegerField()
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True, default="")
    due_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Task.TaskStatus.choices, required=False, default=Task.TaskStatus.PENDING)
    assignee = serializers.CharField(required=False, allow_blank=True, default="")
    meta = serializers.DictField(required=False, default=dict)


class EventCreateSerializer(serializers.Serializer):
    case_id = serializers.IntegerField()
    type = serializers.CharField()
    source = serializers.CharField(required=False, allow_blank=True, default="")
    payload = serializers.DictField(required=False, default=dict)


class CaseSummarySerializer(serializers.Serializer):
    case = serializers.DictField()
    client = serializers.DictField()
    payments = serializers.DictField()
    stage = serializers.DictField(allow_null=True)


def serialize_case(case: Case) -> Dict[str, Any]:
    return {
        "id": case.id,
        "number": case.number,
        "opened_at": case.opened_at,
        "closed_at": case.closed_at,
        "comment": case.comment,
    }


def serialize_stage(stage: CaseStage | None) -> Dict[str, Any] | None:
    if not stage:
        return None
    return {
        "code": stage.code,
        "name": stage.name,
        "order": stage.order,
        "is_final": stage.is_final,
    }
