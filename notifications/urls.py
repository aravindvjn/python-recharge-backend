from django.urls import path
from .views import NotificationListView,NotificationSettingsView

urlpatterns = [
    path('listnotifications/', NotificationListView.as_view(), name='notification-list'),
    path('notification-settings/', NotificationSettingsView.as_view(), name='notification-settings'),
    

   
]
