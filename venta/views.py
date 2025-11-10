import datetime
from django.shortcuts import render
from decimal import Decimal
from dateutil.relativedelta import relativedelta
# from utils.encrypted_logger import registrar_accion
from comercio.permissions import requiere_permiso 
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
# from .serializers import 
from producto.models import ProductoModel
from .models import CarritoModel, DetalleCarritoModel, FormaPagoModel, PedidoModel, DetallePedidoModel, PlanPagoModel
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

@api_view(['DELETE'])
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
def eliminar_producto_carrito(request):
    try:
        usuario = request.user
        data = request.data
        
        print("📥 Datos recibidos RAW:", data)
        
        # Obtener producto_id
        producto_id = data.get('producto_id')
        
        if isinstance(producto_id, dict):
            print("⚠️  producto_id llegó como dict, extrayendo valor...")
            producto_id = producto_id.get('producto_id') or producto_id.get('id')
        
        # Convertir a entero
        try:
            producto_id = int(producto_id)
        except (TypeError, ValueError):
            return Response({
                "status": 0,
                "error": 1,
                "message": "producto_id debe ser un número válido",
                "values": {}
            }, status=400)
        
        # 🔥 CORRECCIÓN: Manejar correctamente la cantidad
        cantidad_a_eliminar = data.get('cantidad', -1)
        print(f"🔧 cantidad recibida: {cantidad_a_eliminar}, tipo: {type(cantidad_a_eliminar)}")
        
        # Si es -1, eliminar todo el producto
        if cantidad_a_eliminar == -1:
            cantidad_a_eliminar = None  # Indicar que se elimine todo
        else:
            try:
                cantidad_a_eliminar = int(cantidad_a_eliminar)
                # Asegurar que sea positivo
                if cantidad_a_eliminar < 0:
                    cantidad_a_eliminar = 1  # Por defecto 1 si es negativo
            except (TypeError, ValueError):
                cantidad_a_eliminar = 1  # Por defecto 1

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
        
        # 🔥 CORRECCIÓN: Manejar eliminación completa vs parcial
        if cantidad_a_eliminar is None:
            # Eliminar todo el producto
            cantidad_eliminada = detalle.cantidad
            subtotal_a_restar = detalle.subtotal
            detalle.delete()
            cantidad_restante = 0
            message = "Producto eliminado del carrito"
        else:
            # Eliminar cantidad específica
            cantidad_eliminada = min(cantidad_a_eliminar, detalle.cantidad)
            precio_unitario = Decimal(detalle.precio_unitario)
            subtotal_a_restar = precio_unitario * Decimal(cantidad_eliminada)
            
            detalle.cantidad -= cantidad_eliminada
            detalle.subtotal -= subtotal_a_restar
            
            if detalle.cantidad <= 0:
                detalle.delete()
                cantidad_restante = 0
                message = "Producto eliminado del carrito"
            else:
                detalle.save()
                cantidad_restante = detalle.cantidad
                message = f"Se eliminaron {cantidad_eliminada} unidades, restan {cantidad_restante}"

        print(f"🔧 Eliminando {cantidad_eliminada} unidades de {detalle.cantidad + cantidad_eliminada} totales")

        # Actualizar total del carrito
        carrito.total = max(0, carrito.total - subtotal_a_restar)
        carrito.save()

        return Response({
            "status": 1,
            "error": 0,
            "message": message,
            "values": {
                "producto_id": producto_id,
                "cantidad_restante": cantidad_restante,
                "total_carrito": float(carrito.total)
            }
        })
        
    except Exception as e:
        print("❌ Error en eliminar_producto_carrito:", str(e))
        import traceback
        traceback.print_exc()
        return Response({
            "status": 0,
            "error": 1,
            "message": f"Error interno del servidor: {str(e)}",
            "values": {}
        }, status=500)

@api_view(['POST'])
@swagger_auto_schema(operation_description="Generar pedido a partir del carrito del usuario")
def generar_pedido(request):
    usuario = request.user
    print("📥 Datos recibidos RAW:", request.data)
    forma_pago_id = request.data.get('forma_pago')
    meses_credito = request.data.get('meses_credito', None)

    try:
        # 1️⃣ Verificar carrito activo
        carrito = CarritoModel.objects.filter(usuario=usuario, is_active=True).first()
        if not carrito or not carrito.carrito_detalles.exists():
            return Response({
                "status": 0,
                "error": 1,
                "message": "El carrito está vacío o no existe",
                "values": {}
            }, status=400)

        # 2️⃣ Obtener forma de pago
        forma_pago = FormaPagoModel.objects.filter(id=forma_pago_id, is_active=True).first()
        if not forma_pago:
            return Response({
                "status": 0,
                "error": 1,
                "message": "La forma de pago especificada no existe o no está disponible",
                "values": {}
            }, status=400)

        # 3️⃣ Validar meses de crédito si es necesario
        if forma_pago.nombre.lower() == "credito":
            if not meses_credito:
                return Response({
                    "status": 0,
                    "error": 1,
                    "message": "Debe especificar la cantidad de meses para el crédito",
                    "values": {}
                }, status=400)
            try:
                meses_credito = int(meses_credito)
                if meses_credito not in [6, 12, 18, 24]:
                    return Response({
                        "status": 0,
                        "error": 1,
                        "message": "Los meses de crédito deben ser 6, 12, 18 o 24",
                        "values": {}
                    }, status=400)
            except (ValueError, TypeError):
                return Response({
                    "status": 0,
                    "error": 1,
                    "message": "Meses de crédito debe ser un número válido",
                    "values": {}
                }, status=400)

        # 4️⃣ Iniciar transacción atómica
        with transaction.atomic():
            total_pedido = 0
            fecha_actual = datetime.datetime.now()

            # 5️⃣ Verificar stock y precios antes de crear pedido
            productos_verificados = []
            for detalle in carrito.carrito_detalles.select_related("producto"):
                producto = detalle.producto
                
                # Verificar stock
                if detalle.cantidad > producto.stock:
                    return Response({
                        "status": 0,
                        "error": 1,
                        "message": f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock}, solicitado: {detalle.cantidad}",
                        "values": {}
                    }, status=400)
                
                # Verificar que el producto esté activo
                if not producto.is_active:
                    return Response({
                        "status": 0,
                        "error": 1,
                        "message": f"El producto '{producto.nombre}' no está disponible",
                        "values": {}
                    }, status=400)

                # Determinar precio según forma de pago
                if forma_pago.nombre.lower() == "credito":
                    precio_unitario = producto.precio_cuota
                    if not precio_unitario or precio_unitario <= 0:
                        return Response({
                            "status": 0,
                            "error": 1,
                            "message": f"El producto '{producto.nombre}' no tiene precio a crédito configurado",
                            "values": {}
                        }, status=400)
                else:
                    precio_unitario = producto.precio_contado
                    if not precio_unitario or precio_unitario <= 0:
                        return Response({
                            "status": 0,
                            "error": 1,
                            "message": f"El producto '{producto.nombre}' no tiene precio contado configurado",
                            "values": {}
                        }, status=400)

                subtotal = precio_unitario * detalle.cantidad
                total_pedido += subtotal
                
                productos_verificados.append({
                    'producto': producto,
                    'detalle': detalle,
                    'precio_unitario': precio_unitario,
                    'subtotal': subtotal
                })

            # 6️⃣ Determinar estado del pedido según forma de pago
            if forma_pago.nombre.lower() in ["tarjeta de débito", "tarjeta de crédito"]:
                estado_pedido = 'confirmado'  # Pagos con tarjeta se confirman inmediatamente
            elif forma_pago.nombre.lower() == "credito":
                estado_pedido = 'pendiente'   # Crédito requiere aprobación
            else:
                estado_pedido = 'pendiente'   # Otros métodos pendientes de pago

            # 7️⃣ Crear el pedido
            pedido = PedidoModel.objects.create(
                usuario=usuario,
                carrito=carrito,
                forma_pago=forma_pago,
                total=total_pedido,
                estado=estado_pedido
            )

            # 8️⃣ Crear detalles del pedido y actualizar stock
            for item in productos_verificados:
                producto = item['producto']
                detalle = item['detalle']
                
                DetallePedidoModel.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=detalle.cantidad,
                    precio_unitario=item['precio_unitario'],
                    subtotal=item['subtotal']
                )

                # Actualizar stock SOLO si el pedido está confirmado
                if estado_pedido == 'confirmado':
                    producto.stock -= detalle.cantidad
                    producto.save()

            # 9️⃣ Crear plan de pagos según forma de pago
            if forma_pago.nombre.lower() == "credito":
                monto_mensual = total_pedido / meses_credito
                
                for i in range(meses_credito):
                    fecha_vencimiento = fecha_actual + relativedelta(months=i + 1)
                    PlanPagoModel.objects.create(
                        pedido=pedido,
                        numero_cuota=i + 1,
                        monto=monto_mensual,
                        fecha_vencimiento=fecha_vencimiento,
                        estado='pendiente'
                    )
                
                mensaje = f"Pedido a crédito creado exitosamente. {meses_credito} cuotas de {monto_mensual:.2f} Bs"
                
            elif forma_pago.nombre.lower() in ["tarjeta de débito", "tarjeta de crédito"]:
                # Para tarjetas, crear un solo pago inmediato
                PlanPagoModel.objects.create(
                    pedido=pedido,
                    numero_cuota=1,
                    monto=total_pedido,
                    fecha_vencimiento=fecha_actual + relativedelta(days=1),
                    estado='pagado'  # Asumimos pago inmediato con tarjeta
                )
                mensaje = "Pedido con tarjeta procesado exitosamente"
                
            else:
                # Para otros métodos, crear pago pendiente
                PlanPagoModel.objects.create(
                    pedido=pedido,
                    numero_cuota=1,
                    monto=total_pedido,
                    fecha_vencimiento=fecha_actual + relativedelta(days=3),  # 3 días para pagar
                    estado='pendiente'
                )
                mensaje = "Pedido creado exitosamente. Complete el pago en 3 días"

            # 🔟 Desactivar carrito
            carrito.is_active = False
            carrito.save()

        # ✅ Si todo fue bien
        return Response({
            "status": 1,
            "error": 0,
            "message": mensaje,
            "values": {
                "pedido_id": pedido.id,
                "estado": estado_pedido,
                "total": float(total_pedido),
                "forma_pago": forma_pago.nombre
            }
        })

    except Exception as e:
        print(f"❌ Error en generar_pedido: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            "status": 0,
            "error": 1,
            "message": f"Error interno del servidor: {str(e)}",
            "values": {}
        }, status=500)

@api_view(['GET'])
@swagger_auto_schema(operation_description="Obtener el carrito con los productos del usuario")
# @requiere_permiso("Pedido", "leer")
def obtener_mi_carrito(request):
    usuario = request.user

    # 1️⃣ Obtener carrito activo
    carrito = CarritoModel.objects.filter(usuario=usuario, is_active=True).first()
    if not carrito:
        return Response({
            "status": 0,
            "error": 1,
            "message": "No tienes un carrito activo",
            "values": {}
        })

    # 2️⃣ Obtener detalles del carrito
    detalles = carrito.carrito_detalles.select_related('producto').all()
    productos = []
    for detalle in detalles:
        productos.append({
            "producto_id": detalle.producto.id,
            "nombre": detalle.producto.nombre,
            "cantidad": detalle.cantidad,
            "precio_unitario": detalle.precio_unitario,
            "subtotal": detalle.subtotal,
            "stock": detalle.producto.stock,
        })

    # 3️⃣ Devolver respuesta
    return Response({
        "status": 1,
        "error": 0,
        "message": "Carrito obtenido exitosamente",
        "values": {
            "carrito_id": carrito.id,
            "total": carrito.total,
            "productos": productos
        }
    })

@api_view(['GET'])
@swagger_auto_schema(operation_description="Obtener los pedidos con los productos del usuario")
# @requiere_permiso("Pedido", "leer")
def listar_mis_pedidos(request):
    usuario = request.user

    # 1️⃣ Obtener pedidos del usuario
    pedidos = PedidoModel.objects.filter(usuario=usuario).prefetch_related('pedido_detalles__producto').order_by('-fecha')

    resultado = []
    for pedido in pedidos:
        detalles = []
        for detalle in pedido.pedido_detalles.all():
            detalles.append({
                "producto_id": detalle.producto.id,
                "nombre": detalle.producto.nombre,
                "cantidad": detalle.cantidad,
                "precio_unitario": float(detalle.precio_unitario),
                "subtotal": float(detalle.subtotal),
            })

        resultado.append({
            "pedido_id": pedido.id,
            "fecha": pedido.fecha,
            "total": float(pedido.total),
            "estado": pedido.estado,
            "forma_pago": pedido.forma_pago.nombre if pedido.forma_pago else None,
            "detalles": detalles
        })

    return Response({
        "status": 1,
        "error": 0,
        "message": "Pedidos obtenidos exitosamente",
        "values": resultado
    })


@api_view(['GET'])
@swagger_auto_schema(operation_description="Listar todos los pedidos existentes")
@requiere_permiso("Pedido", "leer")
def listar_pedidos(request):
    # 1️⃣ Obtener todos los pedidos
    pedidos = PedidoModel.objects.prefetch_related(
        'pedido_detalles__producto',
        'usuario',
        'forma_pago'
    ).order_by('-fecha')

    resultado = []
    for pedido in pedidos:
        detalles = []
        for detalle in pedido.pedido_detalles.all():
            detalles.append({
                "producto_id": detalle.producto.id,
                "nombre": detalle.producto.nombre,
                "cantidad": detalle.cantidad,
                "precio_unitario": detalle.precio_unitario,
                "subtotal": detalle.subtotal,
            })

        resultado.append({
            "pedido_id": pedido.id,
            "usuario_id": pedido.usuario.id,
            "usuario_nombre": pedido.usuario.get_full_name() or pedido.usuario.username,
            "fecha": pedido.fecha,
            "total": pedido.total,
            "estado": pedido.estado,
            "forma_pago": pedido.forma_pago.nombre if pedido.forma_pago else None,
            "detalles": detalles
        })

    return Response({
        "status": 1,
        "error": 0,
        "message": "Pedidos obtenidos exitosamente",
        "values": resultado
    })


@api_view(['GET'])
@swagger_auto_schema(operation_description="Obtener un pedido mediante su ID")
# @requiere_permiso("Pedido", "leer")
def obtener_pedido(request, pedido_id):
    try:
        pedido = PedidoModel.objects.prefetch_related(
            'pedido_detalles__producto', 'forma_pago', 'usuario'
        ).get(id=pedido_id)
    except PedidoModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": f"No se encontró un pedido con id {pedido_id}",
            "values": {}
        })

    # Construir lista de detalles
    detalles = []
    for detalle in pedido.pedido_detalles.all():
        detalles.append({
            "producto_id": detalle.producto.id,
            "nombre": detalle.producto.nombre,
            "cantidad": detalle.cantidad,
            "precio_unitario": detalle.precio_unitario,
            "subtotal": detalle.subtotal,
        })

    return Response({
        "status": 1,
        "error": 0,
        "message": "Pedido obtenido exitosamente",
        "values": {
            "pedido_id": pedido.id,
            "usuario_id": pedido.usuario.id,
            "usuario_nombre": pedido.usuario.get_full_name() or pedido.usuario.username,
            "fecha": pedido.fecha,
            "total": float(pedido.total),
            "estado": pedido.estado,
            "forma_pago": pedido.forma_pago.nombre if pedido.forma_pago else None,
            "detalles": detalles
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

@api_view(['GET'])
def listar_formas_pago_activas_usuario(request):
    """Formas de pago disponibles para usuarios normales"""
    formas_pago = FormaPagoModel.objects.filter(is_active=True)
    serializer = FormaPagoSerializer(formas_pago, many=True)
    return Response({
        "status": 1,
        "error": 0,
        "message": "Formas de pago obtenidas correctamente",
        "values": {"formas_pago": serializer.data}
    })