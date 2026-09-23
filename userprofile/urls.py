from django.urls import path

from . import views

urlpatterns = [
    path("profile/",views.account, name ="profile"),
    path("logout/",views.logout_view,name = "logout"),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
]