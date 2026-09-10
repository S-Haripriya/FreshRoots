
from django.db import models
from django.conf import settings
from django.db.models import Sum
from userprofile.models import GetCertified   # the verified farm


# =========================================================
# ADMIN-MANAGED CATALOG
# =========================================================

class Product(models.Model):
    """
    Master catalog entry. Only admin creates/edits/deletes these.
    Price here is the single source of truth for the whole site.
    """
    name = models.CharField(max_length=150, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    # ---- Aggregates for the admin dashboard ----

    @property
    def total_quantity_listed(self):
        """Total stock added across all farmers for this product."""
        return self.farmer_listings.aggregate(
            total=Sum('quantity')
        )['total'] or 0

    @property
    def total_quantity_sold(self):
        return self.farmer_listings.aggregate(
            total=Sum('sold_quantity')
        )['total'] or 0

    @property
    def total_earned(self):
        """Total money earned by ALL farmers selling this product."""
        return self.farmer_listings.aggregate(
            total=Sum('money_earned')
        )['total'] or 0


# =========================================================
# FARMER'S LISTING OF A PRODUCT
# =========================================================

class FarmerProduct(models.Model):
    """
    A farmer's own stock entry for an existing catalog Product.
    Price is NOT stored here — always pulled from product.price.
    sold_quantity / money_earned are cached counters, kept in sync
    via a signal whenever a SaleRecord is created (see signals.py).
    """
    farm = models.ForeignKey(
        GetCertified,
        on_delete=models.CASCADE,
        related_name='product_listings'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='farmer_listings'
    )
    image = models.ImageField(upload_to='farmer_products/', blank=True, null=True)

    quantity = models.PositiveIntegerField(default=0)          # total stock added
    sold_quantity = models.PositiveIntegerField(default=0)     # cached running total
    money_earned = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )                                                            # cached running total
    is_active = models.BooleanField(default=True)   # NEW
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('farm', 'product')  # one listing per farm per product

    def __str__(self):
        return f"{self.farm.farm_name} — {self.product.name}"

    @property
    def price(self):
        """Always reflects the current admin-set price."""
        return self.product.price

    @property
    def remaining(self):
        return self.quantity - self.sold_quantity

    @property
    def is_sold_out(self):
        return self.remaining <= 0


