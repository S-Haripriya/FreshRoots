from django.contrib import admin
from .models import Order, OrderStatusUpdate, DeliveryPartner, SaleRecord


class OrderStatusUpdateInline(admin.TabularInline):
    model = OrderStatusUpdate
    extra = 1
    readonly_fields = ['updated_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'customer', 'farmer_product', 'quantity',
        'status', 'delivery_status', 'delivery_partner', 'created_at'
    ]
    list_filter = ['status', 'delivery_status', 'created_at']
    search_fields = ['customer__username', 'customer__email', 'farmer_product__product__name']
    inlines = [OrderStatusUpdateInline]

    fieldsets = (
        ('Order Info', {
            'fields': ('customer', 'farmer_product', 'quantity', 'price_per_unit', 'total_amount', 'delivery_address')
        }),
        ('Payment', {
            'fields': ('status',)
        }),
        ('Delivery', {
            'fields': ('delivery_status', 'delivery_partner', 'estimated_delivery_date', 'delivered_at')
        }),
    )
    readonly_fields = ['delivered_at']


@admin.register(DeliveryPartner)
class DeliveryPartnerAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'vehicle_number', 'is_approved']
    list_editable = ['is_approved']
    search_fields = ['user__username', 'phone_number']


@admin.register(SaleRecord)
class SaleRecordAdmin(admin.ModelAdmin):
    list_display = ['farmer_product', 'buyer', 'quantity', 'price_at_sale', 'sold_at']
    list_filter = ['sold_at']