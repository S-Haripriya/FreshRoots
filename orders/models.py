from django.db import models
from django.conf import settings
from products.models import FarmerProduct


class DeliveryPartner(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delivery_partner_profile'
    )
    phone_number = models.CharField(max_length=15)
    vehicle_number = models.CharField(max_length=20, blank=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


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


class Order(models.Model):

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
    # Add inside Order, alongside your other fields
    cart_checkout_id = models.CharField(max_length=64, blank=True, db_index=True)
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


class Cart(models.Model):
    customer = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart — {self.customer.username}"

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    farmer_product = models.ForeignKey(FarmerProduct, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'farmer_product')

    def __str__(self):
        return f"{self.quantity} x {self.farmer_product.product.name}"

    @property
    def subtotal(self):
        return self.quantity * self.farmer_product.price