from accounts.models import UserType
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import User, OTP, UserType, UserProfile
from .serializers import (
    UserSignupSerializer, UserLoginSerializer, OTPGenerateSerializer,
    OTPVerifySerializer, UserSerializer, CreateUserSerializer,
    UpdateUserSerializer, PasswordResetSerializer, UserProfileSerializer
)
import random
import string
from notifications.models import Notification
from notifications.utils import generate_notification_content,is_notification_allowed


@swagger_auto_schema(
    method='post',
    operation_summary="User Registration",
    operation_description="Register a new user account with email, phone, and personal details",
    request_body=UserSignupSerializer,
    responses={
        201: openapi.Response(
            description="User created successfully",
            examples={
                "application/json": {
                    "message": "User created successfully",
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "phone": "+1234567890",
                        "name": "John Doe",
                        "user_type": 4
                    },
                    "tokens": {
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                    }
                }
            }
        ),
        400: openapi.Response(
            description="Bad request - validation errors",
            examples={
                "application/json": {
                    "email": ["User with this email already exists."],
                    "password": ["This password is too common."]
                }
            }
        )
    },
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = UserSignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        if is_notification_allowed('recharge_success', 'in_app'):
            data = generate_notification_content(user, 'USER_REGISTERED')
            Notification.objects.create(
                user=user,
                title=data['title'],
                message=data['message'],
                notification_type='USER_REGISTERED'
)

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'phone': user.phone,
                'name': f"{user.first_name} {user.last_name}",
                'user_type': user.user_type,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_summary="Email Login",
    operation_description="Login using email and password to get JWT tokens",
    request_body=UserLoginSerializer,
    responses={
        200: openapi.Response(
            description="Login successful",
            examples={
                "application/json": {
                    "message": "Login successful",
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "phone": "+1234567890",
                        "name": "John Doe",
                        "user_type": 4
                    },
                    "tokens": {
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                    }
                }
            }
        ),
        401: openapi.Response(
            description="Invalid credentials",
            examples={
                "application/json": {
                    "error": "Invalid credentials"
                }
            }
        ),
        400: openapi.Response(
            description="Bad request - validation errors",
            examples={
                "application/json": {
                    "email": ["This field is required."],
                    "password": ["This field is required."]
                }
            }
        )
    },
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_email(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(username=email, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'phone': user.phone,
                    'name': f"{user.first_name} {user.last_name}",
                    'user_type': user.user_type,
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


OTP_COOLDOWN_SECONDS = 120  # Cooldown of 1 minute


@swagger_auto_schema(
    method='post',
    operation_summary="Generate OTP",
    operation_description="Generate OTP for phone number authentication",
    request_body=OTPGenerateSerializer,
    responses={
        200: openapi.Response(
            description="OTP generated successfully",
            examples={
                "application/json": {
                    "message": "OTP generated successfully",
                    "otp": "123456",
                    "expires_in": "1 minute"
                }
            }
        ),
        400: openapi.Response(
            description="Bad request - validation errors",
            examples={
                "application/json": {
                    "phone": ["Phone number not registered"]
                }
            }
        )
    },
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def generate_otp(request):
    serializer = OTPGenerateSerializer(data=request.data)
    if serializer.is_valid():
        phone = serializer.validated_data['phone']

        # Save the serializer to trigger user creation if needed
        serializer.create(validated_data=serializer.validated_data)

        # Check cooldown logic
        last_otp = OTP.objects.filter(
            phone=phone).order_by('-created_at').first()
        if last_otp and timezone.now() < last_otp.created_at + timedelta(seconds=OTP_COOLDOWN_SECONDS):
            remaining = (last_otp.created_at +
                         timedelta(seconds=OTP_COOLDOWN_SECONDS)) - timezone.now()
            return Response({
                'message': f"Please wait {int(remaining.total_seconds())} seconds before requesting another OTP."
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Generate 6-digit OTP
        otp_code = ''.join(random.choices(string.digits, k=6))

        # Create OTP record
        otp = OTP.objects.create(phone=phone, code=otp_code)

        # In a real application, send the OTP via SMS here (e.g., using an SMS service like Twilio)
        # For testing, return OTP in response (remove in production)
        return Response({
            'message': 'OTP generated successfully',
            'otp': otp_code,  # Remove this in production for security
            'expires_in': '60 seconds'  # Match with OTP model expiration if defined
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_summary="Verify OTP",
    operation_description="Verify OTP code and get JWT tokens",
    request_body=OTPVerifySerializer,
    responses={
        200: openapi.Response(
            description="OTP verified successfully",
            examples={
                "application/json": {
                    "message": "OTP verified successfully",
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "phone": "+1234567890",
                        "name": "John Doe",
                        "user_type": 4
                    },
                    "tokens": {
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                    }
                }
            }
        ),
        400: openapi.Response(
            description="Invalid or expired OTP",
            examples={
                "application/json": {
                    "error": "Invalid or expired OTP"
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
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    serializer = OTPVerifySerializer(data=request.data)
    if serializer.is_valid():
        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']

        try:
            otp = OTP.objects.filter(
                phone=phone, code=code).latest('created_at')

            # MODIFIED: Check if OTP is expired or already verified
            if not otp.is_valid():
                return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)

            #  MODIFIED: Mark OTP as verified
            otp.is_verified = True
            otp.save()

            # Get user by phone
            user = User.objects.get(phone=phone)
            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'OTP verified successfully',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'phone': user.phone,
                    'name': f"{user.first_name} {user.last_name}",
                    'user_type': user.user_type,
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)

        except OTP.DoesNotExist:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# # view for user_profile


# @api_view(['POST', 'PUT', 'PATCH'])
# @permission_classes([IsAuthenticated])
# def user_profile_create_or_update(request):
#     profile = UserProfile.objects.filter(user=request.user).first()
# # profile creation
#     if request.method == 'POST':
#         if profile:
#             return Response({"error": "Profile already exists"}, status=400)
#         serializer = UserProfileSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(user=request.user)
#             return Response({
#                 "message": "Profile created successfully",
#                 "profile": serializer.data
#             }, status=201)
#         return Response(serializer.errors, status=400)
# # profile update - PUT OR PATCH
#     elif request.method in ['PUT', 'PATCH']:
#         if not profile:
#             return Response({"error": "Profile not found"}, status=404)
#         serializer = UserProfileSerializer(
#             profile, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({
#                 "message": "Profile updated successfully",
#                 "profile": serializer.data
#             })
#         return Response(serializer.errors, status=400)

# Admin Management Views


class UserListView(generics.ListAPIView):
    """
    List Users (Admin Only)

    Get list of distributors and retailers. Supports filtering by user_type parameter.
    - user_type: Filter by user type (2=Distributor, 3=Retailer)
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List Users (Admin Only)",
        operation_description="Get list of distributors and retailers. Supports filtering by user_type parameter.",
        manual_parameters=[
            openapi.Parameter('user_type', openapi.IN_QUERY,
                              description="Filter by user type (2=Distributor, 3=Retailer)", type=openapi.TYPE_INTEGER)
        ],
        responses={
            200: openapi.Response(
                description="List of users",
                examples={
                    "application/json": {
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 2,
                                "email": "distributor@example.com",
                                "username": "distributor@example.com",
                                "first_name": "John",
                                "last_name": "Distributor",
                                "phone": "+1234567891",
                                "user_type": 2,
                                "user_type_display": "Distributor",
                                "is_active": True,
                                "date_joined": "2024-01-15T10:30:00Z",
                                "wallet_balance": "1500.00",
                                "wallet_id": 1
                            }
                        ]
                    }
                }
            ),
            403: openapi.Response(
                description="Forbidden - Admin access required",
                examples={
                    "application/json": {
                        "detail": "You do not have permission to perform this action."
                    }
                }
            )
        },
        tags=['Admin - User Management']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if not self.request.user.is_admin:
            return User.objects.none()

        user_type = self.request.query_params.get('user_type')
        queryset = User.objects.filter(
            user_type__in=[UserType.DISTRIBUTOR, UserType.RETAILER]).select_related('wallet')

        if user_type:
            try:
                user_type_int = int(user_type)
                if user_type_int in [UserType.DISTRIBUTOR, UserType.RETAILER]:
                    queryset = queryset.filter(user_type=user_type_int)
            except (ValueError, TypeError):
                pass

        return queryset.order_by('-date_joined')


@swagger_auto_schema(
    method='post',
    operation_summary="Create User (Admin Only)",
    operation_description="Create a new distributor or retailer account",
    request_body=CreateUserSerializer,
    responses={
        201: openapi.Response(
            description="User created successfully",
            examples={
                "application/json": {
                    "message": "User created successfully",
                    "user": {
                        "id": 4,
                        "email": "newuser@example.com",
                        "username": "newuser@example.com",
                        "first_name": "New",
                        "last_name": "User",
                        "phone": "+1234567893",
                        "user_type": 2,
                        "user_type_display": "Distributor",
                        "is_active": True,
                        "date_joined": "2024-01-15T12:30:00Z",
                        "wallet_balance": "0.00",
                        "wallet_id": 2
                    }
                }
            }
        ),
        400: openapi.Response(
            description="Bad request - validation errors",
            examples={
                "application/json": {
                    "email": ["User with this email already exists."],
                    "password": ["This password is too common."]
                }
            }
        ),
        403: openapi.Response(
            description="Forbidden - Admin access required",
            examples={
                "application/json": {
                    "error": "Only admins can create users"
                }
            }
        )
    },
    tags=['Admin - User Management']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_user(request):
    if not request.user.is_admin:
        return Response({"error": "Only admins can create users"}, status=status.HTTP_403_FORBIDDEN)

    serializer = CreateUserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Reload user with wallet to get accurate serialized data
        user_with_wallet = User.objects.select_related(
            'wallet').get(id=user.id)
        return Response({
            "message": "User created successfully",
            "user": UserSerializer(user_with_wallet).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    operation_summary="Get User Details (Admin Only)",
    operation_description="Get detailed information about a specific distributor or retailer",
    responses={
        200: openapi.Response(
            description="User details",
            examples={
                "application/json": {
                    "id": 2,
                    "email": "distributor@example.com",
                    "username": "distributor@example.com",
                    "first_name": "John",
                    "last_name": "Distributor",
                    "phone": "+1234567891",
                    "user_type": 2,
                    "user_type_display": "Distributor",
                    "is_active": True,
                    "date_joined": "2024-01-15T10:30:00Z",
                    "wallet_balance": "1500.00",
                    "wallet_id": 1
                }
            }
        ),
        403: openapi.Response(
            description="Forbidden - Admin access required",
            examples={
                "application/json": {
                    "error": "Only admins can view user details"
                }
            }
        ),
        404: openapi.Response(
            description="User not found",
            examples={
                "application/json": {
                    "detail": "Not found."
                }
            }
        )
    },
    tags=['Admin - User Management']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request, user_id):
    if not request.user.is_admin:
        return Response({"error": "Only admins can view user details"}, status=status.HTTP_403_FORBIDDEN)

    user = get_object_or_404(User.objects.select_related(
        'wallet'), id=user_id, user_type__in=[UserType.DISTRIBUTOR, UserType.RETAILER])
    return Response(UserSerializer(user).data)


@swagger_auto_schema(
    method='put',
    operation_summary="Update User (Admin Only)",
    operation_description="Update distributor or retailer information",
    request_body=UpdateUserSerializer,
    responses={
        200: openapi.Response(
            description="User updated successfully",
            examples={
                "application/json": {
                    "message": "User updated successfully",
                    "user": {
                        "id": 2,
                        "email": "updated@example.com",
                        "username": "updated@example.com",
                        "first_name": "Updated",
                        "last_name": "User",
                        "phone": "+1234567891",
                        "user_type": 2,
                        "user_type_display": "Distributor",
                        "is_active": True,
                        "date_joined": "2024-01-15T10:30:00Z",
                        "wallet_balance": "1500.00",
                        "wallet_id": 1
                    }
                }
            }
        ),
        400: openapi.Response(
            description="Bad request - validation errors",
            examples={
                "application/json": {
                    "email": ["User with this email already exists."]
                }
            }
        ),
        403: openapi.Response(
            description="Forbidden - Admin access required",
            examples={
                "application/json": {
                    "error": "Only admins can update users"
                }
            }
        ),
        404: openapi.Response(
            description="User not found",
            examples={
                "application/json": {
                    "detail": "Not found."
                }
            }
        )
    },
    tags=['Admin - User Management']
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request, user_id):
    if not request.user.is_admin:
        return Response({"error": "Only admins can update users"}, status=status.HTTP_403_FORBIDDEN)

    user = get_object_or_404(User.objects.select_related(
        'wallet'), id=user_id, user_type__in=[UserType.DISTRIBUTOR, UserType.RETAILER])
    serializer = UpdateUserSerializer(user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "User updated successfully",
            "user": UserSerializer(user).data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='delete',
    operation_summary="Delete User (Admin Only)",
    operation_description="Permanently delete a distributor or retailer account",
    responses={
        200: openapi.Response(
            description="User deleted successfully",
            examples={
                "application/json": {
                    "message": "User deleted successfully"
                }
            }
        ),
        403: openapi.Response(
            description="Forbidden - Admin access required",
            examples={
                "application/json": {
                    "error": "Only admins can delete users"
                }
            }
        ),
        404: openapi.Response(
            description="User not found",
            examples={
                "application/json": {
                    "detail": "Not found."
                }
            }
        )
    },
    tags=['Admin - User Management']
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    if not request.user.is_admin:
        return Response({"error": "Only admins can delete users"}, status=status.HTTP_403_FORBIDDEN)

    user = get_object_or_404(User, id=user_id, user_type__in=[
                             UserType.DISTRIBUTOR, UserType.RETAILER])
    user.delete()
    return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    operation_summary="Reset User Password (Admin Only)",
    operation_description="Reset password for a distributor or retailer",
    request_body=PasswordResetSerializer,
    responses={
        200: openapi.Response(
            description="Password reset successfully",
            examples={
                "application/json": {
                    "message": "Password reset successfully",
                    "user": {
                        "id": 2,
                        "email": "distributor@example.com",
                        "username": "distributor@example.com",
                        "first_name": "John",
                        "last_name": "Distributor",
                        "phone": "+1234567891",
                        "user_type": 2,
                        "user_type_display": "Distributor",
                        "is_active": True,
                        "date_joined": "2024-01-15T10:30:00Z",
                        "wallet_balance": "1500.00",
                        "wallet_id": 1
                    }
                }
            }
        ),
        400: openapi.Response(
            description="Bad request - validation errors",
            examples={
                "application/json": {
                    "new_password": ["This password is too common."]
                }
            }
        ),
        403: openapi.Response(
            description="Forbidden - Admin access required",
            examples={
                "application/json": {
                    "error": "Only admins can reset passwords"
                }
            }
        ),
        404: openapi.Response(
            description="User not found",
            examples={
                "application/json": {
                    "detail": "Not found."
                }
            }
        )
    },
    tags=['Admin - User Management']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_user_password(request, user_id):
    if not request.user.is_admin:
        return Response({"error": "Only admins can reset passwords"}, status=status.HTTP_403_FORBIDDEN)

    user = get_object_or_404(User.objects.select_related(
        'wallet'), id=user_id, user_type__in=[UserType.DISTRIBUTOR, UserType.RETAILER])
    serializer = PasswordResetSerializer(data=request.data)

    if serializer.is_valid():
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return Response({
            "message": "Password reset successfully",
            "user": UserSerializer(user).data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# admin can search users


User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):

    if not request.user.is_admin:
        return Response({"error": "Only admins can search users"}, status=status.HTTP_403_FORBIDDEN)

    query = request.GET.get('q')
    if not query:
        return Response({"error": "Please provide a search query (?q=...)"}, status=status.HTTP_400_BAD_REQUEST)

    users = User.objects.select_related('wallet').filter(
        Q(email__icontains=query) |
        Q(phone__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query),

    )

    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['POST', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile_create_or_update(request):
    #  Allow only DISTRIBUTOR (2) and RETAILER (3)
    if not request.user.is_distributor and not request.user.is_retailer:
        return Response(
            {"error": "Only distributors and retailers can manage profiles"},
            status=status.HTTP_403_FORBIDDEN
        )

    profile = UserProfile.objects.filter(user=request.user).first()

    # Profile Creation
    if request.method == 'POST':
        if profile:
            return Response({"error": "Profile already exists"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                "message": "Profile created successfully",
                "profile": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Profile Update
    elif request.method in ['PUT', 'PATCH']:
        if not profile:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserProfileSerializer(
            profile, data=request.data, partial=(request.method == 'PATCH')
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profile updated successfully",
                "profile": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
