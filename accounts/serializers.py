from .models import UserProfile
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, OTP, UserType, UserProfile
import re


class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'phone', 'first_name', 'last_name',
                  'password', 'password_confirm', 'user_type']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'phone': {'required': True},
        }

    def validate_phone(self, value):

        # Normalize by removing spaces
        normalized_value = value.replace(" ", "")

        # Match +91 followed by 10 digits starting with 6-9
        pattern = r'^\+91[6-9]\d{9}$'
        if not re.match(pattern, normalized_value):
            raise serializers.ValidationError(
                "Phone number must be a valid 10-digit Indian number prefixed with +91 (with or without space)."
            )

        # Check uniqueness manually
        if User.objects.filter(phone=normalized_value).exists():
            raise serializers.ValidationError(
                "User with this phone already exists.")

        return normalized_value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        # Set username same as email
        validated_data['username'] = validated_data['email']

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class OTPGenerateSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

    def validate_phone(self, value):
        # Remove any non-digit characters from phone number
        cleaned_phone = ''.join(filter(str.isdigit, value))

        if len(cleaned_phone) < 10:
            raise serializers.ValidationError("Invalid phone number format")

        return value

    def create(self, validated_data):
        phone = validated_data['phone']

        # Check if user exists with the phone number
        if not User.objects.filter(phone=phone).exists():
            # Generate dummy email using phone number
            dummy_email = f"{phone}@example.com"

            # Create new user
            user = User.objects.create(
                phone=phone,
                email=dummy_email,
                username=phone,  # Using phone as username
                user_type=UserType.CLIENT
            )
            # Set a default unusable password
            user.set_unusable_password()
            user.save()

        return validated_data


class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            otp = OTP.objects.filter(
                phone=attrs['phone'],
                code=attrs['code']
            ).latest('created_at')

            if not otp.is_valid():
                raise serializers.ValidationError("Invalid or expired OTP")

        except OTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP")

        return attrs


class UserSerializer(serializers.ModelSerializer):
    user_type_display = serializers.CharField(
        source='get_user_type_display', read_only=True)
    wallet_balance = serializers.SerializerMethodField()
    wallet_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'phone', 'user_type',
                  'user_type_display', 'is_active', 'date_joined', 'wallet_balance', 'wallet_id']
        read_only_fields = ['id', 'date_joined', 'wallet_balance', 'wallet_id']

    def get_wallet_balance(self, obj):
        try:
            return str(obj.wallet.balance)
        except:
            return "0.00"

    def get_wallet_id(self, obj):
        try:
            return obj.wallet.id
        except:
            return None


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    full_name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'phone', 'full_name',
                  'user_type', 'password', 'password_confirm']
        extra_kwargs = {
            'email': {'required': True},
            'phone': {'required': True},
        }

    def validate_user_type(self, value):
        if value not in [UserType.DISTRIBUTOR, UserType.RETAILER]:
            raise serializers.ValidationError(
                "Can only create distributors and retailers")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        from wallet.models import Wallet

        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        # Handle full_name splitting
        full_name = validated_data.pop('full_name', '').strip()
        parts = full_name.split()
        first_name = parts[0] if parts else ''
        last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
        validated_data['first_name'] = first_name
        validated_data['last_name'] = last_name

        # Set username same as email if not provided
        if not validated_data.get('username'):
            validated_data['username'] = validated_data['email']

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Create wallet for distributor and retailer
        if user.user_type in [UserType.DISTRIBUTOR, UserType.RETAILER]:
            Wallet.objects.create(user=user)

        return user


class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name',
                  'last_name', 'phone', 'user_type', 'is_active']
        extra_kwargs = {
            'email': {'required': False},
            'username': {'required': False},
        }

    def validate_user_type(self, value):
        if value not in [UserType.DISTRIBUTOR, UserType.RETAILER]:
            raise serializers.ValidationError(
                "Can only update distributors and retailers")
        return value


class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(validators=[validate_password])
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'user',
            'full_name',
            'email',
            'phone',
            'bio',
            'address',  # billing_address
        ]
        read_only_fields = ['user', 'email', 'phone', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()
