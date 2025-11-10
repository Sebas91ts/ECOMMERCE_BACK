import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import CarritoModel, FormaPagoModel
import json

stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['POST'])
def crear_sesion_pago_stripe(request):
    """Crear sesión de pago con Stripe"""
    try:
        usuario = request.user
        forma_pago_id = request.data.get('forma_pago')
        
        print("🛒 Creando sesión Stripe para usuario:", usuario.id)
        
        # 1️⃣ Verificar carrito activo
        carrito = CarritoModel.objects.filter(usuario=usuario, is_active=True).first()
        if not carrito or not carrito.carrito_detalles.exists():
            return Response({
                "status": 0,
                "error": 1,
                "message": "El carrito está vacío",
                "values": {}
            }, status=400)

        # 2️⃣ Verificar forma de pago
        forma_pago = FormaPagoModel.objects.filter(id=forma_pago_id).first()
        if not forma_pago or forma_pago.nombre.lower() not in ["tarjeta de débito", "tarjeta de crédito"]:
            return Response({
                "status": 0,
                "error": 1,
                "message": "Forma de pago no válida para Stripe",
                "values": {}
            }, status=400)

        # 3️⃣ Verificar stock y precios
        line_items = []
        metadata_items = []
        
        for detalle in carrito.carrito_detalles.select_related("producto"):
            producto = detalle.producto
            
            # Verificar stock
            if detalle.cantidad > producto.stock:
                return Response({
                    "status": 0,
                    "error": 1,
                    "message": f"Stock insuficiente para {producto.nombre}",
                    "values": {}
                }, status=400)
            
            # Usar precio contado para Stripe
            precio_unitario = producto.precio_contado
            if not precio_unitario or precio_unitario <= 0:
                return Response({
                    "status": 0,
                    "error": 1,
                    "message": f"Precio no configurado para {producto.nombre}",
                    "values": {}
                }, status=400)

            # Crear item para Stripe
            line_items.append({
                'price_data': {
                    'currency': 'bob',
                    'product_data': {
                        'name': producto.nombre,
                        'description': producto.descripcion or f"Modelo: {producto.modelo}",
                        'metadata': {
                            'producto_id': producto.id,
                        }
                    },
                    'unit_amount': int(precio_unitario * 100),  # Convertir a centavos
                },
                'quantity': detalle.cantidad,
            })
            
            metadata_items.append(f"{producto.nombre} x{detalle.cantidad}")

        # 4️⃣ Crear sesión de Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=settings.FRONTEND_URL + '/pago-exitoso?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=settings.FRONTEND_URL + '/carrito',
            customer_email=usuario.email,  # Email del usuario
            client_reference_id=str(usuario.id),
            metadata={
                'usuario_id': usuario.id,
                'carrito_id': carrito.id,
                'forma_pago_id': forma_pago_id,
                'productos': ', '.join(metadata_items)
            },
            shipping_address_collection={
                'allowed_countries': ['BO'],  # Solo Bolivia
            },
            custom_text={
                'submit': {
                    'message': 'Al confirmar el pago, aceptas nuestros términos y condiciones.'
                }
            }
        )

        print("✅ Sesión Stripe creada:", session.id)

        return Response({
            "status": 1,
            "error": 0,
            "message": "Sesión de pago creada",
            "values": {
                "sessionId": session.id,
                "publicKey": settings.STRIPE_PUBLISHABLE_KEY
            }
        })

    except stripe.error.StripeError as e:
        print("❌ Error de Stripe:", str(e))
        return Response({
            "status": 0,
            "error": 1,
            "message": f"Error en el procesamiento de pago: {str(e)}",
            "values": {}
        }, status=400)
    except Exception as e:
        print("❌ Error general:", str(e))
        return Response({
            "status": 0,
            "error": 1,
            "message": "Error interno del servidor",
            "values": {}
        }, status=500)

@api_view(['POST'])
@csrf_exempt
def webhook_stripe(request):
    """Webhook para recibir notificaciones de Stripe"""
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return Response({"error": str(e)}, status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return Response({"error": str(e)}, status=400)

    # Manejar el evento
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print("💰 Pago completado:", session.id)
        
        # Aquí puedes procesar el pedido automáticamente
        # usuario_id = session.metadata.get('usuario_id')
        # carrito_id = session.metadata.get('carrito_id')
        # ... procesar pedido ...

    elif event['type'] == 'checkout.session.expired':
        session = event['data']['object']
        print("❌ Sesión expirada:", session.id)

    return Response({"status": "success"})

@api_view(['GET'])
def verificar_pago_stripe(request, session_id):
    """Verificar estado de un pago en Stripe"""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        return Response({
            "status": 1,
            "error": 0,
            "message": "Estado del pago obtenido",
            "values": {
                "payment_status": session.payment_status,
                "status": session.status,
                "customer_email": session.customer_details.get('email'),
                "amount_total": session.amount_total / 100,  # Convertir a Bs
                "metadata": session.metadata
            }
        })
        
    except stripe.error.StripeError as e:
        return Response({
            "status": 0,
            "error": 1,
            "message": f"Error al verificar pago: {str(e)}",
            "values": {}
        }, status=400)