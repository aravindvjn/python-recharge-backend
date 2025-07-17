from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import PlanPurchase
from .serializers import PlanPurchaseSerializer, PurchasePlanSerializer, PurchaseHistorySerializer
from plans.models import Plans
import random
import time
import uuid
from notifications.utils import generate_notification_content,is_notification_allowed
from notifications.models import Notification

def generate_unique_transaction_id():
    return f"TXN-{uuid.uuid4().hex[:10]}"



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase_plan(request):
    serializer = PurchasePlanSerializer(data=request.data)
    if serializer.is_valid():
        plan_id = serializer.validated_data['plan_id']
        phone_number = serializer.validated_data['phone_number']
        payment_method = serializer.validated_data['payment_method']
        
        try:
            plan = Plans.objects.get(id=plan_id, is_active=True)

            transaction_id = generate_unique_transaction_id()
            
            
            # Create purchase record
            purchase = PlanPurchase.objects.create(
                user=request.user,
                plan=plan,
                amount=plan.amount,
                phone_number=phone_number,
                payment_method=payment_method,
                payment_status='pending',
                transaction_id=transaction_id 
            )
            
            # Simulate payment processing
            # In a real app, you would integrate with payment gateway here
            time.sleep(1)  # Simulate processing time
            
            # Random success/failure for demo (80% success rate)
            payment_success = random.choice([True, True, True, True, False])
            
            if payment_success:
                purchase.payment_status = 'success'
                purchase.completed_at = timezone.now()
                purchase.payment_gateway_response = {
                    'status': 'success',
                    'message': 'Payment completed successfully',
                    'gateway_txn_id': f"GTW_{purchase.transaction_id}"
                }
                # Send RECHARGE notification
                if is_notification_allowed('recharge_success', 'in_app'):
                    data = generate_notification_content(request.user, 'RECHARGE', related_id=purchase.id)
                    Notification.objects.create(
                        user=request.user,
                        title=data['title'],
                        message=data['message'],
                        notification_type='RECHARGE',
                        related_id=purchase.id
                        )
            else:
                purchase.payment_status = 'failed'
                purchase.payment_gateway_response = {
                    'status': 'failed',
                    'message': 'Payment failed due to insufficient funds',
                    'error_code': 'INSUFFICIENT_FUNDS'
                }
                 # ❌ Optionally send failed payment notification
                if is_notification_allowed('recharge_success', 'in_app'):
                    Notification.objects.create(
                        user=request.user,
                        title="Recharge Failed",
                        message=f"Hi {request.user.first_name or request.user.email.split('@')[0]},\n\n"
                            f"Your payment for the plan '{plan.title}' failed due to insufficient funds.\n"
                            f"Please try again.",
                        notification_type='RECHARGE',
                        related_id=purchase.id
                        )
            
            purchase.save()
            
            serializer = PlanPurchaseSerializer(purchase)
            return Response({
                'message': 'Purchase processed successfully',
                'purchase': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Plans.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
            
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def purchase_history(request):
    purchases = PlanPurchase.objects.filter(user=request.user).select_related('plan', 'plan__provider')
    
    # Filter by payment status
    payment_status = request.GET.get('payment_status', '')
    if payment_status:
        purchases = purchases.filter(payment_status=payment_status)
    
    # Filter by date range
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if start_date:
        purchases = purchases.filter(created_at__gte=start_date)
    if end_date:
        purchases = purchases.filter(created_at__lte=end_date)
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        purchases = purchases.filter(
            Q(plan__title__icontains=search) |
            Q(plan__provider__title__icontains=search) |
            Q(transaction_id__icontains=search) |
            Q(phone_number__icontains=search)
        )
    
    # Filter by provider
    provider_id = request.GET.get('provider_id', '')
    if provider_id:
        purchases = purchases.filter(plan__provider_id=provider_id)
    
    # Ordering
    ordering = request.GET.get('ordering', '-created_at')
    if ordering in ['created_at', '-created_at', 'amount', '-amount', 'payment_status']:
        purchases = purchases.order_by(ordering)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = purchases.count()
    purchases_page = purchases[start:end]
    
    serializer = PurchaseHistorySerializer(purchases_page, many=True)
    
    return Response({
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
        'results': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def purchase_detail(request, pk):
    try:
        purchase = PlanPurchase.objects.select_related('plan', 'plan__provider').get(
            pk=pk, user=request.user
        )
        serializer = PlanPurchaseSerializer(purchase)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except PlanPurchase.DoesNotExist:
        return Response({'error': 'Purchase not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_payment(request, pk):
    try:
        purchase = PlanPurchase.objects.get(pk=pk, user=request.user, payment_status='failed')
        
        # Reset payment status to pending
        purchase.payment_status = 'pending'
        purchase.save()
        
        # Simulate retry payment processing
        time.sleep(1)
        
        # Random success/failure for demo (70% success rate on retry)
        payment_success = random.choice([True, True, True, False])
        
        if payment_success:
            purchase.payment_status = 'success'
            purchase.completed_at = timezone.now()
            purchase.payment_gateway_response = {
                'status': 'success',
                'message': 'Payment completed successfully on retry',
                'gateway_txn_id': f"GTW_{purchase.transaction_id}_RETRY"
            }
        else:
            purchase.payment_status = 'failed'
            purchase.payment_gateway_response = {
                'status': 'failed',
                'message': 'Payment failed on retry',
                'error_code': 'PAYMENT_DECLINED'
            }
        
        purchase.save()
        
        serializer = PlanPurchaseSerializer(purchase)
        return Response({
            'message': 'Payment retry processed',
            'purchase': serializer.data
        }, status=status.HTTP_200_OK)
        
    except PlanPurchase.DoesNotExist:
        return Response({'error': 'Purchase not found or not eligible for retry'}, status=status.HTTP_404_NOT_FOUND)
