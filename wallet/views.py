from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Wallet, WalletTransaction, UserMargin
from .serializers import (
    WalletSerializer, WalletTransactionSerializer, AddToWalletSerializer,
    DebitFromWalletSerializer, UserMarginSerializer, SetMarginSerializer
)
from accounts.models import User, UserType

class WalletListView(generics.ListAPIView):
    """
    List Wallets
    
    Get list of wallets. Admins see all wallets, users see only their own.
    """
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="List Wallets",
        operation_description="Get list of wallets. Admins see all wallets, users see only their own.",
        responses={
            200: openapi.Response(
                description="List of wallets",
                examples={
                    "application/json": {
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "user_email": "distributor@example.com",
                                "user_type": 2,
                                "balance": "1500.00",
                                "created_at": "2024-01-15T10:30:00Z",
                                "updated_at": "2024-01-15T15:45:00Z"
                            }
                        ]
                    }
                }
            )
        },
        tags=['Wallet Management']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Wallet.objects.all().select_related('user')
        else:
            return Wallet.objects.filter(user=user)

class WalletDetailView(generics.RetrieveAPIView):
    """
    Get Wallet Details
    
    Get detailed wallet information. Admins can view any wallet, users can only view their own.
    """
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get Wallet Details",
        operation_description="Get detailed wallet information. Admins can view any wallet, users can only view their own.",
        responses={
            200: openapi.Response(
                description="Wallet details",
                examples={
                    "application/json": {
                        "id": 1,
                        "user_email": "distributor@example.com",
                        "user_type": 2,
                        "balance": "1500.00",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T15:45:00Z"
                    }
                }
            ),
            404: openapi.Response(
                description="Wallet not found",
                examples={
                    "application/json": {
                        "detail": "Not found."
                    }
                }
            )
        },
        tags=['Wallet Management']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Wallet.objects.all().select_related('user')
        else:
            return Wallet.objects.filter(user=user)

class WalletTransactionListView(generics.ListAPIView):
    """
    List Wallet Transactions
    
    Get wallet transaction history. Admins see all transactions, users see only their own.
    """
    serializer_class = WalletTransactionSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="List Wallet Transactions",
        operation_description="Get wallet transaction history. Admins see all transactions, users see only their own.",
        responses={
            200: openapi.Response(
                description="List of wallet transactions",
                examples={
                    "application/json": {
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "wallet_user": "distributor@example.com",
                                "transaction_type": "add_to_wallet",
                                "amount": "1000.00",
                                "description": "Initial wallet funding",
                                "created_by_email": "admin@example.com",
                                "created_at": "2024-01-15T10:30:00Z"
                            }
                        ]
                    }
                }
            )
        },
        tags=['Wallet Management']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return WalletTransaction.objects.all().select_related('wallet__user', 'created_by')
        else:
            return WalletTransaction.objects.filter(wallet__user=user).select_related('wallet__user', 'created_by')

@swagger_auto_schema(
    method='post',
    operation_summary="Add Money to Wallet (Admin Only)",
    operation_description="Add money to a distributor or retailer wallet",
    request_body=AddToWalletSerializer,
    responses={
        200: openapi.Response(
            description="Money added successfully",
            examples={
                "application/json": {
                    "message": "Money added to wallet successfully",
                    "wallet": {
                        "id": 1,
                        "user_email": "distributor@example.com",
                        "user_type": 2,
                        "balance": "1500.00",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T16:00:00Z"
                    }
                }
            }
        ),
        400: openapi.Response(
            description="Bad request - validation errors",
            examples={
                "application/json": {
                    "user_email": ["User with this email does not exist."]
                }
            }
        ),
        403: openapi.Response(
            description="Forbidden - Admin access required",
            examples={
                "application/json": {
                    "error": "Only admins can add money to wallets"
                }
            }
        ),
        404: openapi.Response(
            description="User not found",
            examples={
                "application/json": {
                    "error": "User not found"
                }
            }
        )
    },
    tags=['Wallet Management']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_wallet(request):
    if not request.user.is_admin:
        return Response({"error": "Only admins can add money to wallets"}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = AddToWalletSerializer(data=request.data)
    if serializer.is_valid():
        user_email = serializer.validated_data['user_email']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        
        try:
            with transaction.atomic():
                user = User.objects.get(email=user_email)
                wallet, _ = Wallet.objects.get_or_create(user=user)
                
                wallet.add_balance(amount)
                
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='add_to_wallet',
                    amount=amount,
                    description=description,
                    created_by=request.user
                )
                
                return Response({
                    "message": "Money added to wallet successfully",
                    "wallet": WalletSerializer(wallet).data
                }, status=status.HTTP_200_OK)
                
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    operation_summary="Debit Money from Wallet (Admin Only)",
    operation_description="Debit money from a distributor or retailer wallet",
    request_body=DebitFromWalletSerializer,
    responses={
        200: openapi.Response(
            description="Money debited successfully",
            examples={
                "application/json": {
                    "message": "Money debited from wallet successfully",
                    "wallet": {
                        "id": 1,
                        "user_email": "distributor@example.com",
                        "user_type": 2,
                        "balance": "1250.00",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T16:30:00Z"
                    }
                }
            }
        ),
        400: openapi.Response(
            description="Bad request - insufficient balance or validation errors",
            examples={
                "application/json": {
                    "error": "Insufficient wallet balance"
                }
            }
        ),
        403: openapi.Response(
            description="Forbidden - Admin access required",
            examples={
                "application/json": {
                    "error": "Only admins can debit money from wallets"
                }
            }
        ),
        404: openapi.Response(
            description="User not found",
            examples={
                "application/json": {
                    "error": "User not found"
                }
            }
        )
    },
    tags=['Wallet Management']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def debit_from_wallet(request):
    if not request.user.is_admin:
        return Response({"error": "Only admins can debit money from wallets"}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = DebitFromWalletSerializer(data=request.data)
    if serializer.is_valid():
        user_email = serializer.validated_data['user_email']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        
        try:
            with transaction.atomic():
                user = User.objects.get(email=user_email)
                wallet = get_object_or_404(Wallet, user=user)
                
                if not wallet.can_debit(amount):
                    return Response({"error": "Insufficient wallet balance"}, status=status.HTTP_400_BAD_REQUEST)
                
                wallet.debit_balance(amount)
                
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='debit_from_wallet',
                    amount=amount,
                    description=description,
                    created_by=request.user
                )
                
                return Response({
                    "message": "Money debited from wallet successfully",
                    "wallet": WalletSerializer(wallet).data
                }, status=status.HTTP_200_OK)
                
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    operation_summary="Set User Margin (Admin Only)",
    operation_description="Set margin percentage for a distributor or retailer",
    request_body=SetMarginSerializer,
    responses={
        200: openapi.Response(
            description="Margin set successfully",
            examples={
                "application/json": {
                    "message": "User margin set successfully",
                    "margin": {
                        "id": 1,
                        "user_email": "distributor@example.com",
                        "user_type": 2,
                        "margin_percentage": "5.50",
                        "admin_email": "admin@example.com",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T16:45:00Z"
                    }
                }
            }
        ),
        400: openapi.Response(
            description="Bad request - validation errors",
            examples={
                "application/json": {
                    "user_email": ["User with this email does not exist."]
                }
            }
        ),
        403: openapi.Response(
            description="Forbidden - Admin access required",
            examples={
                "application/json": {
                    "error": "Only admins can set user margins"
                }
            }
        ),
        404: openapi.Response(
            description="User not found",
            examples={
                "application/json": {
                    "error": "User not found"
                }
            }
        )
    },
    tags=['Wallet Management']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_user_margin(request):
    if not request.user.is_admin:
        return Response({"error": "Only admins can set user margins"}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = SetMarginSerializer(data=request.data)
    if serializer.is_valid():
        user_email = serializer.validated_data['user_email']
        margin_percentage = serializer.validated_data['margin_percentage']
        
        try:
            user = User.objects.get(email=user_email)
            margin, _ = UserMargin.objects.update_or_create(
                admin=request.user,
                user=user,
                defaults={'margin_percentage': margin_percentage}
            )
            
            return Response({
                "message": "User margin set successfully",
                "margin": UserMarginSerializer(margin).data
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserMarginListView(generics.ListAPIView):
    """
    List User Margins
    
    Get list of user margins. Admins see margins they set, users see their own margin.
    """
    serializer_class = UserMarginSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="List User Margins",
        operation_description="Get list of user margins. Admins see margins they set, users see their own margin.",
        responses={
            200: openapi.Response(
                description="List of user margins",
                examples={
                    "application/json": {
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "user_email": "distributor@example.com",
                                "user_type": 2,
                                "margin_percentage": "5.50",
                                "admin_email": "admin@example.com",
                                "created_at": "2024-01-15T10:30:00Z",
                                "updated_at": "2024-01-15T16:45:00Z"
                            }
                        ]
                    }
                }
            )
        },
        tags=['Wallet Management']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return UserMargin.objects.filter(admin=user).select_related('user', 'admin')
        else:
            return UserMargin.objects.filter(user=user).select_related('user', 'admin')