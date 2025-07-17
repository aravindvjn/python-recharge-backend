from django.shortcuts import render
from rest_framework import generics
from .models import Support
from .serializers import SupportSerializer, SupportStatusUpdateSerializer,SupportCreateSerializer
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminUserOnly
from notifications.utils import generate_notification_content,is_notification_allowed
from notifications.models import Notification
# List all support tickets
class SupportCreateView(generics.CreateAPIView):
    queryset = Support.objects.all()
    serializer_class = SupportCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # auto-assign user

class SupportListView(generics.ListAPIView):
    queryset = Support.objects.all()
    serializer_class = SupportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Support.objects.filter(user=self.request.user)


# Update status of a ticket
class SupportStatusUpdateView(generics.UpdateAPIView):
    queryset = Support.objects.all()
    serializer_class = SupportStatusUpdateSerializer
    permission_classes = [IsAuthenticated,IsAdminUserOnly]
    lookup_field = 'id'

    def perform_update(self, serializer):
        support = serializer.save()

        # ✅ Create notification after support update
        if is_notification_allowed('recharge_success', 'in_app'):
            data = generate_notification_content(
                user=support.user,
                notification_type='SUPPORT',
                related_id=support.id
                )
            Notification.objects.create(
                user=support.user,
                title=data['title'],
                message=data['message'],
                notification_type='SUPPORT',
                related_id=support.id
                )
