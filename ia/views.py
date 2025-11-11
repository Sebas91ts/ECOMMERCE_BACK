from datetime import datetime, date, timedelta
from matplotlib.dates import relativedelta
import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from venta.models import PedidoModel
from ia.serializers import PrediccionVentasSerializer, PrediccionVentasMensualSerializer
import joblib

# --- Cargar los modelos una sola vez ---
modelo_ventas_path = "ia/ml/modelo_random_forest_ventas.pkl"
modelo_pedidos_path = "ia/ml/modelo_random_forest_pedidos.pkl"
modelo_ventas_mensuales_path = "ia/ml/modelo_random_forest_ventas_mensuales.pkl"

modelo = joblib.load(modelo_ventas_mensuales_path)
modelo_ventas = joblib.load(modelo_ventas_path)
modelo_pedidos = joblib.load(modelo_pedidos_path)

class PrediccionVentasView(APIView):
    def get(self, request):
        # Validar parámetros
        serializer = PrediccionVentasSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Fecha de predicción
        fecha_pred = data.get("fecha", date.today())
        if isinstance(fecha_pred, str):
            fecha_pred = datetime.strptime(fecha_pred, "%Y-%m-%d").date()

        # --- Datos históricos ---
        fecha_inicio = fecha_pred - timedelta(days=730)  # últimos 2 años
        fecha_fin = date.today() - timedelta(days=1)

        pedidos_historicos = PedidoModel.objects.filter(
            estado='pagado',
            fecha__range=(fecha_inicio, fecha_fin)
        )

        pedidos_historicos = pedidos_historicos.filter(
            fecha__month=fecha_pred.month,
            fecha__day=fecha_pred.day
        )
        # Calcular estadísticas históricas
        num_pedidos = pedidos_historicos.count()
        total_ventas = sum(p.total for p in pedidos_historicos)
        promedio_pedido = total_ventas / num_pedidos if num_pedidos > 0 else 0

        credito = pedidos_historicos.filter(forma_pago__nombre__icontains="credito").count()
        contado = pedidos_historicos.filter(forma_pago__nombre__icontains="contado").count()

        porcentaje_credito = credito / num_pedidos if num_pedidos > 0 else 0
        porcentaje_contado = contado / num_pedidos if num_pedidos > 0 else 0

        # Variables temporales
        mes = fecha_pred.month
        dia_semana = fecha_pred.weekday()  # 0=lunes, 6=domingo
        temporada = 1 if mes in [1, 6, 11, 12] else 0

        # --- Preparar datos para los modelos ---
        X_ventas = np.array([[num_pedidos,promedio_pedido, porcentaje_credito,
                              porcentaje_contado, mes, dia_semana, temporada]])
        
        X_pedidos = np.array([[ promedio_pedido, porcentaje_credito,
                               porcentaje_contado, mes, dia_semana, temporada]])
            
                # --- Predicciones --- 
        prediccion_ventas = modelo_ventas.predict(X_ventas)[0]
        prediccion_pedidos = modelo_pedidos.predict(X_pedidos)[0]

        # --- Respuesta ---
        return Response({
            "fecha": fecha_pred,
            "historico": {
                "num_pedidos": num_pedidos,
                "total_ventas": total_ventas,
                "promedio_pedido": promedio_pedido,
                "porcentaje_credito": porcentaje_credito,
                "porcentaje_contado": porcentaje_contado
            },
            "prediccion": {
                "ventas_estimadas": float(prediccion_ventas),
                "pedidos_estimados": float(prediccion_pedidos)
            }
        }, status=status.HTTP_200_OK)

class PrediccionVentasMensualView(APIView):
    def get(self, request):
        serializer = PrediccionVentasMensualSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        anio = data['anio']
        mes = data['mes']

        # Calcular rango de 2 años hacia atrás
        fecha_inicio = date.today().replace(day=1) - relativedelta(years=2)
        fecha_fin = date.today().replace(day=1)
        print(fecha_inicio, fecha_fin)
        # Filtrar pedidos históricos para ese mes (hasta mes anterior)
        pedidos_historicos = PedidoModel.objects.filter(
            estado='pagado',
            fecha__range=(fecha_inicio, fecha_fin)
        )

        pedidos_mes = pedidos_historicos.filter(
            fecha__month=mes
        )

        # Estadísticas históricas del mes
        num_pedidos_mes = pedidos_mes.count()
        total_ventas_mes = sum(p.total for p in pedidos_mes)
        promedio_pedido_mes = total_ventas_mes / num_pedidos_mes if num_pedidos_mes > 0 else 0

        credito = pedidos_mes.filter(forma_pago__nombre__icontains="credito").count()
        contado = pedidos_mes.filter(forma_pago__nombre__icontains="contado").count()

        porcentaje_credito = credito / num_pedidos_mes if num_pedidos_mes > 0 else 0
        porcentaje_contado = contado / num_pedidos_mes if num_pedidos_mes > 0 else 0

        temporada = 1 if mes in [1,6,11,12] else 0

        # Preparar input para el modelo
        X = np.array([[num_pedidos_mes, promedio_pedido_mes, porcentaje_credito,
                       porcentaje_contado, mes, temporada]])

        # Predicción
        prediccion_ventas = modelo.predict(X)[0]

        return Response({
            "anio": anio,
            "mes": mes,
            "num_pedidos_historicos": num_pedidos_mes,
            "total_ventas_historico": total_ventas_mes,
            "promedio_pedido_historico": promedio_pedido_mes,
            "porcentaje_credito_historico": porcentaje_credito,
            "porcentaje_contado_historico": porcentaje_contado,
            "prediccion_ventas": float(prediccion_ventas)
        }, status=status.HTTP_200_OK)