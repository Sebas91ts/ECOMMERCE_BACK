# urls.py
from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView
from . import views
urlpatterns = [
# CRUD CARRITO_COMPRA
    path('agregar_producto_carrito', views.agregar_producto_carrito, name='agregar_producto_carrito'),
    path('vaciar_carrito', views.vaciar_carrito, name='vaciar_carrito'),
    path('eliminar_producto_carrito', views.eliminar_producto_carrito, name='eliminar_producto_carrito'),
    path('generar_pedido',views.generar_pedido, name='generar_pedido'),

# CRUD FORMAS DE PAGO
    path('crear_forma_pago', views.crear_forma_pago, name='crear_forma_pago'),
    path('editar_forma_pago/<int:forma_pago_id>', views.editar_forma_pago, name='editar_forma_pago'),
    path('eliminar_forma_pago/<int:forma_pago_id>', views.eliminar_forma_pago, name='eliminar_forma_pago'),
    path('activar_forma_pago/<int:forma_pago_id>', views.activar_forma_pago, name='activar_forma_pago'),
    path('listar_formas_pago', views.listar_formas_pago, name='listar_formas_pago'),
    path('listar_formas_pago_activos', views.listar_formas_pago_activos, name='listar_formas_pago_activos'),
    path('obtener_forma_pago/<int:forma_pago_id>/', views.obtener_forma_pago_por_id, name='obtener_forma_pago'),



]