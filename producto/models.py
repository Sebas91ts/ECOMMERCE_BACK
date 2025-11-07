from django.db import models

# Create your models here.

# CATEGORIAS DE PRODUCTO ELECTRODOMESTICO: "COCINA, REFRIGERACION, LAVADO, ETC"
class CategoriaModel(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "categoria"

# SUBCATEGORIA DE LAS CATEGORIAS DE LOS PRODUCTOS ELECTRODOMESTICO: "REFRIGERADOR, CONGELADOR, NEVERA, ETC"
class SubcategoriaModel(models.Model):
    nombre = models.CharField(max_length=50)
    categoria = models.ForeignKey(CategoriaModel, on_delete=models.CASCADE, blank=True, null=True, related_name="categoria_subcategorias")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "subcategoria"

# MARCA DE LOS PRODUCTOS ELECTRODOMESTICO: "SAMSUNG, LG, WHIRLPOOL, ETC"
class MarcaModel(models.Model):
    nombre = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "marca"

# PRODUCTOS ELECTRODOMESTICO
class ProductoModel(models.Model):
    categoria = models.ForeignKey(CategoriaModel, on_delete=models.CASCADE, related_name="categoria_productos", null=True, blank=True)
    marca = models.ForeignKey(MarcaModel, on_delete=models.CASCADE, related_name="marca_productos", null=True, blank=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    descripcion = models.CharField(max_length=300, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    precio_contado = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    precio_cuota = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    stock = models.IntegerField(blank=True, null=True, default=0)
    garantia_meses = models.IntegerField(blank=True, null=True)
    fecha_registro = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.nombre or 'Producto sin nombre'} - {self.categoria}"

    class Meta:
        db_table = "producto"



class CambioPrecioModel(models.Model):
    producto = models.ForeignKey(ProductoModel, on_delete=models.CASCADE, related_name="cambios_precio")
    precio_anterior = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_nuevo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_cuota_anterior = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_cuota_nuevo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_cambio = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "cambio_precio"

    # tipo_operacion = models.CharField(max_length=20, choices=[
    #     ('venta', 'Venta'),
    #     ('alquiler', 'Alquiler'),
    #     ('anticretico', 'Anticrético'),
    # ], blank=True, null=True)
    
# TABLA DE IMAGENES DE PRODUCTO
class ImagenProductoModel(models.Model):
    producto = models.ForeignKey(
        ProductoModel, 
        on_delete=models.CASCADE, 
        related_name="imagenes", 
        null=False, 
        blank=False
    )
    # Campo para almacenar la URL de la imagen (o la ruta al archivo subido)
    url_imagen = models.CharField(max_length=500, null=False, blank=False)
    
    # Un campo opcional para indicar si esta es la imagen principal/miniatura
    is_main = models.BooleanField(default=False)
    
    # Campo opcional para ordenar las imágenes
    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        # Muestra el nombre del producto al que pertenece y si es la principal
        return f"Imagen para {self.producto.nombre} (Principal: {self.is_main})"

    class Meta:
        db_table = "imagen_producto"
        # Esto asegura que las imágenes se recuperen por defecto en orden
        ordering = ['orden', 'id']