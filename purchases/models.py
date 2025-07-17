from django.db import models
from django.contrib.auth import get_user_model
from plans.models import Plans

User = get_user_model()

class PlanPurchase(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    plan = models.ForeignKey(Plans, on_delete=models.CASCADE, related_name='purchases')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=15)
    payment_method = models.CharField(max_length=50, default='online')
    payment_gateway_response = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Plan Purchase'
        verbose_name_plural = 'Plan Purchases'
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.title} - {self.payment_status}"
