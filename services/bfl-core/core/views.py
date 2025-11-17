from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Case, CaseStage, Client, Event, Lead, Payment, PaymentPlan, Task
from .serializers import (
    CaseImportSerializer,
    CaseStageSerializer,
    CaseSummarySerializer,
    ClientSerializer,
    EventCreateSerializer,
    PaymentRecordSerializer,
    TaskCreateSerializer,
    serialize_case,
    serialize_stage,
)


class HealthCheckView(APIView):
    authentication_classes: list[Any] = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok", "version": "v1"})


class CaseImportView(APIView):
    def post(self, request):
        serializer = CaseImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        idempotency_key = request.headers.get("Idempotency-Key")
        if idempotency_key:
            existing_case = Case.objects.filter(idempotency_key=idempotency_key).first()
            if existing_case:
                return Response(self._build_response(existing_case))

        with transaction.atomic():
            validated = serializer.validated_data
            client = self._upsert_client(validated["client"])
            lead = self._upsert_lead(validated, client)
            case = self._create_case(validated.get("case", {}), client, idempotency_key)
            lead.case = case
            lead.client = client
            lead.save(update_fields=["case", "client"])
            payment_plan = self._upsert_payment_plan(case, validated.get("payment_plan"))

        return Response(self._build_response(case, payment_plan))

    def _upsert_client(self, data: Dict[str, Any]) -> Client:
        defaults = {k: data.get(k, "") for k in ["first_name", "last_name", "patronymic", "email", "region", "city", "comment"]}
        client, _ = Client.objects.update_or_create(phone=data["phone"], defaults=defaults)
        return client

    def _upsert_lead(self, data: Dict[str, Any], client: Client) -> Lead:
        defaults = {
            "channel": data.get("lead_channel", ""),
            "client": client,
            "utm_source": data.get("utm_source", ""),
            "utm_medium": data.get("utm_medium", ""),
            "utm_campaign": data.get("utm_campaign", ""),
            "utm_content": data.get("utm_content", ""),
            "utm_term": data.get("utm_term", ""),
        }
        lead, _ = Lead.objects.update_or_create(
            source=data["lead_source"],
            external_id=data["lead_external_id"],
            defaults=defaults,
        )
        return lead

    def _create_case(self, data: Dict[str, Any], client: Client, idempotency_key: str | None) -> Case:
        stage = None
        stage_code = data.get("stage_code")
        if stage_code:
            stage, _ = CaseStage.objects.get_or_create(
                code=stage_code,
                defaults={"name": stage_code, "order": 0},
            )
        case = Case.objects.create(
            client=client,
            number=data.get("contract_number", ""),
            opened_at=data.get("opened_at"),
            comment=data.get("comment", ""),
            stage=stage,
            idempotency_key=idempotency_key,
        )
        return case

    def _upsert_payment_plan(self, case: Case, data: Dict[str, Any] | None) -> PaymentPlan | None:
        if not data:
            return None
        defaults = {
            "total_amount": data["total_amount"],
            "currency": data.get("currency", "RUB"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date"),
            "monthly_payment": data.get("monthly_payment"),
            "meta": data.get("meta", {}),
        }
        payment_plan, _ = PaymentPlan.objects.update_or_create(case=case, defaults=defaults)
        return payment_plan

    def _build_response(self, case: Case, payment_plan: PaymentPlan | None = None) -> Dict[str, Any]:
        lead = getattr(case, "lead", None)
        plan = payment_plan or getattr(case, "payment_plan", None)
        return {
            "client_id": case.client_id,
            "case_id": case.id,
            "lead_id": lead.id if lead else None,
            "payment_plan_id": plan.id if plan else None,
        }


class CaseStageUpdateView(APIView):
    def post(self, request, case_id: int):
        stage_code = request.data.get("stage")
        if not stage_code:
            return Response({"detail": "stage is required"}, status=status.HTTP_400_BAD_REQUEST)
        case = get_object_or_404(Case, id=case_id)
        previous_stage = case.stage
        stage, _ = CaseStage.objects.get_or_create(code=stage_code, defaults={"name": stage_code})
        case.stage = stage
        case.save(update_fields=["stage"])
        payload = {
            "from": serialize_stage(previous_stage),
            "to": serialize_stage(stage),
            "reason": request.data.get("reason"),
            "meta": request.data.get("meta", {}),
        }
        Event.objects.create(case=case, type="stage_change", source="bfl_core", payload=payload)
        return Response({"case_id": case.id, "stage": CaseStageSerializer(stage).data})


class PaymentRecordView(APIView):
    def post(self, request):
        serializer = PaymentRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = get_object_or_404(Case, id=serializer.validated_data["case_id"])
        payment = Payment.objects.create(
            case=case,
            amount=serializer.validated_data["amount"],
            date=serializer.validated_data["date"],
            source=serializer.validated_data["source"],
            status=serializer.validated_data.get("status", Payment.PaymentStatus.PAID),
            meta=serializer.validated_data.get("meta", {}),
        )
        Event.objects.create(
            case=case,
            type="payment",
            source="bfl_core",
            payload={"payment_id": payment.id, "status": payment.status, "amount": str(payment.amount)},
        )
        return Response({"payment_id": payment.id}, status=status.HTTP_201_CREATED)


class TaskCreateView(APIView):
    def post(self, request):
        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = get_object_or_404(Case, id=serializer.validated_data["case_id"])
        task = Task.objects.create(
            case=case,
            type=serializer.validated_data["type"],
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get("description", ""),
            due_date=serializer.validated_data.get("due_date"),
            status=serializer.validated_data.get("status", Task.TaskStatus.PENDING),
            assignee=serializer.validated_data.get("assignee", ""),
            meta=serializer.validated_data.get("meta", {}),
        )
        return Response({"task_id": task.id}, status=status.HTTP_201_CREATED)


class EventCreateView(APIView):
    def post(self, request):
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = get_object_or_404(Case, id=serializer.validated_data["case_id"])
        event = Event.objects.create(
            case=case,
            type=serializer.validated_data["type"],
            source=serializer.validated_data.get("source", ""),
            payload=serializer.validated_data.get("payload", {}),
        )
        return Response({"event_id": event.id}, status=status.HTTP_201_CREATED)


class CaseSummaryView(APIView):
    def get(self, request, case_id: int):
        case = get_object_or_404(Case.objects.select_related("client", "stage"), id=case_id)
        payments = case.payments.all()
        total_paid = sum((p.amount for p in payments if p.status == Payment.PaymentStatus.PAID), Decimal("0"))
        total_planned = sum((p.amount for p in payments if p.status == Payment.PaymentStatus.PLANNED), Decimal("0"))
        currency = case.payment_plan.currency if hasattr(case, "payment_plan") and case.payment_plan else "RUB"
        data = {
            "case": serialize_case(case),
            "client": ClientSerializer(case.client).data,
            "payments": {
                "total_paid": str(total_paid),
                "total_planned": str(total_planned),
                "currency": currency,
            },
            "stage": serialize_stage(case.stage),
        }
        summary_serializer = CaseSummarySerializer(data)
        return Response(summary_serializer.data)
