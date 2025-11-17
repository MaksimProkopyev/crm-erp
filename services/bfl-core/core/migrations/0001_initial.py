from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CaseStage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("order", models.PositiveIntegerField(default=0)),
                ("is_final", models.BooleanField(default=False)),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Client",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("first_name", models.CharField(max_length=150)),
                ("last_name", models.CharField(max_length=150)),
                ("patronymic", models.CharField(blank=True, max_length=150)),
                ("phone", models.CharField(max_length=32, unique=True)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("region", models.CharField(blank=True, max_length=150)),
                ("city", models.CharField(blank=True, max_length=150)),
                ("comment", models.TextField(blank=True)),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Case",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("number", models.CharField(blank=True, max_length=128)),
                ("opened_at", models.DateField(blank=True, null=True)),
                ("closed_at", models.DateField(blank=True, null=True)),
                ("idempotency_key", models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ("comment", models.TextField(blank=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cases", to="core.client")),
                ("stage", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.casestage")),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Lead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source", models.CharField(max_length=128)),
                ("channel", models.CharField(blank=True, max_length=128)),
                ("external_id", models.CharField(max_length=255)),
                ("utm_source", models.CharField(blank=True, max_length=255)),
                ("utm_medium", models.CharField(blank=True, max_length=255)),
                ("utm_campaign", models.CharField(blank=True, max_length=255)),
                ("utm_content", models.CharField(blank=True, max_length=255)),
                ("utm_term", models.CharField(blank=True, max_length=255)),
                ("case", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="lead", to="core.case")),
                ("client", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="leads", to="core.client")),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="PaymentPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="RUB", max_length=3)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("monthly_payment", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("meta", models.JSONField(blank=True, default=dict)),
                ("case", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="payment_plan", to="core.case")),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("date", models.DateField()),
                ("source", models.CharField(max_length=128)),
                ("status", models.CharField(choices=[("planned", "planned"), ("paid", "paid"), ("failed", "failed")], default="paid", max_length=16)),
                ("meta", models.JSONField(blank=True, default=dict)),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="core.case")),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Task",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("type", models.CharField(max_length=128)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[
                    ("pending", "pending"),
                    ("in_progress", "in_progress"),
                    ("done", "done"),
                    ("cancelled", "cancelled"),
                ], default="pending", max_length=16)),
                ("assignee", models.CharField(blank=True, max_length=255)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("meta", models.JSONField(blank=True, default=dict)),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tasks", to="core.case")),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("type", models.CharField(max_length=128)),
                ("source", models.CharField(blank=True, max_length=128)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="core.case")),
            ],
            options={"ordering": ["-occurred_at"]},
        ),
        migrations.AddConstraint(
            model_name="lead",
            constraint=models.UniqueConstraint(fields=("source", "external_id"), name="lead_source_external_unique"),
        ),
    ]
