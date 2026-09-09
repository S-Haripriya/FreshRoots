from django.contrib import admin

from .models import Product
from .models import FarmerProduct
from .models import SaleRecord
admin.site.register(Product)
admin.site.register(FarmerProduct)
admin.site.register(SaleRecord)
