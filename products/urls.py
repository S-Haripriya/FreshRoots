from django.urls import path
from . import views

urlpatterns = [
    path('my-products/', views.my_products, name='my_products'),
path('remove-product/<int:listing_id>/', views.remove_farmer_product, name='remove_farmer_product'),
]
