from django.urls import path
from . import views

urlpatterns = [
    path('buy-now/<int:listing_id>/', views.buy_now, name='buy_now'),
    path('confirm-payment/<int:order_id>/', views.confirm_payment, name='confirm_payment'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('purchase-history/', views.purchase_history, name='purchase_history'),
]