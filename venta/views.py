from django.shortcuts import render
# from utils.encrypted_logger import registrar_accion
from comercio.permissions import requiere_permiso 
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
# from .serializers import 
from producto.models import ProductoModel
from .models import CarritoModel, DetalleCarritoModel, FormaPagoModel, PedidoModel, DetallePedidoModel
from .serializers import CarritoSerializer, DetalleCarritoSerializer, FormaPagoSerializer, PedidoSerializer, DetallePedidoSerializer
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q

# Create your views here.

@api_view(['POST'])
@swagger_auto_schema(operation_description="Añadir producto al carrito de compras")
def añadir_producto_carrito(request):
    usuario = request.user
    producto_id = request.data.get('producto_id')
    producto = ProductoModel.objects.get(id=producto_id)
    if not producto :
        return Response({
            "status": 0,
            "error": 1,
            "message": "El producto con ese id no existe",
            "values": {}
        })
    cantidad = request.data.get('cantidad', 1)
    if cantidad > producto.stock:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Cantidad solicitada excede el stock disponible",
            "values": {}
        })
    carrito = CarritoModel.objects.filter(usuario=usuario, is_active=True).first()
    if not carrito:
        carrito = CarritoModel.objects.create(usuario=usuario)

    # Añadir producto al carrito
    serializer = DetalleCarritoSerializer(data={
        'carrito': carrito.id,
        'producto': producto,
        'cantidad': cantidad
    })
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Producto añadido al carrito con éxito",
            "values": {"detalle": serializer.data}
        })
    return Response({
        "status": 0,
        "error": 1,
        "message": "Error al añadir producto al carrito",
        "values": serializer.errors
    })

# --------------------- Crear Categoria ---------------------
# @swagger_auto_schema(
#     method="post",
#     request_body=CategoriaSerializer,
#     responses={201: CategoriaSerializer} 
# )
# @api_view(['POST'])
# @requiere_permiso("Categoria", "crear")
# def crear_categoria(request):
#     serializer = CategoriaSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response({
#             "status": 1,
#             "error": 0,
#             "message": "Categoria creada correctamente",
#             "values": {"categoria": serializer.data}
#         })
#     return Response({
#         "status": 0,
#         "error": 1,
#         "message": "Error al crear Categoría",
#         "values": serializer.errors
#     })
