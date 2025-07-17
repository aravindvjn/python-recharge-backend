from django.db import models
from django.utils import timezone
from django.conf import settings



# Create your models here.from django.utils import timezone

# Enum-like choices for notification_type and status
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

NOTIFICATION_TYPES = (
    ('RECHARGE', 'Recharge'),
    ('SUPPORT', 'Support'),
    ('PROMOTION', 'Promotion'),
    ('ACCOUNT', 'Account'),
    ('OTHER', 'Other'),
)

NOTIFICATION_STATUSES = (
    ('SENT', 'Sent'),
    ('DELIVERED', 'Delivered'),
    ('READ', 'Read'),
    ('FAILED', 'Failed'),
)

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    status = models.CharField(max_length=20, choices=NOTIFICATION_STATUSES, default='SENT')
    created_at = models.DateTimeField(default=timezone.now)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    related_id = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Notification #{self.id} - {self.title} ({self.notification_type})"

    class Meta:
        db_table = 'notifications'

class GlobalNotificationSetting(models.Model):
    # Channels
    in_app = models.BooleanField(default=True)
    email = models.BooleanField(default=False)
    sms = models.BooleanField(default=False)

    # Types
    recharge_success = models.BooleanField(default=True)
    recharge_failed = models.BooleanField(default=True)
    new_user_registered = models.BooleanField(default=True)
    low_balance = models.BooleanField(default=True)
    maintenance_scheduled = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Global Notification Settings"

class LowBalanceThreshold(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=10000)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Low Balance Threshold: ₹{self.amount}"

   
        ...
