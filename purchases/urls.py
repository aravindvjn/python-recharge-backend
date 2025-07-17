from django.urls import path
from . import views

urlpatterns = [
    path('purchase/', views.purchase_plan, name='purchase_plan'),
    path('history/', views.purchase_history, name='purchase_history'),
    path('history/<int:pk>/', views.purchase_detail, name='purchase_detail'),
    path('retry/<int:pk>/', views.retry_payment, name='retry_payment'),
]