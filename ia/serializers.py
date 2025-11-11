# ia/serializers.py
from rest_framework import serializers

class PrediccionVentasSerializer(serializers.Serializer):
    fecha = serializers.DateField(required=False)
    
class PrediccionVentasMensualSerializer(serializers.Serializer):
    anio = serializers.IntegerField(min_value=2000, max_value=2100)
    mes = serializers.IntegerField(min_value=1, max_value=12)