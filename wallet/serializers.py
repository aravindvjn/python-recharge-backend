from rest_framework import serializers
from .models import Wallet, WalletTransaction, UserMargin
from accounts.models import User, UserType

class WalletSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_type = serializers.CharField(source='user.user_type', read_only=True)
    
    class Meta:
        model = Wallet
        fields = ['id', 'user_email', 'user_type', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class WalletTransactionSerializer(serializers.ModelSerializer):
    wallet_user = serializers.EmailField(source='wallet.user.email', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = WalletTransaction
        fields = ['id', 'wallet_user', 'transaction_type', 'amount', 'description', 'created_by_email', 'created_at']
        read_only_fields = ['id', 'created_at']

class AddToWalletSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    description = serializers.CharField(max_length=500, required=False)
    
    def validate_user_email(self, value):
        try:
            user = User.objects.get(email=value)
            if user.user_type not in [UserType.DISTRIBUTOR, UserType.RETAILER]:
                raise serializers.ValidationError("Only distributors and retailers can have wallet transactions.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

class DebitFromWalletSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    description = serializers.CharField(max_length=500, required=False)
    
    def validate_user_email(self, value):
        try:
            user = User.objects.get(email=value)
            if user.user_type not in [UserType.DISTRIBUTOR, UserType.RETAILER]:
                raise serializers.ValidationError("Only distributors and retailers can have wallet transactions.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

class UserMarginSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_type = serializers.CharField(source='user.user_type', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True)
    
    class Meta:
        model = UserMargin
        fields = ['id', 'user_email', 'user_type', 'margin_percentage', 'admin_email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class SetMarginSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    margin_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0, max_value=100)
    
    def validate_user_email(self, value):
        try:
            user = User.objects.get(email=value)
            if user.user_type not in [UserType.DISTRIBUTOR, UserType.RETAILER]:
                raise serializers.ValidationError("Margin can only be set for distributors and retailers.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")