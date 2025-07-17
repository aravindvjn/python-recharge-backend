from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from accounts.models import UserType

User = get_user_model()

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - Balance: ₹{self.balance}"
    
    def can_debit(self, amount):
        return self.balance >= amount
    
    def add_balance(self, amount):
        self.balance += amount
        self.save()
    
    def debit_balance(self, amount):
        if self.can_debit(amount):
            self.balance -= amount
            self.save()
            return True
        return False

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('add_to_wallet', 'Add to Wallet'),
        ('debit_from_wallet', 'Debit from Wallet'),
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions_created')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.wallet.user.email} - {self.transaction_type} - ₹{self.amount}"

class UserMargin(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_margins', limit_choices_to={'user_type': UserType.ADMIN})
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='margin_settings', limit_choices_to={'user_type__in': [UserType.DISTRIBUTOR, UserType.RETAILER]})
    margin_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Margin percentage (e.g., 5.50 for 5.5%)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['admin', 'user']
    
    def __str__(self):
        return f"{self.user.email} - Margin: {self.margin_percentage}%"