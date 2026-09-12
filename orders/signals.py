from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import SaleRecord, Order, OrderStatusUpdate


@receiver(post_save, sender=SaleRecord)
def update_farmer_product_totals(sender, instance, created, **kwargs):
    if not created:
        return

    fp = instance.farmer_product
    fp.sold_quantity += instance.quantity
    fp.money_earned += instance.total_amount
    fp.save(update_fields=['sold_quantity', 'money_earned'])


@receiver(post_save, sender=Order)
def log_initial_order_status(sender, instance, created, **kwargs):
    """
    When an Order is first created, log its starting delivery
    status so the timeline always has a first entry.
    """
    if created:
        OrderStatusUpdate.objects.create(
            order=instance,
            status=instance.delivery_status,
            note="Order placed."
        )


@receiver(pre_save, sender=Order)
def log_delivery_status_change(sender, instance, **kwargs):
    """
    Whenever delivery_status changes on an existing order,
    automatically log it to the timeline and stamp
    delivered_at if it just became Delivered.
    """
    if not instance.pk:
        return   # new order — handled by post_save above

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