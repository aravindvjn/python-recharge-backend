from rest_framework import generics, permissions
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from rest_framework.permissions import IsAdminUser
from .models import GlobalNotificationSetting
from .serializers import GlobalNotificationSettingSerializer

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
class NotificationSettingsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        settings = GlobalNotificationSetting.objects.first()
        serializer = GlobalNotificationSettingSerializer(settings)
        return Response(serializer.data)

    def put(self, request):
        settings = GlobalNotificationSetting.objects.first()
        serializer = GlobalNotificationSettingSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Settings updated', 'data': serializer.data})
        return Response(serializer.errors, status=400)
