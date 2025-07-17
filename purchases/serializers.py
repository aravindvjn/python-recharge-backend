from rest_framework import serializers
from .models import PlanPurchase
from plans.serializers import PlansSerializer
from accounts.serializers import UserSignupSerializer
import uuid
from django.utils import timezone

class PlanPurchaseSerializer(serializers.ModelSerializer):
    plan = PlansSerializer(read_only=True)
    plan_id = serializers.IntegerField(write_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    plan_title = serializers.CharField(source='plan.title', read_only=True)
    provider_name = serializers.CharField(source='plan.provider.title', read_only=True)
    
    class Meta:
        model = PlanPurchase
        fields = [
            'id', 'plan', 'plan_id', 'user_email', 'user_name', 'plan_title', 'provider_name',
            'amount', 'payment_status', 'transaction_id', 'phone_number', 'payment_method',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['transaction_id', 'created_at', 'updated_at', 'completed_at']
    
    def create(self, validated_data):
        # Generate unique transaction ID
        validated_data['transaction_id'] = f"TXN_{uuid.uuid4().hex[:12].upper()}"
        return super().create(validated_data)

class PurchasePlanSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=15)
    payment_method = serializers.CharField(max_length=50, default='online')
    
    def validate_plan_id(self, value):
        from plans.models import Plans
        try:
            plan = Plans.objects.get(id=value, is_active=True)
            return value
        except Plans.DoesNotExist:
            raise serializers.ValidationError("Plan not found or not active")

from datetime import timedelta, date

class PurchaseHistorySerializer(serializers.ModelSerializer):
    plan_title = serializers.CharField(source='plan.title', read_only=True)
    provider_name = serializers.CharField(source='plan.provider.title', read_only=True)
    plan_validity = serializers.IntegerField(source='plan.validity', read_only=True)
    validity_left = serializers.SerializerMethodField()  # 👈 NEW FIELD

    class Meta:
        model = PlanPurchase
        fields = [
            'id', 'plan_title', 'provider_name', 'plan_validity', 'amount', 
            'payment_status', 'transaction_id', 'phone_number', 'payment_method',
            'created_at', 'completed_at', 'validity_left'  # 👈 ADD HERE
        ]

    def get_validity_left(self, obj):
        if obj.completed_at and obj.plan.validity:
            expiry_date = obj.completed_at.date() + timedelta(days=obj.plan.validity)
            remaining_days = (expiry_date - date.today()).days
            return max(0, remaining_days)  # don’t return negative values
        return None
