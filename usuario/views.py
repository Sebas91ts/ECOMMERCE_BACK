from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from django.db import transaction

from .models import Usuario, Grupo
from .serializers import UserSerializer, MyTokenObtainPairSerializer, UserProfileSerializer, UserUpdateSerializer
from comercio.permissions import PuedeActualizar, PuedeEliminar, PuedeLeer, PuedeCrear

# --------------------------
# Registro de usuario
# --------------------------
class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Verificar si el grupo existe si se proporciona
            grupo_id = request.data.get('grupo')
            if grupo_id:
                try:
                    grupo = Grupo.objects.get(id=grupo_id, is_active=True)
                except Grupo.DoesNotExist:
                    return Response({
                        "status": 2,
                        "error": 1,
                        "message": "El grupo especificado no existe o no está activo"
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            user = serializer.save()
            
            
            return Response({
                "status": 1,
                "error": 0,
                "message": "Usuario registrado correctamente",
                "values": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "grupo": user.grupo.nombre if user.grupo else None,
                    "ci": user.ci,
                    "telefono": user.telefono
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                "status": 2,
                "error": 1,
                "message": f"Error en el registro: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

# --------------------------
# Login personalizado (usa username y password)
# --------------------------
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed as e:
            error_msg = str(e)
            if "No active account" in error_msg:
                return Response({
                    "status": 2,
                    "error": 1,
                    "message": "Usuario o contraseña incorrectos"
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            return Response({
                "status": 2,
                "error": 1,
                "message": error_msg
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Si pasó la validación, autenticar usuario
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        
        if user:
            # Verificar si el usuario está activo
            if not user.is_active:
                return Response({
                    "status": 2,
                    "error": 1,
                    "message": "La cuenta está desactivada"
                }, status=status.HTTP_401_UNAUTHORIZED)
                
            
            # Datos adicionales del usuario para la respuesta
            user_data = {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "grupo": user.grupo.nombre if user.grupo else None,
                "ci": user.ci,
                "telefono": user.telefono
            }
            
            response_data = serializer.validated_data
            response_data['user'] = user_data
            
            return Response({
                "status": 1,
                "error": 0,
                "message": "Se inició sesión correctamente",
                "values": response_data
            })
        
        return Response({
            "status": 2,
            "error": 1,
            "message": "Error de autenticación"
        }, status=status.HTTP_401_UNAUTHORIZED)

# --------------------------
# Logout
# --------------------------
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return Response({
                    "status": 2,
                    "error": 1,
                    "message": "No se proporcionó token de acceso"
                }, status=status.HTTP_400_BAD_REQUEST)

            token_str = auth_header.split(" ")[1]  # "Bearer <token>"
            token = AccessToken(token_str)

            if hasattr(token, 'blacklist'):
                token.blacklist()

            token.blacklist()
            return Response({
                "status": 1,
                "error": 0,
                "message": "Se cerró la sesión correctamente",
            })

        except IndexError:
            return Response({
                "status": 2,
                "error": 1,
                "message": "Formato de token inválido",
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": 2,
                "error": 1,
                "message": f"Error al cerrar la sesión: {str(e)}",
            }, status=status.HTTP_400_BAD_REQUEST)

# --------------------------
# Perfil de usuario (adicional)
# --------------------------
class UserProfileView(APIView):
    permission_classes = [PuedeLeer("Usuario")]

    def get(self, request):
        user = request.user
        return Response({
            "status": 1,
            "error": 0,
            "values": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "grupo": {
                    "id": user.grupo.id if user.grupo else None,
                    "nombre": user.grupo.nombre if user.grupo else None
                },
                "ci": user.ci,
                "telefono": user.telefono,
                "is_staff": user.is_staff,
                "is_active": user.is_active,
                "date_joined": user.date_joined,
                "last_login": user.last_login
            }
        })

    def put(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": 1,
                "error": 0,
                "message": "Perfil actualizado correctamente",
                "values": serializer.data
            })
        
        return Response({
            "status": 2,
            "error": 1,
            "message": "Error en los datos",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
# --------------------------
# Lista de usuarios (solo staff)
# --------------------------
class UserListView(generics.ListAPIView):
    permission_classes = [PuedeLeer("Usuario")]
    serializer_class = UserProfileSerializer
    
    def get_queryset(self):
        # Solo staff puede ver todos los usuarios
        if self.request.user.is_staff:
            return Usuario.objects.all()
        # Usuarios normales solo ven su perfil
        return Usuario.objects.filter(id=self.request.user.id)
# --------------------------
# Actualizar usuario específico
# --------------------------
class UserUpdateView(generics.UpdateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [PuedeActualizar("Usuario")]

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            return Response({
                "status": 1,
                "error": 0,
                "message": "Usuario actualizado correctamente",
                "values": serializer.data
            })
            
        except Exception as e:
            return Response({
                "status": 2,
                "error": 1,
                "message": f"Error al actualizar usuario: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

# --------------------------
# Eliminar usuario (desactivar)
# --------------------------
class UserDeleteView(generics.DestroyAPIView):
    queryset = Usuario.objects.all()
    permission_classes = [PuedeEliminar("Usuario")]

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            # Verificar si el usuario intenta eliminarse a sí mismo
            if instance == request.user:
                return Response({
                    "status": 2,
                    "error": 1,
                    "message": "No puede desactivar su propio usuario"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # En lugar de eliminar, desactivamos
            instance.is_active = False
            instance.save()
            
            return Response({
                "status": 1,
                "error": 0,
                "message": "Usuario desactivado correctamente"
            })
            
        except Exception as e:
            return Response({
                "status": 2,
                "error": 1,
                "message": f"Error al desactivar usuario: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)


# Ejemplo con function-based views
# @api_view(['GET'])
# @requiere_permiso("Usuario", "leer")