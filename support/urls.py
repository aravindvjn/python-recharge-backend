from django.urls import path
from .views import SupportListView, SupportStatusUpdateView,SupportCreateView

urlpatterns = [
    path('supportcreate/', SupportCreateView.as_view(), name='support-create'),
    path('supportlist/', SupportListView.as_view(), name='support-list'),
    path('supportupdate/<int:id>/status/', SupportStatusUpdateView.as_view(), name='support-status-update'),
]