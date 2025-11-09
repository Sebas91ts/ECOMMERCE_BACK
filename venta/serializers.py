from .models import CarritoModel, DetalleCarritoModel, FormaPagoModel, PedidoModel, DetallePedidoModel
from rest_framework import serializers
class CarritoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarritoModel
        fields = ['id', 'usuario', 'fecha', 'total', 'is_active']
        read_only_fields = ['id', 'fecha', 'total']

class DetalleCarritoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleCarritoModel
        fields = ['id', 'carrito', 'producto', 'cantidad', 'precio']
        read_only_fields = ['id']

class FormaPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormaPagoModel
        fields = ['id', 'nombre', 'descripcion']
        read_only_fields = ['id']

class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PedidoModel
        fields = ['id', 'usuario', 'fecha', 'total', 'estado']
        read_only_fields = ['id', 'fecha', 'total']

class DetallePedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePedidoModel
        fields = ['id', 'pedido', 'producto', 'cantidad', 'precio']
        read_only_fields = ['id']
