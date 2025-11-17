"""API views for BFL Core v1."""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import APIKeyAuthentication
from .models import Case, CaseStage, Client, Event, Lead, Payment, PaymentPlan, Task
from .serializers import (
    CaseSerializer,
    CaseSetStageSerializer,
    CaseStageSerializer,
    ClientSerializer,
    EventCreateSerializer,
    EventSerializer,
    HealthCheckSerializer,
    ImportCaseFromLeadSerializer,
    ImportResponseSerializer,
    PaymentRecordSerializer,
    PaymentSerializer,
    TaskCreateSerializer,
    TaskSerializer,
    serialize_meta,
)


class AuthenticatedAPIView(APIView):
    """Base API view that requires the BFL Core API token."""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]


class HealthCheckView(APIView):
    """Simple unauthenticated health endpoint."""

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]

    def get(self, request):
        data = {"status": "ok", "version": "v1"}
        serializer = HealthCheckSerializer(data)
        return Response(serializer.data)


class ImportCaseFromLeadView(AuthenticatedAPIView):
    """Create or retrieve a case based on lead data."""

    def post(self, request):
        serializer = ImportCaseFromLeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        idempotency_key = request.headers.get("Idempotency-Key") or None
        if idempotency_key:
            existing_case = (
                Case.objects.select_related("client")
                .filter(idempotency_key=idempotency_key)
                .first()
            )
            if existing_case:
                payment_plan = self._maybe_create_payment_plan(
                    existing_case, data.get("payment_plan")
                )
                return Response(
                    ImportResponseSerializer(
                        self._build_import_response(existing_case, payment_plan)
                    ).data
                )

        with transaction.atomic():
            client = self._upsert_client(data["client"])
            lead = self._upsert_lead(client, data)

            if getattr(lead, "case_id", None):
                payment_plan = self._maybe_create_payment_plan(
                    lead.case, data.get("payment_plan")
                )
                return Response(
                    ImportResponseSerializer(
                        self._build_import_response(lead.case, payment_plan)
                    ).data
                )

            case = self._create_case(client, data.get("case"), idempotency_key)
            lead.case = case
            lead.save(update_fields=["case", "updated_at"])

            payment_plan = self._maybe_create_payment_plan(case, data.get("payment_plan"))

        response_payload = self._build_import_response(case, payment_plan)
        return Response(
            ImportResponseSerializer(response_payload).data,
            status=status.HTTP_201_CREATED,
        )

    def _upsert_client(self, client_data: dict) -> Client:
        defaults = {
            "first_name": client_data["first_name"],
            "last_name": client_data["last_name"],
            "patronymic": client_data.get("patronymic", ""),
            "email": client_data.get("email", ""),
            "region": client_data.get("region", ""),
            "city": client_data.get("city", ""),
            "comment": client_data.get("comment", ""),
        }
        client, _ = Client.objects.update_or_create(
            phone=client_data["phone"],
            defaults=defaults,
        )
        return client

    def _upsert_lead(self, client: Client, data: dict) -> Lead:
        defaults = {
            "client": client,
            "channel": data.get("lead_channel", ""),
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

    def _create_case(self, client: Client, case_data: dict | None, idem_key: str | None) -> Case:
        case_data = case_data or {}
        stage = None
        stage_code = case_data.get("stage_code")
        if stage_code:
            stage, _ = CaseStage.objects.get_or_create(
                code=stage_code,
                defaults={"name": stage_code},
            )
        case = Case.objects.create(
            client=client,
            number=case_data.get("contract_number", ""),
            stage=stage,
            opened_at=case_data.get("opened_at"),
            comment=case_data.get("comment", ""),
            idempotency_key=idem_key,
        )
        return case

    def _maybe_create_payment_plan(
        self, case: Case, payment_plan_data: dict | None
    ) -> PaymentPlan | None:
        if not payment_plan_data:
            try:
                return case.payment_plan
            except PaymentPlan.DoesNotExist:
                return None

        defaults = {
            "total_amount": payment_plan_data["total_amount"],
            "currency": payment_plan_data.get("currency", "RUB"),
            "start_date": payment_plan_data.get("start_date"),
            "end_date": payment_plan_data.get("end_date"),
            "monthly_payment": payment_plan_data.get("monthly_payment"),
            "meta": serialize_meta(payment_plan_data.get("meta")),
        }
        payment_plan, created = PaymentPlan.objects.get_or_create(
            case=case,
            defaults=defaults,
        )
        if not created:
            for field, value in defaults.items():
                setattr(payment_plan, field, value)
            payment_plan.save(update_fields=list(defaults.keys()) + ["updated_at"])
        return payment_plan

    def _build_import_response(
        self,
        case: Case,
        payment_plan: PaymentPlan | None = None,
    ) -> dict:
        try:
            lead = case.lead
        except Lead.DoesNotExist:
            lead = None

        if payment_plan is None:
            try:
                payment_plan = case.payment_plan
            except PaymentPlan.DoesNotExist:  # pragma: no cover - simple fallback
                payment_plan = None

        return {
            "client_id": case.client_id,
            "case_id": case.id,
            "lead_id": lead.id if lead else None,
            "payment_plan_id": payment_plan.id if payment_plan else None,
        }


class CaseSetStageView(AuthenticatedAPIView):
    """Update a case stage and record the transition."""

    def post(self, request, pk: int):
        serializer = CaseSetStageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        case = get_object_or_404(Case.objects.select_related("stage"), pk=pk)
        previous_stage = case.stage

        stage, _ = CaseStage.objects.get_or_create(
            code=data["stage"],
            defaults={"name": data["stage"]},
        )
        case.stage = stage
        case.save(update_fields=["stage", "updated_at"])

        payload: dict = {
            "from": previous_stage.code if previous_stage else None,
            "to": stage.code,
        }
        if data.get("reason"):
            payload["reason"] = data["reason"]
        meta_data = serialize_meta(data.get("meta"))
        if meta_data:
            payload["meta"] = meta_data

        Event.objects.create(
            case=case,
            type="stage_change",
            source="bfl_core",
            payload=payload,
        )

        return Response(CaseSerializer(case).data)


class PaymentRecordView(AuthenticatedAPIView):
    """Record a payment and add a timeline event."""

    def post(self, request):
        serializer = PaymentRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        case = get_object_or_404(Case, pk=data["case_id"])
        payment = Payment.objects.create(
            case=case,
            amount=data["amount"],
            date=data["date"],
            source=data["source"],
            status=data.get("status") or Payment.PaymentStatus.PAID,
            meta=serialize_meta(data.get("meta")),
        )

        Event.objects.create(
            case=case,
            type="payment",
            source="bfl_core",
            payload={
                "payment_id": payment.id,
                "amount": str(payment.amount),
                "date": payment.date.isoformat(),
                "status": payment.status,
                "source": payment.source,
                "meta": payment.meta,
            },
        )

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class TaskCreateView(AuthenticatedAPIView):
    """Create a task for a case."""

    def post(self, request):
        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        case = get_object_or_404(Case, pk=data["case_id"])
        task = Task.objects.create(
            case=case,
            type=data["type"],
            title=data["title"],
            description=data.get("description", ""),
            due_date=data.get("due_date"),
            status=data.get("status") or Task.TaskStatus.PENDING,
            assignee=data.get("assignee", ""),
            completed_at=data.get("completed_at"),
            meta=serialize_meta(data.get("meta")),
        )

        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)


class EventCreateView(AuthenticatedAPIView):
    """Create a case event."""

    def post(self, request):
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        case = get_object_or_404(Case, pk=data["case_id"])
        event_kwargs = {
            "case": case,
            "type": data["type"],
            "source": data.get("source", ""),
            "payload": serialize_meta(data.get("payload")),
        }
        if data.get("occurred_at"):
            event_kwargs["occurred_at"] = data["occurred_at"]

        event = Event.objects.create(**event_kwargs)
        return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)


class CaseSummaryView(AuthenticatedAPIView):
    """Return summary information about a case."""

    def get(self, request, pk: int):
        case = get_object_or_404(
            Case.objects.select_related("client", "stage", "payment_plan"),
            pk=pk,
        )
        payment_totals = case.payments.aggregate(
            total_paid=Sum(
                "amount",
                filter=Q(status=Payment.PaymentStatus.PAID),
            ),
            total_planned=Sum(
                "amount",
                filter=Q(status=Payment.PaymentStatus.PLANNED),
            ),
        )
        total_paid = payment_totals["total_paid"] or Decimal("0")
        total_planned = payment_totals["total_planned"] or Decimal("0")

        try:
            currency = case.payment_plan.currency
        except PaymentPlan.DoesNotExist:
            currency = "RUB"

        response_data = {
            "case": {
                "id": case.id,
                "number": case.number,
                "opened_at": case.opened_at,
                "closed_at": case.closed_at,
                "comment": case.comment,
            },
            "client": ClientSerializer(case.client).data,
            "payments": {
                "total_paid": total_paid,
                "total_planned": total_planned,
                "currency": currency,
            },
            "stage": CaseStageSerializer(case.stage).data if case.stage else None,
        }
        return Response(response_data)
