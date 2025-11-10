# urls.py
from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import views_stripe
urlpatterns = [
# CRUD CARRITO_COMPRA
    path('agregar_producto_carrito', views.agregar_producto_carrito, name='agregar_producto_carrito'),
    path('vaciar_carrito', views.vaciar_carrito, name='vaciar_carrito'),
    path('eliminar_producto_carrito', views.eliminar_producto_carrito, name='eliminar_producto_carrito'),
    path('generar_pedido',views.generar_pedido, name='generar_pedido'),
    path('obtener_mi_carrito', views.obtener_mi_carrito, name='obtener_mi_carrito'),

# CRUD FORMAS DE PAGO
    path('crear_forma_pago', views.crear_forma_pago, name='crear_forma_pago'),
    path('editar_forma_pago/<int:forma_pago_id>', views.editar_forma_pago, name='editar_forma_pago'),
    path('eliminar_forma_pago/<int:forma_pago_id>', views.eliminar_forma_pago, name='eliminar_forma_pago'),
    path('activar_forma_pago/<int:forma_pago_id>', views.activar_forma_pago, name='activar_forma_pago'),
    path('listar_formas_pago', views.listar_formas_pago, name='listar_formas_pago'),
    path('listar_formas_pago_activos', views.listar_formas_pago_activos, name='listar_formas_pago_activos'),
    path('obtener_forma_pago/<int:forma_pago_id>/', views.obtener_forma_pago_por_id, name='obtener_forma_pago'),
    path('listar_formas_pago_activas_usuario', views.listar_formas_pago_activas_usuario, name='listar_formas_pago_activas_usuario'),

# CRUD PEDIDOS Y CARRITO
    # PARA EL USUARIO
    path('listar_mis_pedidos', views.listar_mis_pedidos, name='listar_mis_pedidos'),
    # PARA ADMINISTRADOR
    path('listar_pedidos', views.listar_pedidos, name='listar_pedidos'),
    # path('listar_pedidos_por_id_usuario/<int:usuario_id>', views.listar_pedidos_por_id_usuario, name='listar_pedidos_por_id_usuario'),
    #GENERAL
    path('obtener_pedido/<int:pedido_id>/', views.obtener_pedido, name='obtener_pedido'),
    #STRIPE
    # path('stripe/crear-sesion', views_stripe.crear_sesion_pago_stripe, name='crear_sesion_stripe'),
    # path('stripe/webhook', views_stripe.webhook_stripe, name='webhook_stripe'),
    # path('stripe/verificar-pago/<str:session_id>', views_stripe.verificar_pago_stripe, name='verificar_pago_stripe'),
]