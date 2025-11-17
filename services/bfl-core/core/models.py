from __future__ import annotations

from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Client(TimeStampedModel):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    patronymic = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=32, unique=True)
    email = models.EmailField(blank=True)
    region = models.CharField(max_length=150, blank=True)
    city = models.CharField(max_length=150, blank=True)
    comment = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name}"


class CaseStage(TimeStampedModel):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    is_final = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.code}: {self.name}"


class Case(TimeStampedModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="cases")
    number = models.CharField(max_length=128, blank=True)
    stage = models.ForeignKey(CaseStage, null=True, blank=True, on_delete=models.SET_NULL)
    opened_at = models.DateField(null=True, blank=True)
    closed_at = models.DateField(null=True, blank=True)
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )
    comment = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"Case {self.id}"


class Lead(TimeStampedModel):
    client = models.ForeignKey(Client, null=True, blank=True, on_delete=models.SET_NULL, related_name="leads")
    case = models.OneToOneField(Case, null=True, blank=True, on_delete=models.SET_NULL, related_name="lead")
    source = models.CharField(max_length=128)
    channel = models.CharField(max_length=128, blank=True)
    external_id = models.CharField(max_length=255)
    utm_source = models.CharField(max_length=255, blank=True)
    utm_medium = models.CharField(max_length=255, blank=True)
    utm_campaign = models.CharField(max_length=255, blank=True)
    utm_content = models.CharField(max_length=255, blank=True)
    utm_term = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "external_id"], name="lead_source_external_unique"),
        ]


class PaymentPlan(TimeStampedModel):
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name="payment_plan")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="RUB")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    monthly_payment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)


class Payment(TimeStampedModel):
    class PaymentStatus(models.TextChoices):
        PLANNED = "planned", "planned"
        PAID = "paid", "paid"
        FAILED = "failed", "failed"

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    source = models.CharField(max_length=128)
    status = models.CharField(max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.PAID)
    meta = models.JSONField(default=dict, blank=True)


class Task(TimeStampedModel):
    class TaskStatus(models.TextChoices):
        PENDING = "pending", "pending"
        IN_PROGRESS = "in_progress", "in_progress"
        DONE = "done", "done"
        CANCELLED = "cancelled", "cancelled"

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="tasks")
    type = models.CharField(max_length=128)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    assignee = models.CharField(max_length=255, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)


class Event(TimeStampedModel):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="events")
    type = models.CharField(max_length=128)
    source = models.CharField(max_length=128, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at"]
