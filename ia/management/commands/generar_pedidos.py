# generar_pedidos_opt_v2.py
import os
import random
import django
from decimal import Decimal
from datetime import date, timedelta

# Configuración Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'comercio.settings')
django.setup()

from usuario.models import Usuario
from producto.models import ProductoModel
from venta.models import (
    PedidoModel, PlanPagoModel, FormaPagoModel, CarritoModel,
    DetalleCarritoModel, DetallePedidoModel, MetodoPagoModel, PagoModel
)

# -------- CONFIGURACIÓN --------
NUM_PEDIDOS = 1000
PROB_CONTADO_PAGADO = 0.8  # Probabilidad de que un pago contado se haya realizado
HOY = date.today()

# Cargar datos existentes
USUARIOS = list(Usuario.objects.filter(is_active=True, grupo=2))
PRODUCTOS = list(ProductoModel.objects.filter(is_active=True))
FORMAS_PAGO = list(FormaPagoModel.objects.all())
METODOS_PAGO = list(MetodoPagoModel.objects.all())

if not USUARIOS or not PRODUCTOS or not FORMAS_PAGO or not METODOS_PAGO:
    print("⚠️ Faltan usuarios, productos, formas de pago o métodos de pago.")
    exit()

print(f"📦 Generando {NUM_PEDIDOS} pedidos sintéticos...")

# -------- LISTAS PARA INSERT BULK --------
pedidos_bulk = []
carritos_bulk = []
detalle_carrito_bulk = []
detalle_pedido_bulk = []

# -------- GENERAR PEDIDOS Y CARROS --------
for i in range(NUM_PEDIDOS):
    usuario = random.choice(USUARIOS)
    forma_pago = random.choice(FORMAS_PAGO)

    # Fecha aleatoria del pedido en el último año
    pedido_fecha = HOY - timedelta(days=random.randint(0, 365))

    carrito = CarritoModel(
        usuario=usuario,
        total=0,
        is_active=False,
        fecha=pedido_fecha
    )
    carritos_bulk.append(carrito)

    # Productos del carrito
    num_productos = random.randint(1, 3)
    productos_elegidos = random.sample(PRODUCTOS, num_productos)
    total = Decimal(0)
    detalles = []

    for producto in productos_elegidos:
        cantidad = random.randint(1, 2)
        if "credito" in forma_pago.nombre.lower():
            precio = producto.precio_cuota or Decimal(random.randint(800, 6000))
        else:
            precio = producto.precio_contado or Decimal(random.randint(800, 6000))
        subtotal = precio * cantidad
        total += subtotal
        detalles.append((producto, cantidad, precio, subtotal))

    # Estado del pedido
    estado_pedido = "pagado" if "credito" in forma_pago.nombre.lower() else ("pagado" if random.random() < PROB_CONTADO_PAGADO else "no pagado")

    pedido = PedidoModel(
        usuario=usuario,
        carrito=carrito,
        forma_pago=forma_pago,
        fecha=pedido_fecha,
        total=total,
        estado=estado_pedido,
        is_active=True
    )
    pedidos_bulk.append(pedido)

    # Crear detalles para carrito y pedido - GUARDAR REFERENCIAS DIRECTAS
    for producto, cantidad, precio, subtotal in detalles:
        detalle_carrito_bulk.append(DetalleCarritoModel(
            carrito=carrito,  # Referencia directa al objeto carrito
            producto=producto,
            cantidad=cantidad,
            precio_unitario=precio,
            subtotal=subtotal
        ))
        detalle_pedido_bulk.append(DetallePedidoModel(
            pedido=pedido,  # Referencia directa al objeto pedido
            producto=producto,
            cantidad=cantidad,
            precio_unitario=precio,
            subtotal=subtotal
        ))

# -------- INSERT BULK: CARROS Y PEDIDOS --------
CarritoModel.objects.bulk_create(carritos_bulk)
PedidoModel.objects.bulk_create(pedidos_bulk)

# -------- CORRECCIÓN: USAR LOS OBJETOS ORIGINALES CON IDs ACTUALIZADAS --------
# Django actualiza los objetos en bulk_create con sus IDs generados
# Podemos usar directamente las listas originales

# Insertar detalles del carrito
DetalleCarritoModel.objects.bulk_create(detalle_carrito_bulk)

# Insertar detalles del pedido
DetallePedidoModel.objects.bulk_create(detalle_pedido_bulk)

# -------- CREAR PLANES DE PAGO Y PAGOS --------
for pedido in pedidos_bulk:  # Usar pedidos_bulk directamente
    nombre_fp = pedido.forma_pago.nombre.lower()
    if "contado" in nombre_fp:
        estado_cuota = "pagado" if pedido.estado == "pagado" else "pendiente"
        plan = PlanPagoModel.objects.create(
            pedido=pedido,
            numero_cuota=1,
            monto=pedido.total,
            fecha_vencimiento=pedido.fecha + timedelta(days=30),
            estado=estado_cuota,
            is_active=True
        )
        if estado_cuota == "pagado":
            PagoModel.objects.create(
                plan_pago=plan,
                metodo_pago=random.choice(METODOS_PAGO),
                fecha_pago=plan.fecha_vencimiento - timedelta(days=random.randint(0, 10)),
                monto=plan.monto,
                comprobante="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                is_active=True
            )
    else:
        num_cuotas = random.randint(3, 6)
        monto_cuota = (pedido.total / num_cuotas).quantize(Decimal("0.01"))
        for n in range(num_cuotas):
            plan = PlanPagoModel.objects.create(
                pedido=pedido,
                numero_cuota=n+1,
                monto=monto_cuota,
                fecha_vencimiento=pedido.fecha + timedelta(days=30*(n+1)),
                estado="pagado",  # todas las cuotas crédito se pagan
                is_active=True
            )
            PagoModel.objects.create(
                plan_pago=plan,
                metodo_pago=random.choice(METODOS_PAGO),
                fecha_pago=plan.fecha_vencimiento - timedelta(days=random.randint(0, 10)),
                monto=plan.monto,
                comprobante="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                is_active=True
            )

print("✅ Todos los pedidos, planes y pagos generados exitosamente, distribuidos en el último año.")