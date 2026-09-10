from django.contrib import admin

from .models import SaleRecord
from .models import Order
admin.site.register(SaleRecord)
admin.site.register(Order)

