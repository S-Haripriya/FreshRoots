from django.contrib import admin

from .models import Product
from .models import FarmerProduct
admin.site.register(Product)
admin.site.register(FarmerProduct)
