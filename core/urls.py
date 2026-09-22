from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/farm/approve/<int:farm_id>/', views.approve_farm, name='approve_farm'),
    path('admin-dashboard/farm/reject/<int:farm_id>/', views.reject_farm, name='reject_farm'),
    path('admin-dashboard/farm/revoke/<int:farm_id>/', views.revoke_farm, name='revoke_farm'),
    path('admin-dashboard/delivery/approve/<int:partner_id>/', views.approve_delivery_partner, name='approve_delivery_partner'),
    path('admin-dashboard/delivery/reject/<int:partner_id>/', views.reject_delivery_partner, name='reject_delivery_partner'),
    path('admin-dashboard/delivery/revoke/<int:partner_id>/', views.revoke_delivery_partner, name='revoke_delivery_partner'),
    path('admin-dashboard/products/', views.manage_products, name='manage_products'),
    path('admin-dashboard/products/add/', views.add_product, name='add_product'),
    path('admin-dashboard/products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('admin-dashboard/products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('admin-dashboard/orders/', views.order_overview, name='order_overview'),
]