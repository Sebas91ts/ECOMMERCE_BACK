from rest_framework import serializers
from .models import ProductoModel, CategoriaModel, MarcaModel, SubcategoriaModel, CambioPrecioModel, ImagenProductoModel

# SERIALIZER PARA CATEGORÍA DE PRODUCTO
class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaModel
        fields = ['id', 'nombre', 'descripcion', 'is_active']
        read_only_fields = ['id']

# SERIALIZER PARA SUBCATEGORÍA DE PRODUCTO
class SubcategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubcategoriaModel
        fields = ['id', 'nombre', 'categoria', 'is_active']
        read_only_fields = ['id']
    
# SERIALIZER PARA MARCA DE PRODUCTO
class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarcaModel
        fields = ['id', 'nombre', 'is_active']
        read_only_fields = ['id']

class ImagenProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenProductoModel
        fields = ['url_imagen', 'is_main', 'orden']

# Serializer temporal para manejar la entrada de archivos de imagen.
class FileInputSerializer(serializers.Serializer):
    file = serializers.FileField() 
    is_main = serializers.BooleanField(required=False, default=False)
    orden = serializers.IntegerField(required=False, default=0)
    id = serializers.IntegerField(required=False, allow_null=True)

class ProductoSerializer(serializers.ModelSerializer):
    # El campo 'imagenes' ahora acepta una lista de objetos que contienen archivos (no solo URLs)
    imagenes = FileInputSerializer(many=True, write_only=True, required=False)
    imagenes_data = ImagenProductoSerializer(source='imagenes', many=True, read_only=True)
    
    categoria_id = serializers.PrimaryKeyRelatedField(queryset=CategoriaModel.objects.all(), source='categoria', required=False)
    marca_id = serializers.PrimaryKeyRelatedField(queryset=MarcaModel.objects.all(), source='marca', required=False)

    class Meta:
        model = ProductoModel
        fields = (
            'id', 'categoria_id', 'marca_id', 'nombre', 'descripcion', 
            'modelo', 'precio_contado', 'precio_cuota', 'stock', 
            'garantia_meses', 'is_active', 
            'imagenes', 'imagenes_data' # Añadimos ambos campos
        )
    
    # --- Sobreescribir el método create para subir y guardar URLs ---
    def create(self, validated_data):
        import cloudinary.uploader # Importa Cloudinary

        # 1. Extraer la lista de imágenes/archivos
        imagenes_data = validated_data.pop('imagenes')
        
        # 2. Crear la instancia del Producto
        producto = ProductoModel.objects.create(**validated_data)
        
        # 3. Subir y crear cada instancia de ImagenProductoModel
        for item in imagenes_data:
            uploaded_file = item['file']
            
            # --- Lógica de Subida a Cloudinary ---
            try:
                # Sube el archivo a Cloudinary
                upload_result = cloudinary.uploader.upload(uploaded_file)
                url_final = upload_result['secure_url']
            except Exception as e:
                # Manejo de error de subida (crucial en producción)
                print(f"Error subiendo a Cloudinary: {e}")
                # Si falla la subida, puedes optar por abortar o ignorar la imagen
                continue 
            
            # 4. Crear la instancia de ImagenProductoModel con la URL de Cloudinary
            ImagenProductoModel.objects.create(
                producto=producto, 
                url_imagen=url_final, # Guardamos la URL de Cloudinary
                is_main=item.get('is_main', False),
                orden=item.get('orden', 0)
            )
        
        return producto
    def update(self, instance, validated_data):
        import cloudinary.uploader
        
        # 1. Extraer la lista de imágenes (si está presente en la solicitud PATCH)
        imagenes_data = validated_data.pop('imagenes', None)
        
        # 2. Actualizar los campos del modelo Producto (nombre, stock, etc.)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 3. Lógica de Edición y Borrado de Imágenes
        if imagenes_data is not None:
            
            # IDs de las imágenes que el frontend quiere mantener/actualizar
            imagenes_ids_a_mantener = [item['id'] for item in imagenes_data if item.get('id')]
            
            # --- Borrar imágenes antiguas no enviadas ---
            # Las imágenes que existían pero NO tienen ID en la nueva lista deben ser eliminadas.
            for existing_image in instance.imagenes.all():
                if existing_image.id not in imagenes_ids_a_mantener:
                    # Opcional: Borrar de Cloudinary también
                    # import re
                    # public_id = re.findall(r'v\d+/(.*)\.jpg', existing_image.url_imagen)[0]
                    # cloudinary.uploader.destroy(public_id)
                    
                    existing_image.delete()
                    
            # --- Crear nuevas y actualizar existentes ---
            for item in imagenes_data:
                # Caso 1: Imagen Existente (se actualiza solo metadata: is_main, orden)
                if item.get('id'):
                    img_instance = ImagenProductoModel.objects.get(id=item['id'], producto=instance)
                    img_instance.is_main = item.get('is_main', img_instance.is_main)
                    img_instance.orden = item.get('orden', img_instance.orden)
                    # Si el archivo ('file') está presente, ignóralo, ya que no queremos reemplazar la imagen solo por actualizar metadata.
                    img_instance.save() 
                
                # Caso 2: Nueva Imagen (se sube a Cloudinary y se crea)
                elif 'file' in item: 
                    uploaded_file = item['file']
                    
                    try:
                        upload_result = cloudinary.uploader.upload(uploaded_file)
                        url_final = upload_result['secure_url']
                    except Exception as e:
                        print(f"Error subiendo nueva imagen a Cloudinary: {e}")
                        continue 
                        
                    ImagenProductoModel.objects.create(
                        producto=instance, 
                        url_imagen=url_final,
                        is_main=item.get('is_main', False),
                        orden=item.get('orden', 0)
                    )

        return instance