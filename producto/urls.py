# urls.py
from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView
from . import views
urlpatterns = [
# CRUD CATEGORIA
    path('crear_categoria', views.crear_categoria, name='crear_categoria'),
    path('editar_categoria/<int:categoria_id>', views.editar_categoria, name='editar_categoria'),
    path('eliminar_categoria/<int:categoria_id>', views.eliminar_categoria, name='eliminar_categoria'),
    path('activar_categoria/<int:categoria_id>', views.activar_categoria, name='activar_categoria'),
    path('listar_categorias_activas', views.listar_categorias_activas, name='listar_categorias_activas'),
    path('listar_categorias', views.listar_categorias, name='listar_categorias'),
    path('obtener_categoria/<int:categoria_id>/', views.obtener_categoria_por_id, name='obtener_categoria_por_id'),
# CRUD SUBCATEGORIA
    path('crear_subcategoria', views.crear_subcategoria, name='crear_subcategoria'),
    path('editar_subcategoria/<int:subcategoria_id>', views.editar_subcategoria, name='editar_subcategoria'),
    path('eliminar_subcategoria/<int:subcategoria_id>', views.eliminar_subcategoria, name='eliminar_subcategoria'),
    path('activar_subcategoria/<int:subcategoria_id>', views.activar_subcategoria, name='activar_subcategoria'),
    path('listar_subcategorias_activas', views.listar_subcategorias_activas, name='listar_subcategorias_activas'),
    path('listar_subcategorias', views.listar_subcategorias, name='listar_subcategorias'),
    path('obtener_subcategoria/<int:subcategoria_id>/', views.obtener_subcategoria_por_id, name='obtener_subcategoria_por_id'),
# CRUD MARCA
    path('crear_marca', views.crear_marca, name='crear_marca'),
    path('editar_marca/<int:marca_id>', views.editar_marca, name='editar_marca'),
    path('eliminar_marca/<int:marca_id>', views.eliminar_marca, name='eliminar_marca'),
    path('activar_marca/<int:marca_id>', views.activar_marca, name='activar_marca'),
    path('listar_marcas_activas', views.listar_marcas_activas, name='listar_marcas_activas'),
    path('listar_marcas', views.listar_marcas, name='listar_marcas'),
    path('obtener_marca/<int:marca_id>/', views.obtener_marca_por_id, name='obtener_marca_por_id'),
# CRUD PRODUCTO
    path('crear_producto', views.crear_producto, name='crear_producto'),
    path('editar_producto/<int:producto_id>', views.editar_producto, name='editar_producto'),
    path('eliminar_producto/<int:producto_id>', views.eliminar_producto, name='eliminar_producto'),
    path('activar_producto/<int:producto_id>', views.activar_producto, name='activar_producto'),
    path('listar_productos_activos', views.listar_productos_activos, name='listar_productos_activas'),
    path('listar_productos', views.listar_productos, name='listar_productos'),
    path('obtener_producto/<int:producto_id>/', views.obtener_producto_por_id, name='obtener_producto_por_id'),
    path('buscar_productos', views.buscar_productos, name='buscar_productos'),
]