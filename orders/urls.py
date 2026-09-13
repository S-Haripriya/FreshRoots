from django.urls import path
from . import views

urlpatterns = [
    path('buy-now/<int:listing_id>/', views.buy_now, name='buy_now'),
    path('confirm-payment/<int:order_id>/', views.confirm_payment, name='confirm_payment'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('purchase-history/', views.purchase_history, name='purchase_history'),

    path('my-orders/', views.farmer_orders, name='farmer_orders'),
    path('advance-delivery/<int:order_id>/', views.advance_delivery_status, name='advance_delivery_status'),

    path('delivery/register/', views.delivery_partner_register, name='delivery_partner_register'),
    path('delivery/dashboard/', views.delivery_dashboard, name='delivery_dashboard'),
    path('delivery/accept/<int:order_id>/', views.accept_delivery, name='accept_delivery'),
    path('delivery/mark-delivered/<int:order_id>/', views.mark_delivered, name='mark_delivered'),
]