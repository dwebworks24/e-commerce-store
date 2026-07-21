from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Order, Notification

@receiver(pre_save, sender=Order)
def store_old_order_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_status = Order.objects.get(pk=instance.pk).status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Order)
def order_status_updated_signal(sender, instance, created, **kwargs):
    old_status = getattr(instance, '_old_status', None)
    new_status = instance.status

    # Fire notification when the status updates (on creation or when changed)
    if created or (old_status and old_status != new_status):
        title = "Order Status Updated"
        message = f"Your order {instance.order_number} status has been updated to {new_status.capitalize()}."
        if created:
            message = f"Your order {instance.order_number} has been placed successfully."

        # 1. Create in-app Notification database entry (if it doesn't already exist)
        if not Notification.objects.filter(user=instance.user, title=title, message=message).exists():
            Notification.objects.create(
                user=instance.user,
                title=title,
                message=message
            )

        # 2. Send Expo Push Notification if user has a push token saved
        if hasattr(instance.user, 'expo_push_token') and instance.user.expo_push_token:
            from .utils import send_expo_push_notification
            try:
                send_expo_push_notification(
                    token=instance.user.expo_push_token,
                    title=title,
                    body=message,
                    data={
                        "order_id": str(instance.id),
                        "order_number": instance.order_number,
                        "status": new_status
                    }
                )
            except Exception as e:
                print(f"Error sending push notification: {e}")
