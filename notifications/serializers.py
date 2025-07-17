from .models import Notification
from rest_framework import serializers
from .models import GlobalNotificationSetting


# Create your views here.

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['created_at', 'title', 'message']

class GlobalNotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalNotificationSetting
        fields = '__all__'
