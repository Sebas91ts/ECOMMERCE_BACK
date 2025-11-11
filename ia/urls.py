# ia/urls.py
from django.urls import path
from .views import PrediccionVentasView, PrediccionVentasMensualView

urlpatterns = [
    path('prediccion-ventas/', PrediccionVentasView.as_view(), name='prediccion-ventas'),
    path('prediccion-ventas-mensuales/', PrediccionVentasMensualView.as_view(), name='prediccion-ventas-mensuales'),
]
