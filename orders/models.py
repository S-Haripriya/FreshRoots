
# orders/models.py

from django.db import models
from django.conf import settings
from products.models import FarmerProduct


class SaleRecord(models.Model):
    farmer_product = models.ForeignKey(
        FarmerProduct, on_delete=models.CASCADE, related_name='sales'
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='purchases'
    )
    quantity = models.PositiveIntegerField()
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)
    sold_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.farmer_product.product.name} on {self.sold_at:%Y-%m-%d}"

    @property
    def total_amount(self):
        return self.quantity * self.price_at_sale


class DeliveryPartner(models.Model):
        name = models.CharField(max_length=100)
        phone_number = models.CharField(max_length=15)
        vehicle_number = models.CharField(max_length=20, blank=True)

        def __str__(self):
            return self.name
    
class Order(models.Model):

    # ================= PAYMENT STATUS =================

    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    # ================= DELIVERY STATUS =================

    DELIVERY_PLACED = 'placed'
    DELIVERY_CONFIRMED = 'confirmed'
    DELIVERY_PACKED = 'packed'
    DELIVERY_SHIPPED = 'shipped'
    DELIVERY_OUT_FOR_DELIVERY = 'out_for_delivery'
    DELIVERY_DELIVERED = 'delivered'
    DELIVERY_CANCELLED = 'cancelled'
    DELIVERY_RETURNED = 'returned'

    DELIVERY_STATUS_CHOICES = [
        (DELIVERY_PLACED, 'Order Placed'),
        (DELIVERY_CONFIRMED, 'Confirmed'),
        (DELIVERY_PACKED, 'Packed'),
        (DELIVERY_SHIPPED, 'Shipped'),
        (DELIVERY_OUT_FOR_DELIVERY, 'Out for Delivery'),
        (DELIVERY_DELIVERED, 'Delivered'),
        (DELIVERY_CANCELLED, 'Cancelled'),
        (DELIVERY_RETURNED, 'Returned'),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders'
    )
    farmer_product = models.ForeignKey(
        FarmerProduct, on_delete=models.CASCADE, related_name='orders'
    )

    quantity = models.PositiveIntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_address = models.TextField()

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )

    delivery_status = models.CharField(
        max_length=20, choices=DELIVERY_STATUS_CHOICES, default=DELIVERY_PLACED
    )
    delivery_partner = models.ForeignKey(
        DeliveryPartner, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='orders'
    )
    estimated_delivery_date = models.DateField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} — {self.farmer_product.product.name}"


class OrderStatusUpdate(models.Model):
    """
    One row per delivery status change. This is what powers
    the tracking timeline shown to the customer.
    """
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='status_updates'
    )
    status = models.CharField(
        max_length=20, choices=Order.DELIVERY_STATUS_CHOICES
    )
    note = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['updated_at']

    def __str__(self):
        return f"{self.order} — {self.get_status_display()}"


    def __str__(self):
        return f"Order #{self.id} — {self.farmer_product.product.name}"

   