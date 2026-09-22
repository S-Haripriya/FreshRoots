from django.urls import path
from . import views

urlpatterns = [
    path('buy-now/<int:listing_id>/', views.buy_now, name='buy_now'),
    path('confirm-payment/<str:checkout_id>/', views.confirm_payment, name='confirm_payment'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('purchase-history/', views.purchase_history, name='purchase_history'),

    path('my-orders/', views.farmer_orders, name='farmer_orders'),
    path('advance-delivery/<int:order_id>/', views.advance_delivery_status, name='advance_delivery_status'),

    path('delivery/register/', views.delivery_partner_register, name='delivery_partner_register'),
    path('delivery/dashboard/', views.delivery_dashboard, name='delivery_dashboard'),
    path('delivery/accept/<int:order_id>/', views.accept_delivery, name='accept_delivery'),
    path('delivery/mark-delivered/<int:order_id>/', views.mark_delivered, name='mark_delivered'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:listing_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('cart/checkout/', views.checkout_cart, name='checkout_cart'),
    path('cart/confirm-payment/<str:checkout_id>/', views.confirm_cart_payment, name='confirm_cart_payment'),
    path('cart/order-success/<str:checkout_id>/', views.cart_order_success, name='cart_order_success'),
    path('cancel-paid-order/<int:order_id>/', views.cancel_paid_order, name='cancel_paid_order'),
]