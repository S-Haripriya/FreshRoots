from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from core.email_utils import send_notification_email
from .models import SaleRecord, Order, OrderStatusUpdate

LOW_STOCK_THRESHOLD = 5
@receiver(post_save, sender=SaleRecord)
def update_farmer_product_totals(sender, instance, created, **kwargs):
    if not created:
        return

    fp = instance.farmer_product
    fp.sold_quantity += instance.quantity
    fp.money_earned += instance.total_amount
    fp.save(update_fields=['sold_quantity', 'money_earned'])
    remaining = fp.quantity - fp.sold_quantity
    if remaining <= LOW_STOCK_THRESHOLD and not fp.low_stock_notified:

        farmer_user = fp.farm.user_profile.user

        send_notification_email(
            subject=f"Low stock alert: {fp.product.name}",
            message=(
                f"Hi {farmer_user.first_name or farmer_user.username},\n\n"
                f"Your listing for {fp.product.name} ({fp.farm.farm_name}) "
                f"is running low — only {remaining} kg remaining.\n\n"
                f"Consider restocking soon to avoid running out.\n\n"
                f"— The FreshRoots Team"
            ),
            recipient_email=farmer_user.email,
        )

        fp.low_stock_notified = True
        fp.save(update_fields=['low_stock_notified'])

@receiver(post_save, sender=Order)
def log_initial_order_status(sender, instance, created, **kwargs):
    if created:
        OrderStatusUpdate.objects.create(
            order=instance,
            status=instance.delivery_status,
            note="Order placed."
        )


@receiver(pre_save, sender=Order)
def log_delivery_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        previous = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    if previous.delivery_status != instance.delivery_status:

        OrderStatusUpdate.objects.create(
            order=instance,
            status=instance.delivery_status,
        )

        if instance.delivery_status == Order.DELIVERY_DELIVERED:
            instance.delivered_at = timezone.now()