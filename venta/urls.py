# urls.py
from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView
from . import views
urlpatterns = [
# CRUD CATEGORIA
    path('añadir_producto_carrito', views.añadir_producto_carrito, name='añadir_producto_carrito'),
]