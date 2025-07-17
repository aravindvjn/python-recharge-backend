from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone
from django.conf import settings
from purchases.models import PlanPurchase

# Enum-like choices for issue_type and status
ISSUE_TYPES = (
    ('RECHARGE_FAILURE', 'Recharge Failure'),
    ('PAYMENT_ISSUE', 'Payment Issue'),
    ('PLAN_QUERY', 'Plan Query'),
    ('ACCOUNT_ISSUE', 'Account Issue'),
    ('OTHER', 'Other'),
)

SUPPORT_STATUSES = (
    ('OPEN', 'Open'),
    ('IN_PROGRESS', 'In Progress'),
    ('RESOLVED', 'Resolved'),
    ('CLOSED', 'Closed'),
)

class Support(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='support_tickets'
    )
    # Temporarily relax the foreign key
    transaction = models.ForeignKey(PlanPurchase, on_delete=models.CASCADE, null=True, blank=True)
    issue_type = models.CharField(max_length=20, choices=ISSUE_TYPES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=SUPPORT_STATUSES, default='OPEN')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_support_tickets'
    )
    resolution_notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.issue_type} [{self.status}]"
