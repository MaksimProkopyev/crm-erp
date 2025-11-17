from django.urls import path

from .views import (
    CaseSetStageView,
    CaseSummaryView,
    EventCreateView,
    HealthCheckView,
    ImportCaseFromLeadView,
    PaymentRecordView,
    TaskCreateView,
)

urlpatterns = [
    path("health", HealthCheckView.as_view(), name="health"),
    path("cases/import-from-lead", ImportCaseFromLeadView.as_view(), name="case-import"),
    path("cases/<int:pk>/set-stage", CaseSetStageView.as_view(), name="case-set-stage"),
    path("cases/<int:pk>/summary", CaseSummaryView.as_view(), name="case-summary"),
    path("payments/record", PaymentRecordView.as_view(), name="payment-record"),
    path("tasks", TaskCreateView.as_view(), name="task-create"),
    path("events", EventCreateView.as_view(), name="event-create"),
]
