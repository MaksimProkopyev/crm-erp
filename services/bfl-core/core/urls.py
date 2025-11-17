from django.urls import path

from .views import (
    CaseImportView,
    CaseStageUpdateView,
    CaseSummaryView,
    EventCreateView,
    HealthCheckView,
    PaymentRecordView,
    TaskCreateView,
)

urlpatterns = [
    path("health", HealthCheckView.as_view(), name="health"),
    path("cases/import-from-lead", CaseImportView.as_view(), name="case-import"),
    path("cases/<int:case_id>/set-stage", CaseStageUpdateView.as_view(), name="case-set-stage"),
    path("payments/record", PaymentRecordView.as_view(), name="payment-record"),
    path("tasks", TaskCreateView.as_view(), name="task-create"),
    path("events", EventCreateView.as_view(), name="event-create"),
    path("cases/<int:case_id>/summary", CaseSummaryView.as_view(), name="case-summary"),
]
