from django.shortcuts import render
from decimal import Decimal
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

from decimal import Decimal
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from django.db import transaction

@api_view(['POST'])
@swagger_auto_schema(operation_description="Añadir producto al carrito de compras")
# @requiere_permiso("DetalleCarrito", "actualizar")
def agregar_producto_carrito(request):
    usuario = request.user
    producto_id = request.data.get('producto_id')
    cantidad = int(request.data.get('cantidad', 1))

    # Obtener producto o devolver 404
    producto = get_object_or_404(ProductoModel, id=producto_id)
    precio_unitario = Decimal(producto.precio_contado)

    # Verificar stock
    if cantidad > producto.stock:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Cantidad solicitada excede el stock disponible",
            "values": {}
        })

    # Obtener o crear carrito
    carrito, created = CarritoModel.objects.get_or_create(usuario=usuario, is_active=True)

    # Calcular subtotal
    subtotal = precio_unitario * Decimal(cantidad)

    # Obtener detalle del carrito
    detalle_carrito = DetalleCarritoModel.objects.filter(
        carrito=carrito,
        producto=producto
    ).first()

    if detalle_carrito:
        if producto.stock < detalle_carrito.cantidad + cantidad:
            return Response({
                "status": 0,
                "error": 1,
                "message": "Cantidad solicitada excede el stock disponible",
                "values": {}
            })
        # Actualizar cantidad y subtotal
        detalle_carrito.cantidad += cantidad
        detalle_carrito.subtotal += subtotal
        detalle_carrito.save()
        serializer = DetalleCarritoSerializer(detalle_carrito)
    else:
        # Crear nuevo detalle
        serializer = DetalleCarritoSerializer(data={
            'carrito': carrito.id,
            'producto': producto.id,
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'subtotal': subtotal,
        })
        if serializer.is_valid():
            serializer.save()
        else:
            return Response({
                "status": 0,
                "error": 1,
                "message": "Error al añadir producto al carrito",
                "values": serializer.errors
            })

    # Actualizar total del carrito
    carrito.total = Decimal(carrito.total) + Decimal(subtotal)
    carrito.save()

    return Response({
        "status": 1,
        "error": 0,
        "message": "Producto añadido al carrito con éxito",
        "values": {"detalle": serializer.data}
    })

@api_view(['PATCH'])
@swagger_auto_schema(operation_description="Añadir producto al carrito de compras")
# @requiere_permiso("Carrito", "actualizar")
def vaciar_carrito(request):
    usuario = request.user

    try:
        carrito = CarritoModel.objects.get(usuario=usuario, is_active=True)
    except CarritoModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "No se encontró un carrito activo para este usuario",
            "values": {}
        })

    # Obtener todos los detalles del carrito
    detalles_carrito = DetalleCarritoModel.objects.filter(carrito=carrito)

    # Eliminar todos los detalles
    detalles_carrito.delete()

    # Reiniciar el total del carrito
    carrito.total = 0
    carrito.save()

    return Response({
        "status": 1,
        "error": 0,
        "message": "Carrito vaciado con éxito",
        "values": {"total": carrito.total, "cantidad_productos": 0}
    })

@api_view(['PATCH'])
@swagger_auto_schema(operation_description="Eliminar una cantidad de un producto del carrito")
# @requiere_permiso("Carrito", "actualizar")
def eliminar_producto_carrito(request):
    usuario = request.user
    producto_id = request.data.get('producto_id')
    cantidad_a_eliminar = int(request.data.get('cantidad', -1))

    # Obtener carrito activo
    try:
        carrito = CarritoModel.objects.get(usuario=usuario, is_active=True)
    except CarritoModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "No se encontró un carrito activo",
            "values": {}
        })

    # Obtener detalle del producto en el carrito
    detalle = DetalleCarritoModel.objects.filter(carrito=carrito, producto_id=producto_id).first()
    if not detalle:
        return Response({
            "status": 0,
            "error": 1,
            "message": "El producto no está en el carrito",
            "values": {}
        })
    if cantidad_a_eliminar == -1 :
        cantidad_a_eliminar = detalle.cantidad
    # Calcular cuánto se va a restar del subtotal
    precio_unitario = Decimal(detalle.precio_unitario)
    cantidad_a_eliminar = min(cantidad_a_eliminar, detalle.cantidad)
    subtotal_a_restar = precio_unitario * Decimal(cantidad_a_eliminar)

    # Actualizar detalle
    detalle.cantidad -= cantidad_a_eliminar
    detalle.subtotal -= subtotal_a_restar
    if detalle.cantidad <= 0:
        detalle.delete()
    else:
        detalle.save()

    # Actualizar total del carrito
    carrito.total -= subtotal_a_restar
    if carrito.total < 0:
        carrito.total = 0
    carrito.save()

    return Response({
        "status": 1,
        "error": 0,
        "message": "Producto actualizado/eliminado del carrito con éxito",
        "values": {
            "producto_id": producto_id,
            "cantidad_restante": detalle.cantidad if detalle.id else 0,
            "total_carrito": carrito.total
        }
    })


@api_view(['POST'])
@swagger_auto_schema(operation_description="Generar un pedido a partir del carrito del usuario")
@requiere_permiso("Pedido", "crear")
def generar_pedido(request):
    usuario = request.user

    try:
        carrito = CarritoModel.objects.get(usuario=usuario, is_active=True)
    except CarritoModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "No se encontró un carrito activo",
            "values": {}
        })

    detalles_carrito = DetalleCarritoModel.objects.filter(carrito=carrito)
    if not detalles_carrito.exists():
        return Response({
            "status": 0,
            "error": 1,
            "message": "El carrito está vacío",
            "values": {}
        })

    try:
        with transaction.atomic():
            # 1. Crear pedido
            pedido = PedidoModel.objects.create(
                usuario=usuario,
                total=carrito.total,
                estado='pendiente'  # o como tengas definido
            )

            # 2. Copiar detalles del carrito al pedido
            for detalle in detalles_carrito:
                if detalle.cantidad > detalle.producto.stock:
                    raise Exception(f"Stock insuficiente para {detalle.producto.nombre}")

                DetallePedidoModel.objects.create(
                    pedido=pedido,
                    producto=detalle.producto,
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.precio_unitario,
                    subtotal=detalle.subtotal
                )

                # 3. Restar stock del producto
                detalle.producto.stock -= detalle.cantidad
                detalle.producto.save()

            # 4. Vaciar carrito
            detalles_carrito.delete()
            carrito.total = Decimal('0.00')
            carrito.is_active = False
            carrito.save()

    except Exception as e:
        return Response({
            "status": 0,
            "error": 1,
            "message": f"Error al generar el pedido: {str(e)}",
            "values": {}
        })

    return Response({
        "status": 1,
        "error": 0,
        "message": "Pedido generado con éxito",
        "values": {
            "pedido_id": pedido.id,
            "total": pedido.total,
            "cantidad_productos": detalles_carrito.count()
        }
    })

    
# --------------------- Crear Categoria ---------------------
# @swagger_auto_schema(
#     method="post",
#     request_body=FormaPagoSerializer,
#     responses={201: FormaPagoSerializer} 
# )
# @api_view(['POST'])
# @requiere_permiso("Categoria", "crear")
# def crear_categoria(request):
#     serializer = FormaPagoSerializer(data=request.data)
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

@swagger_auto_schema(
    method="post",
    request_body=FormaPagoSerializer,
    responses={201: FormaPagoSerializer} 
)
@api_view(['POST'])
@requiere_permiso("Forma Pago", "crear")
def crear_forma_pago(request):
    serializer = FormaPagoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Forma Pago creada correctamente",
            "values": {"Forma Pago": serializer.data}
        })
    return Response({
        "status": 0,
        "error": 1,
        "message": "Error al crear Forma Pago",
        "values": serializer.errors
    })

@swagger_auto_schema(
    method="patch",
    request_body=FormaPagoSerializer,
    responses={200: FormaPagoSerializer} 
)
@api_view(['PATCH'])
@requiere_permiso("Forma Pago", "actualizar")
def editar_forma_pago(request, forma_pago_id):
    try:
        forma_pago = FormaPagoModel.objects.get(id=forma_pago_id)
    except FormaPagoModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Forma Pago no encontrada",
            "values": {}
        })

    serializer = FormaPagoSerializer(forma_pago, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Forma Pago editada correctamente",
            "values": {"Forma Pago": serializer.data}
        })
    return Response({
        "status": 0,
        "error": 1,
        "message": "Error al editar Forma Pago",
        "values": serializer.errors
    })

# --------------------- Eliminar ( desactivar ) Forma Pago ---------------------
@api_view(['DELETE'])
@requiere_permiso("Forma Pago", "eliminar")
def eliminar_forma_pago(request, forma_pago_id):
    try:
        forma_pago = FormaPagoModel.objects.get(id=forma_pago_id)
        forma_pago.is_active = False
        forma_pago.save()
    except FormaPagoModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Forma Pago no encontrada",
            "values": {}
        })

    return Response({
        "status": 1,
        "error": 0,
        "message": "Forma Pago eliminada correctamente",
        "values": {}
    })

# --------------------- Activar Formas Pago ---------------------
@api_view(['PATCH'])
@requiere_permiso("Forma Pago", "activar")
def activar_forma_pago(request, forma_pago_id):
    try:
        forma_pago = FormaPagoModel.objects.get(id=forma_pago_id)
        forma_pago.is_active = True
        forma_pago.save()
    except FormaPagoModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Forma Pago no encontrada",
            "values": {}
        })

    return Response({
        "status": 1,
        "error": 0,
        "message": "Forma Pago activada correctamente",
        "values": {}
    })

# --------------------- Listar Formas Pago ( ACTIVAS )---------------------
@api_view(['GET'])
@requiere_permiso("Forma Pago", "leer")
def listar_formas_pago_activos(request):
    formas_pago = FormaPagoModel.objects.filter(is_active=True)
    serializer = FormaPagoSerializer(formas_pago, many=True)
    return Response({
        "status": 1,
        "error": 0,
        "message": "Formas Pago obtenidas correctamente",
        "values": {"Formas Pago": serializer.data}
    })

# --------------------- Listar Todas las Formas Pago ---------------------
@api_view(['GET'])
@requiere_permiso("Forma Pago", "leer")
def listar_formas_pago(request):
    formas_pago = FormaPagoModel.objects.all()
    serializer = FormaPagoSerializer(formas_pago, many=True)
    return Response({
        "status": 1,
        "error": 0,
        "message": "Formas Pago obtenidas correctamente",
        "values": {"Formas Pago": serializer.data}
    })

# ---------------------- Listar Formas Pago por ID ----------------------
@api_view(['GET'])
@requiere_permiso("Forma Pago", "leer")
def obtener_forma_pago_por_id(request, forma_pago_id):
    try:
        forma_pago = FormaPagoModel.objects.get(id=forma_pago_id)
    except FormaPagoModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Forma Pago no encontrada",
            "values": {}
        })

    serializer = FormaPagoSerializer(forma_pago)
    return Response({
        "status": 1,
        "error": 0,
        "message": "Forma Pago obtenida correctamente",
        "values": {"Forma Pago": serializer.data}
    })