from django.db import models
from usuario.models import Usuario
from producto.models import ProductoModel
# Create your models here.

# MODELO DEL CARRITO DE COMPRAS
class CarritoModel(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="usuario_carritos")
    fecha= models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Carrito {self.id} - Creado el {self.fecha}"
    
    def calcular_total(self):
        """Recalcula el total del carrito con debug"""
        detalles = self.carrito_detalles.filter(is_active=True)
        total = sum(detalle.subtotal for detalle in detalles)
        self.total = total
        self.save()
        return total

    def obtener_resumen(self):
        """Obtiene resumen del carrito"""
        detalles = self.carrito_detalles.filter(is_active=True)
        return {
            "total_productos": detalles.count(),
            "total_items": sum(detalle.cantidad for detalle in detalles),
            "total_precio": float(self.total)
        }
    
    class Meta:
        db_table = "carrito"

# DETALLE DEL CARRITO DE COMPRAS
class DetalleCarritoModel(models.Model):
    carrito = models.ForeignKey(CarritoModel, on_delete=models.CASCADE, related_name="carrito_detalles")
    producto = models.ForeignKey(ProductoModel, on_delete=models.CASCADE, related_name="producto_detalles_carrito")
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default = 0.00)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Detalle {self.id} - Carrito {self.carrito.id} - Producto {self.producto.nombre}"
    
    def save(self, *args, **kwargs):
        """Override save para debug"""
        super().save(*args, **kwargs)
    class Meta:
        db_table = "detalle_carrito"

# MODELO FORMAS DE PAGO
class FormaPagoModel(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "forma_pago"

# MODELO PEDIDO
class PedidoModel(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="usuario_pedidos")
    carrito = models.ForeignKey(CarritoModel, on_delete=models.CASCADE, related_name="carrito_pedidos")
    forma_pago = models.ForeignKey(FormaPagoModel, on_delete=models.CASCADE, related_name="forma_pago_pedidos")
    fecha = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=50, choices=[
        ('pendiente', 'Pendiente'),
        ('pagando', 'Pagando'),
        ('pagado', 'Pagado'),
        ('cancelado', 'Cancelado'),
    ], default="Pendiente")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Pedido {self.id} - Usuario {self.usuario.username}"

    class Meta:
        db_table = "pedido"

# MODELO DETALLE PEDIDO
class DetallePedidoModel(models.Model):
    pedido = models.ForeignKey(PedidoModel, on_delete=models.CASCADE, related_name="pedido_detalles")
    producto = models.ForeignKey(ProductoModel, on_delete=models.CASCADE, related_name="producto_detalles_pedido")
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Detalle {self.id} - Pedido {self.pedido.id} - Producto {self.producto.nombre}"

    class Meta:
        db_table = "detalle_pedido"
# MODELO PLAN DE PAGOS ( CUANDO EL USUARIO ELIGE PAGAR EN CUOTAS)
class PlanPagoModel(models.Model):
    pedido = models.ForeignKey(PedidoModel, on_delete=models.CASCADE, related_name="pedido_planes_pago")
    numero_cuota = models.IntegerField(default=1)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=50, choices=[
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
    ], default="Pendiente")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Plan de Pago {self.id} - Pedido {self.pedido.id}"

    class Meta:
        db_table = "plan_pago"

# MODELO METODO DE PAGO
class MetodoPagoModel(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "metodo_pago"

# MODELO PAGOS
class PagoModel(models.Model):
    plan_pago = models.ForeignKey(PlanPagoModel, on_delete=models.CASCADE, related_name="plan_pago_pagos")
    metodo_pago = models.ForeignKey(MetodoPagoModel, on_delete=models.CASCADE, related_name="metodo_pago_pagos")
    fecha_pago = models.DateField(auto_now_add=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    comprobante = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Pago {self.id} - Plan de Pago {self.plan_pago.id}"

    class Meta:
        db_table = "pago"