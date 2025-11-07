from django.shortcuts import render
# from utils.encrypted_logger import registrar_accion
from comercio.permissions import requiere_permiso 
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .serializers import CategoriaSerializer, SubcategoriaSerializer, MarcaSerializer, ProductoSerializer, ImagenProductoSerializer
from .models import CategoriaModel, SubcategoriaModel, MarcaModel, ProductoModel
# Create your views here.

# CRUD CATEGORIAS
# --------------------- Crear Categoria ---------------------
@api_view(['POST'])
@requiere_permiso("Categoria", "crear")
def crear_categoria(request):
    serializer = CategoriaSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Categoria creada correctamente",
            "values": {"categoria": serializer.data}
        })
    return Response({
        "status": 0,
        "error": 1,
        "message": "Error al crear Categoría",
        "values": serializer.errors
    })

# --------------------- Editar Categorias ---------------------
@api_view(['PATCH'])
@requiere_permiso("Categoria", "actualizar")
def editar_categoria(request, categoria_id):
    try:
        categoria = CategoriaModel.objects.get(id=categoria_id)
    except CategoriaModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Categoria no encontrada",
            "values": {}
        })

    serializer = CategoriaSerializer(categoria, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Categoria editada correctamente",
            "values": {"categoria": serializer.data}
        })
    return Response({
        "status": 0,
        "error": 1,
        "message": "Error al editar Categoria",
        "values": serializer.errors
    })

# --------------------- Eliminar ( desactivar ) Categorias ---------------------
@api_view(['DELETE'])
@requiere_permiso("Categoria", "eliminar")
def eliminar_categoria(request, categoria_id):
    try:
        categoria = CategoriaModel.objects.get(id=categoria_id)
        categoria.is_active = False
        categoria.save()
    except CategoriaModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Categoria no encontrada",
            "values": {}
        })

    return Response({
        "status": 1,
        "error": 0,
        "message": "Categoria eliminada correctamente",
        "values": {}
    })

# --------------------- Activar Categorias ---------------------
@api_view(['PATCH'])
@requiere_permiso("Categoria", "activar")
def activar_categoria(request, categoria_id):
    try:
        categoria = CategoriaModel.objects.get(id=categoria_id)
        categoria.is_active = True
        categoria.save()
    except CategoriaModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Categoria no encontrada",
            "values": {}
        })

    return Response({
        "status": 1,
        "error": 0,
        "message": "Categoria activada correctamente",
        "values": {}
    })

# --------------------- Listar Categorias ( ACTIVAS )---------------------
@api_view(['GET'])
@requiere_permiso("Categoria", "leer")
def listar_categorias_activas(request):
    categorias = CategoriaModel.objects.filter(is_active=True)
    serializer = CategoriaSerializer(categorias, many=True)
    return Response({
        "status": 1,
        "error": 0,
        "message": "Categorias obtenidas correctamente",
        "values": {"categorias": serializer.data}
    })

# --------------------- Listar Todas las Categorias ---------------------
@api_view(['GET'])
@requiere_permiso("Categoria", "leer")
def listar_categorias(request):
    categorias = CategoriaModel.objects.all()
    serializer = CategoriaSerializer(categorias, many=True)
    return Response({
        "status": 1,
        "error": 0,
        "message": "Categorias obtenidas correctamente",
        "values": {"categorias": serializer.data}
    })

# ---------------------- Listar Categoría por ID ----------------------
@api_view(['GET'])
@requiere_permiso("Categoria", "leer")
def obtener_categoria_por_id(request, categoria_id):
    try:
        categoria = CategoriaModel.objects.get(id=categoria_id)
    except CategoriaModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Categoria no encontrada",
            "values": {}
        })

    serializer = CategoriaSerializer(categoria)
    return Response({
        "status": 1,
        "error": 0,
        "message": "Categoria obtenida correctamente",
        "values": {"categoria": serializer.data}
    })

# CRUD SUBCATEGORIAS
# --------------------- Crear Subcategoria ---------------------
@api_view(['POST'])
@requiere_permiso("Subcategoria", "crear")
def crear_subcategoria(request):
    serializer = SubcategoriaSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Subcategoria creada correctamente",
            "values": {"subcategoria": serializer.data}
        })
    return Response({
        "status": 0,
        "error": 1,
        "message": "Error al crear Subcategoria",
        "values": serializer.errors
    })  

# --------------------- Editar Subcategoria ---------------------
@api_view(['PATCH'])
@requiere_permiso("Subcategoria", "actualizar")
def editar_subcategoria(request, subcategoria_id):
    try:
        subcategoria = SubcategoriaModel.objects.get(id=subcategoria_id)
    except SubcategoriaModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Subcategoria no encontrada",
            "values": {}
        })

    serializer = SubcategoriaSerializer(subcategoria, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Subcategoria editada correctamente",
            "values": {"subcategoria": serializer.data}
        })
    return Response({
        "status": 0,
        "error": 1,
        "message": "Error al editar Subcategoria",
        "values": serializer.errors
    })

# --------------------- Eliminar ( desactivar ) Subcategoria ---------------------
@api_view(['DELETE'])
@requiere_permiso("Subcategoria", "eliminar")
def eliminar_subcategoria(request, subcategoria_id):
    try:
        subcategoria = SubcategoriaModel.objects.get(id=subcategoria_id)
        subcategoria.is_active = False
        subcategoria.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Subcategoria eliminada correctamente",
            "values": {}
        })
    except SubcategoriaModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Subcategoria no encontrada",
            "values": {}
        })

# --------------------- Activar Subcategoria ---------------------
@api_view(['PATCH'])
@requiere_permiso("Subcategoria", "activar")
def activar_subcategoria(request, subcategoria_id):
    try:
        subcategoria = SubcategoriaModel.objects.get(id=subcategoria_id)
        subcategoria.is_active = True
        subcategoria.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Subcategoria activada correctamente",
            "values": {}
        })
    except SubcategoriaModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Subcategoria no encontrada",
            "values": {}
        })

# --------------------- Listar Subcategorias ( ACTIVAS )---------------------
@api_view(['GET'])
@requiere_permiso("Subcategoria", "leer")
def listar_subcategorias_activas(request):
    subcategorias = SubcategoriaModel.objects.filter(is_active=True)
    serializer = SubcategoriaSerializer(subcategorias, many=True)
    return Response({
        "status": 1,
        "error": 0,
        "message": "Subcategorias obtenidas correctamente",
        "values": {"subcategorias": serializer.data}
    })

# --------------------- Listar Todas las Subcategorias ---------------------
@api_view(['GET'])
@requiere_permiso("Subcategoria", "leer")
def listar_subcategorias(request):
    subcategorias = SubcategoriaModel.objects.all()
    serializer = SubcategoriaSerializer(subcategorias, many=True)
    return Response({
        "status": 1,
        "error": 0,
        "message": "Subcategorias obtenidas correctamente",
        "values": {"subcategorias": serializer.data}
    })

# ---------------------- Listar Subcategoría por ID ----------------------
@api_view(['GET'])
@requiere_permiso("Subcategoria", "leer")
def obtener_subcategoria_por_id(request, subcategoria_id):
    try:
        subcategoria = SubcategoriaModel.objects.get(id=subcategoria_id)
    except SubcategoriaModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Subcategoria no encontrada",
            "values": {}
        })

    serializer = SubcategoriaSerializer(subcategoria)
    return Response({
        "status": 1,
        "error": 0,
        "message": "Subcategoria obtenida correctamente",
        "values": {"subcategoria": serializer.data}
    })

# CRUD MARCAS
# --------------------- Crear Marca ---------------------
@api_view(['POST'])
@requiere_permiso("Marca", "crear")
def crear_marca(request):
    serializer = MarcaSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Marca creada correctamente",
            "values": {"marca": serializer.data}
        })
    return Response({
        "status": 0,
        "error": 1,
        "message": "Error al crear Marca",
        "values": serializer.errors
    })
# --------------------- Actualizar Marca ---------------------
@api_view(['PATCH'])
@requiere_permiso("Marca", "actualizar")
def editar_marca(request, marca_id):
    try:
        marca = MarcaModel.objects.get(id=marca_id)
    except MarcaModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Marca no encontrada",
            "values": {}
        })

    serializer = MarcaSerializer(marca, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Marca editada correctamente",
            "values": {"marca": serializer.data}
        })
    return Response({
        "status": 0,
        "error": 1,
        "message": "Error al editar Marca",
        "values": serializer.errors
    })
# --------------------- Eliminar ( desactivar ) Marca ---------------------
@api_view(['DELETE'])
@requiere_permiso("Marca", "eliminar")
def eliminar_marca(request, marca_id):
    try:
        marca = MarcaModel.objects.get(id=marca_id)
        marca.is_active = False
        marca.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Marca eliminada correctamente",
            "values": {"marca": marca.id}
        })
    except MarcaModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Marca no encontrada",
            "values": {}
        })
    
# --------------------- Activar Marca ---------------------
@api_view(['PATCH'])
@requiere_permiso("Marca", "activar")
def activar_marca(request, marca_id):
    try:
        marca = MarcaModel.objects.get(id=marca_id)
        marca.is_active = True
        marca.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Marca activada correctamente",
            "values": {"marca": marca.id}
        })
    except MarcaModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Marca no encontrada",
            "values": {}
        })
# --------------------- Listar Marcas ( ACTIVAS )---------------------
@api_view(['GET'])
@requiere_permiso("Marca", "leer")
def listar_marcas_activas(request):
    marcas = MarcaModel.objects.filter(is_active=True)
    serializer = MarcaSerializer(marcas, many=True)
    return Response({
        "status": 1,
        "error": 0,
        "message": "Marcas activas obtenidas correctamente",
        "values": {"marcas": serializer.data}
    })
# --------------------- Listar Todas las Marcas ---------------------
@api_view(['GET'])
@requiere_permiso("Marca", "leer")
def listar_marcas(request):
    marcas = MarcaModel.objects.all()
    serializer = MarcaSerializer(marcas, many=True)
    return Response({
        "status": 1,
        "error": 0,
        "message": "Todas las marcas obtenidas correctamente",
        "values": {"marcas": serializer.data}
    })
# ---------------------- Obtener Marca por ID ----------------------
@api_view(['GET'])
@requiere_permiso("Marca", "leer")
def obtener_marca_por_id(request, marca_id):
    try:
        marca = MarcaModel.objects.get(id=marca_id)
        serializer = MarcaSerializer(marca)
        return Response({
            "status": 1,
            "error": 0,
            "message": "Marca obtenida correctamente",
            "values": {"marca": serializer.data}
        })
    except MarcaModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Marca no encontrada",
            "values": {}
        })
    
# CRUD PRODUCTOS
# --------------------- Crear Producto ---------------------
@swagger_auto_schema(
    method="post",
    request_body=ProductoSerializer,
    responses={201: ProductoSerializer} 
)
@api_view(['POST'])
@requiere_permiso("Producto", "crear")
def crear_producto(request):
    
    # Debes pasar 'request.data' al serializer
    serializer = ProductoSerializer(data=request.data) 
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Producto creado y fotos subidas a Cloudinary",
            "values": {"producto": serializer.data}
        }, status=201)
        
    return Response({
        "status": 0,
        "error": 1,
        "message": "Error al crear Producto",
        "values": serializer.errors
    }, status=400)

# --------------------- Actualizar Producto ---------------------
@api_view(['PATCH'])
@requiere_permiso("Producto", "editar")
def editar_producto(request, producto_id):
    try:
        producto = ProductoModel.objects.get(id=producto_id)
        serializer = ProductoSerializer(producto, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": 1,
                "error": 0,
                "message": "Producto actualizado correctamente",
                "values": {"producto": serializer.data}
            })
        return Response({
            "status": 0,
            "error": 1,
            "message": "Error al actualizar Producto",
            "values": serializer.errors
        })
    except ProductoModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Producto no encontrado",
            "values": {}
        })

# --------------------- Eliminar ( desactivar ) Producto ---------------------
@api_view(['DELETE'])
@requiere_permiso("Producto", "eliminar")
def eliminar_producto(request, producto_id):
    try:
        producto = ProductoModel.objects.get(id=producto_id)
        producto.is_active = False
        producto.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Producto eliminado correctamente",
            "values": {"producto": producto.id}
        })
    except ProductoModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Producto no encontrado",
            "values": {}
        })
# --------------------- Activar Producto ---------------------
@api_view(['PATCH'])
@requiere_permiso("Producto", "activar")
def activar_producto(request, producto_id):
    try:
        producto = ProductoModel.objects.get(id=producto_id)
        producto.is_active = True
        producto.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "Producto activado correctamente",
            "values": {"producto": producto.id}
        })
    except ProductoModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Producto no encontrado",
            "values": {}
        })
# --------------------- Listar Productos ( ACTIVOS )---------------------
@api_view(['GET'])
@requiere_permiso("Producto", "listar")
def listar_productos_activos(request):
    productos = ProductoModel.objects.filter(is_active=True)
    serializer = ProductoSerializer(productos, many=True)
    return Response({
        "status": 1,
        "error": 0,
        "message": "Productos obtenidos correctamente",
        "values": {"productos": serializer.data}
    })
# ---------------------- Listar Producto por ID ----------------------
@api_view(['GET'])
@requiere_permiso("Producto", "listar")
def obtener_producto_por_id(request, producto_id):
    try:
        producto = ProductoModel.objects.get(id=producto_id, is_active=True)
        serializer = ProductoSerializer(producto)
        return Response({
            "status": 1,
            "error": 0,
            "message": "Producto obtenido correctamente",
            "values": {"producto": serializer.data}
        })
    except ProductoModel.DoesNotExist:
        return Response({
            "status": 0,
            "error": 1,
            "message": "Producto no encontrado",
            "values": {}
        })
# --------------------- Listar Todos los Productos ---------------------
@api_view(['GET'])
@requiere_permiso("Producto", "listar")
def listar_productos(request):
    productos = ProductoModel.objects.all()
    serializer = ProductoSerializer(productos, many=True)
    return Response({
        "status": 1,
        "error": 0,
        "message": "Todos los productos obtenidos correctamente",
        "values": {"productos": serializer.data}
    })