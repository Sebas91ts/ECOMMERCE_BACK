# producto/nlp_views.py - VERSIÓN COMPLETA

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.contrib.auth import get_user_model
from .nlp_utils import parse_ecommerce_query
from .models import ProductoModel
from venta.models import CarritoModel, DetalleCarritoModel
from .serializers import ProductoSerializer

Usuario = get_user_model()

class BusquedaNaturalView(APIView):
    permission_classes = []
    
    def post(self, request):
        """
        Procesa solicitudes naturales para buscar o agregar productos al carrito
        """
        query_text = request.data.get('q', '').strip()
        usuario_id = request.data.get('usuario_id')
        
        print(f"=== SOLICITUD NLP ===")
        
        if not query_text:
            return Response({
                "status": 0,
                "error": 1,
                "message": "Se requiere una consulta de texto",
                "values": {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 1. Analizar la consulta natural
        filters = parse_ecommerce_query(query_text)
        
        # 2. Determinar la acción
        accion = filters.get('accion', 'buscar')
        
        # 3. VERIFICAR SI HAY USUARIO_ID PARA AGREGAR AL CARRITO
        if accion == 'agregar_carrito':
            if not usuario_id:
                return self._procesar_busqueda(filters, query_text)
            else:
                return self._procesar_agregar_carrito(filters, usuario_id, query_text)
        else:
            return self._procesar_busqueda(filters, query_text)
    
    def _procesar_busqueda(self, filters, query_text):
        """Procesa búsqueda de productos"""
        q_objects = Q(is_active=True)
        
        # Filtros por nombre del producto
        if filters.get('producto_nombre'):
            producto_nombre = filters['producto_nombre'].lower()
            q_objects &= (
                Q(nombre__icontains=producto_nombre) |
                Q(descripcion__icontains=producto_nombre) |
                Q(subcategoria__nombre__icontains=producto_nombre) |
                Q(subcategoria__categoria__nombre__icontains=producto_nombre)
            )
        
        # Filtro por marca
        if filters.get('marca'):
            q_objects &= Q(marca__nombre__icontains=filters['marca'])
        
        # Filtro por categoría
        if filters.get('categoria'):
            q_objects &= Q(subcategoria__categoria__nombre__icontains=filters['categoria'])
        
        # Filtro por precio máximo
        if filters.get('precio_maximo'):
            q_objects &= Q(precio_contado__lte=filters['precio_maximo'])
        
        # Filtro por características
        if filters.get('caracteristicas'):
            for caracteristica in filters['caracteristicas']:
                if isinstance(caracteristica, str):
                    q_objects &= (
                        Q(descripcion__icontains=caracteristica) |
                        Q(nombre__icontains=caracteristica) |
                        Q(modelo__icontains=caracteristica)
                    )
        
        # Ejecutar búsqueda
        productos = ProductoModel.objects.filter(q_objects).select_related(
            'marca', 'subcategoria', 'subcategoria__categoria'
        ).prefetch_related('imagenes')[:20]
        
        serializer = ProductoSerializer(productos, many=True)
        
        return Response({
            "status": 1,
            "error": 0,
            "message": f"Búsqueda: {query_text}",
            "values": {
                "productos": serializer.data,
                "count": productos.count(),
                "filtros_nlp": filters,
                "accion": "busqueda"
            }
        })
    
    def _procesar_agregar_carrito(self, filters, usuario_id, query_text):
        """Procesa agregado de productos al carrito"""
        try:
            usuario = Usuario.objects.get(id=usuario_id, is_active=True)
            
            # Buscar productos que coincidan EXACTAMENTE
            productos = self._buscar_productos_exactos(filters)
            
            if not productos:
                return Response({
                    "status": 0,
                    "error": 1,
                    "message": f"No se encontraron productos que coincidan con: {query_text}",
                    "values": {}
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Obtener o crear carrito activo
            carrito, created = CarritoModel.objects.get_or_create(
                usuario=usuario,
                is_active=True,
                defaults={'total': 0}
            )
            
            resultados_agregados = []
            producto_agregado = None
            
            # Tomar el producto más relevante (el primero)
            producto = productos[0]
            cantidad = filters.get('cantidad', 1)
            
            # Verificar stock
            if producto.stock < cantidad:
                resultados_agregados.append({
                    "producto": producto.nombre,
                    "agregado": False,
                    "mensaje": f"Stock insuficiente. Disponible: {producto.stock}"
                })
            else:
                # Agregar o actualizar detalle del carrito
                detalle, created = DetalleCarritoModel.objects.get_or_create(
                    carrito=carrito,
                    producto=producto,
                    is_active=True,
                    defaults={
                        'cantidad': cantidad,
                        'precio_unitario': producto.precio_contado,
                        'subtotal': producto.precio_contado * cantidad
                    }
                )
                
                if not created:
                    detalle.cantidad += cantidad
                    detalle.subtotal = detalle.cantidad * detalle.precio_unitario
                    detalle.save()
                
                resultados_agregados.append({
                    "producto": producto.nombre,
                    "agregado": True,
                    "cantidad": detalle.cantidad,
                    "subtotal": float(detalle.subtotal),
                    "precio_unitario": float(detalle.precio_unitario)
                })
                
                producto_agregado = producto
            
            # Recalcular total del carrito
            carrito.calcular_total()
            
            # Serializar el producto agregado para la respuesta
            producto_data = None
            if producto_agregado:
                producto_data = ProductoSerializer(producto_agregado).data
            
            return Response({
                "status": 1,
                "error": 0,
                "message": f"✅ Producto agregado al carrito: {query_text}",
                "values": {
                    "resultados": resultados_agregados,
                    "producto_agregado": producto_data,
                    "carrito_id": carrito.id,
                    "total_carrito": float(carrito.total),
                    "filtros_nlp": filters,
                    "accion": "agregar_carrito"
                }
            })
            
        except Usuario.DoesNotExist:
            print(f"❌ Usuario no encontrado: {usuario_id}")
            return Response({
                "status": 0,
                "error": 1,
                "message": "Usuario no encontrado",
                "values": {}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return Response({
                "status": 0,
                "error": 1,
                "message": f"Error al agregar al carrito: {str(e)}",
                "values": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _buscar_productos_exactos(self, filters):
        """Busca productos con criterios específicos para agregar al carrito"""
        q_objects = Q(is_active=True, stock__gt=0)
        
        producto_nombre = filters.get('producto_nombre', '').lower()
        marca = filters.get('marca', '').lower()
        caracteristicas = filters.get('caracteristicas', [])
        
        # Búsqueda por nombre de producto
        if producto_nombre:
            q_objects &= (
                Q(nombre__icontains=producto_nombre) |
                Q(descripcion__icontains=producto_nombre) |
                Q(subcategoria__nombre__icontains=producto_nombre)
            )
        
        # Búsqueda por marca (EXACTA)
        if marca:
            q_objects &= Q(marca__nombre__iexact=marca)
        
        # Búsqueda por características
        if caracteristicas:
            for carac in caracteristicas:
                if isinstance(carac, str):
                    q_objects &= Q(descripcion__icontains=carac.lower())
        
        productos = ProductoModel.objects.filter(q_objects).select_related(
            'marca', 'subcategoria', 'subcategoria__categoria'
        ).prefetch_related('imagenes')
        
        
        # Ordenar por mejor coincidencia
        if marca:
            productos = productos.order_by('-marca__nombre')
        
        return productos[:5]  # Máximo 5 productos más relevantes