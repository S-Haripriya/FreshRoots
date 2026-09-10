# orders/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SaleRecord


@receiver(post_save, sender=SaleRecord)
def update_farmer_product_totals(sender, instance, created, **kwargs):
    if not created:
        return

    fp = instance.farmer_product
    fp.sold_quantity += instance.quantity
    fp.money_earned += instance.total_amount
    fp.save(update_fields=['sold_quantity', 'money_earned'])