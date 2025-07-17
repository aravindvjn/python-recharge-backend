from django.urls import path
from .views import CreateRazorpayOrderAPIView, RazorpayPaymentSuccessAPIView

urlpatterns = [
    path('create-order/', CreateRazorpayOrderAPIView.as_view(), name='create-order'),
    path('payment-success/', RazorpayPaymentSuccessAPIView.as_view(), name='payment-success'),
]
