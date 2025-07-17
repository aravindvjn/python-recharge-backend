from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, OTP
from notifications.models import GlobalNotificationSetting,LowBalanceThreshold
from notifications.utils import notify_users_with_low_balance
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'phone', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'phone')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'phone', 'user_type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'user_type', 'password1', 'password2'),
        }),
    )

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('phone', 'code', 'created_at', 'expires_at', 'is_verified')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('phone', 'code')
    readonly_fields = ('created_at', 'expires_at')

@admin.register(GlobalNotificationSetting)
class GlobalNotificationSettingAdmin(admin.ModelAdmin):
    list_display = [
        'id',  # Add this to use as the display link
        'in_app', 'email', 'sms',
        'recharge_success', 'recharge_failed',
        'new_user_registered', 'low_balance', 'maintenance_scheduled',
        'updated_at',
    ]
    list_display_links = ['id']  # ✅ Use a non-editable field as the link

    list_editable = [
        'in_app', 'email', 'sms',
        'recharge_success', 'recharge_failed',
        'new_user_registered', 'low_balance', 'maintenance_scheduled',
    ]

@admin.register(LowBalanceThreshold)
class LowBalanceThresholdAdmin(admin.ModelAdmin):
    list_display = ['amount', 'updated_at']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # ✅ Call function after threshold is saved
        notify_users_with_low_balance()

admin.site.register(User, CustomUserAdmin)
