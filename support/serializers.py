from rest_framework import serializers
from .models import Support

class SupportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Support
        fields = ['issue_type', 'description']  

class SupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Support
        fields = '__all__'

class SupportStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Support
        fields = ['status', 'resolution_notes']