from rest_framework import serializers
from .models import Provider, Plans

class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = ['id', 'title', 'is_active']

class PlansSerializer(serializers.ModelSerializer):
    provider = ProviderSerializer(read_only=True)
    provider_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Plans
        fields = [
            'id', 'provider', 'provider_id', 'title', 'description', 
            'validity', 'is_active', 'amount', 'identifier', 'created_at'
        ]
        read_only_fields = ['created_at']

class PlansListSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.title', read_only=True)
    
    class Meta:
        model = Plans
        fields = [
            'id', 'provider_name', 'title', 'description', 
            'validity', 'amount', 'identifier', 'created_at'
        ]