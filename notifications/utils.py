from django.utils import timezone
from purchases.models import PlanPurchase
from support.models import Support
from notifications.models import Notification
from django.contrib.auth import get_user_model
from notifications.models import LowBalanceThreshold,GlobalNotificationSetting


def generate_notification_content(user, notification_type, related_id=None):
    NOTIFICATION_TYPES = {
        'RECHARGE', 'SUPPORT', 'PROMOTION', 'ACCOUNT', 'OTHER','USER_REGISTERED','LOW_BALANCE'
    }

    if notification_type not in NOTIFICATION_TYPES:
        raise ValueError(f"Invalid notification type: {notification_type}")

    name = getattr(user, 'first_name', user.email.split('@')[0])

    if notification_type == 'RECHARGE':
        try:
            purchase = PlanPurchase.objects.get(id=related_id, user=user) if related_id else None
            plan_title = purchase.plan.title if purchase else 'Unknown Plan'
            title = f"Recharge Successful for {plan_title}"
            message = (
                f"Hi {name},\n\n"
                f"Your recharge for {plan_title} has been successfully processed "
                f"on {timezone.now().strftime('%Y-%m-%d')}.\n"
                f"Phone Number: {purchase.phone_number if purchase else 'N/A'}.\n"
                f"Amount: ₹{purchase.amount if purchase else 'N/A'}.\n"
                f"Enjoy your plan!"
            )
        except PlanPurchase.DoesNotExist:
            title = "Recharge Notification"
            message = f"Hi {name},\n\nWe attempted to process your recharge, but something went wrong. Please contact support."

    elif notification_type == 'SUPPORT':
        try:
            ticket = Support.objects.get(id=related_id, user=user) if related_id else None
            title = f"Support Ticket #{related_id or 'New'} Update"
            message = (
                f"Hi {name},\n\n"
                f"Your support ticket (Issue: {ticket.issue_type if ticket else 'N/A'}) "
                f"has been updated.\n"
                f"Status: {ticket.status if ticket else 'N/A'}.\n"
                f"Please check your account for details or contact us for assistance."
            )
        except Support.DoesNotExist:
            title = "Support Ticket Update"
            message = f"Hi {name},\n\nWe couldn’t find your support ticket. Please contact us for assistance."

    elif notification_type == 'USER_REGISTERED':
        title = "Welcome to Our Platform!"
        message = (
        f"Hi {name},\n\n"
        "Thank you for registering with us. We're excited to have you on board!\n"
        "You can now access your account and explore all the available features.\n\n"
        "If you need any help, feel free to contact our support team.\n\n"
        "Best regards,\n"
        "The Team"
    )
    
    elif notification_type == 'PROMOTION':
        title = "Exclusive Offer Just for You!"
        message = (
            f"Hi {name},\n\n"
            f"Unlock a special offer on your next recharge! "
            f"Get 10% extra data on any plan above ₹299. "
            f"Hurry, this offer is valid until {timezone.now().strftime('%Y-%m-%d')}!"
        )

    elif notification_type == 'ACCOUNT':
        title = "Account Update"
        message = (
            f"Hi {name},\n\n"
            f"We’ve made some updates to your account. "
            f"Please log in to review your details or contact support if you have questions."
        )

    elif notification_type == 'LOW_BALANCE':
        title = "Low Wallet Balance Alert"
        message = (
            f"Hi {name},\n\n"
            f"Your wallet balance is below the required limit (₹{user.wallet.balance}). "
            "Please recharge soon to continue operations without issues.\n\n"
            "Regards,\nSupport Team"
            )

    else:  # OTHER
        title = "Important Update"
        message = (
            f"Hi {name},\n\n"
            f"We have an important update for you. "
            f"Please check your account or contact support for more information."
        )


    return {'title': title, 'message': message}

def is_notification_allowed(notification_type: str, channel: str = 'in_app') -> bool:
    from notifications.models import GlobalNotificationSetting
    settings = GlobalNotificationSetting.objects.first()
    
    if not settings:
        return False  # Default to blocking if no settings

    type_enabled = getattr(settings, notification_type.lower(), False)
    channel_enabled = getattr(settings, channel.lower(), False)

    return type_enabled and channel_enabled


User = get_user_model()
def notify_users_with_low_balance():
    try:
        threshold = LowBalanceThreshold.objects.last()
        setting = GlobalNotificationSetting.objects.last()  # ✅ No user field used

        if not threshold or not setting:
            return

        if not (setting.in_app and setting.low_balance):
            return  # ✅ Global toggle is OFF, skip sending

        low_balance_users = User.objects.filter(
            user_type__in=[2, 3],  # Assuming 2 = RETAILER, 3 = DISTRIBUTOR
            wallet__balance__lt=threshold.amount
        )

        for user in low_balance_users:
            data = generate_notification_content(user, 'LOW_BALANCE')
            Notification.objects.create(
                user=user,
                title=data['title'],
                message=data['message'],
                notification_type='LOW_BALANCE'
            )

    except Exception as e:
        print(" Error while sending low balance notifications:", e)

