# serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, Grupo, Privilegio, Componente

# --------------------------
# Serializer para Grupo
# --------------------------
class GrupoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grupo
        fields = ['id', 'nombre', 'descripcion', 'is_active']

# --------------------------
# Serializer para Registro de Usuario
# --------------------------
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    grupo_nombre = serializers.CharField(source='grupo.nombre', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'password', 'password2', 'first_name', 'last_name', 
            'email', 'grupo', 'grupo_nombre', 'ci', 'telefono', 'is_active', 'is_staff'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs

    def validate_username(self, value):
        if Usuario.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        return value

    def validate_email(self, value):
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo electrónico ya está en uso.")
        return value

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        
        user = Usuario.objects.create_user(
            **validated_data
        )
        user.set_password(password)
        user.save()
        
        return user

# --------------------------
# Serializer para Actualizar Usuario
# --------------------------
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 
            'grupo', 'ci', 'telefono', 'is_active', 'is_staff'
        ]
        read_only_fields = ['username']  # No permitir cambiar username

# --------------------------
# Serializer para Perfil de Usuario
# --------------------------
class UserProfileSerializer(serializers.ModelSerializer):
    grupo_nombre = serializers.CharField(source='grupo.nombre', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'grupo', 'grupo_nombre', 'ci', 'telefono', 'is_staff',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['username', 'is_staff', 'date_joined', 'last_login']


# --------------------------
# Serializer para Token JWT personalizado
# --------------------------
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Agregar claims personalizados al token
        token['username'] = user.username
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        token['grupo_id'] = user.grupo.id if user.grupo else None  # ← AÑADIDO
        token['grupo_nombre'] = user.grupo.nombre if user.grupo else None

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Agregar datos del usuario a la respuesta
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
            'grupo_id': self.user.grupo.id if self.user.grupo else None,  # ← AÑADIDO
            'grupo_nombre': self.user.grupo.nombre if self.user.grupo else None,  # ← AÑADIDO
            'ci': self.user.ci,
            'telefono': self.user.telefono,
            'is_staff': self.user.is_staff,
            'is_active': self.user.is_active
        }
        
        return data
class ComponenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Componente
        fields = ['id', 'nombre']

class PrivilegioSerializer(serializers.ModelSerializer):
    grupo = GrupoSerializer(read_only=True)
    grupo_id = serializers.PrimaryKeyRelatedField(
        queryset=Grupo.objects.all(), source='grupo', write_only=True
    )
    componente = ComponenteSerializer(read_only=True)
    componente_id = serializers.PrimaryKeyRelatedField(
        queryset=Componente.objects.all(), source='componente', write_only=True
    )

    class Meta:
        model = Privilegio
        fields = [
            'id', 'grupo', 'grupo_id', 'componente', 'componente_id',
            'puede_leer', 'puede_crear', 'puede_activar', 'puede_actualizar', 'puede_eliminar'
        ] 