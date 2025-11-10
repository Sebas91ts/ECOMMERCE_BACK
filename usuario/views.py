from django.shortcuts import get_object_or_404, render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes 
from drf_yasg.utils import swagger_auto_schema
from .models import Usuario, Grupo, Dispositivo
from . import models
from . import serializers
from .serializers import UserSerializer, MyTokenObtainPairSerializer, UserProfileSerializer, UserUpdateSerializer, ComponenteSerializer, PrivilegioSerializer, GrupoSerializer
from rest_framework import serializers
from comercio.permissions import PuedeActualizar, PuedeEliminar, PuedeLeer, PuedeCrear,requiere_permiso
# --------------------------
# Registro de usuario
# --------------------------
class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            # Hacer mutable el request.data
            mutable_data = request.data.copy()
            
            print("📥 Datos recibidos:", mutable_data)  # ← AÑADE ESTO PARA DEBUG
            
            # Asignar grupo 2 por defecto
            if 'grupo' not in mutable_data:
                mutable_data['grupo'] = 2
            
            serializer = self.get_serializer(data=mutable_data)
            
            if not serializer.is_valid():
                print("❌ Errores del serializer:", serializer.errors)  # ← AÑADE ESTO
                return Response({
                    "status": 2,
                    "error": 1,
                    "message": "Errores de validación",
                    "errors": serializer.errors  # ← INCLUYE LOS ERRORES DETALLADOS
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = serializer.save()
            
            # Generar tokens JWT para el nuevo usuario
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
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
                    "grupo_id": user.grupo.id if user.grupo else None,
                    "grupo_nombre": user.grupo.nombre if user.grupo else None,
                    "ci": user.ci,
                    "telefono": user.telefono,
                    "is_staff": user.is_staff,
                    "is_active": user.is_active,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print("💥 Error general:", str(e))  # ← AÑADE ESTO
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
                "grupo_id": user.grupo.id if user.grupo else None,  
                "grupo_nombre": user.grupo.nombre if user.grupo else None,  
                "ci": user.ci,
                "telefono": user.telefono,
                "is_staff": user.is_staff,  
                "is_active": user.is_active  
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
    serializer_class = UserSerializer
    
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
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Usuario.objects.filter(id=self.request.user.id)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            # Manejar cambio de contraseña si se proporciona
            password = request.data.get('password')
            if password:
                try:
                    validate_password(password)
                    instance.set_password(password)
                    instance.save()
                except ValidationError as e:
                    return Response({
                        "status": 2,
                        "error": 1,
                        "message": "Error en la contraseña",
                        "errors": {'password': list(e.messages)}
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            user = serializer.save()
            
            # Devolver datos actualizados del usuario
            user_data = UserProfileSerializer(user).data
            
            return Response({
                "status": 1,
                "error": 0,
                "message": "Perfil actualizado correctamente",
                "values": user_data
            })
            
        except Exception as e:
            return Response({
                "status": 2,
                "error": 1,
                "message": f"Error al actualizar el perfil: {str(e)}"
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
        
# --------------------------
# Actualizar perfil de usuario
# --------------------------

class EditarUsuarioView(APIView):
    permission_classes = [PuedeActualizar("Usuario")] 

    def put(self, request, id):
        """Actualización completa del usuario"""
        return self._actualizar_usuario(request, id, partial=False)
    
    def patch(self, request, id):
        """Actualización parcial del usuario"""
        return self._actualizar_usuario(request, id, partial=True)
    
    def _actualizar_usuario(self, request, id, partial=False):
        try:
            usuario = get_object_or_404(Usuario, id=id)
            
            serializer = UserUpdateSerializer(
                usuario,
                data=request.data,
                partial=partial,
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": 1,
                    "error": 0,
                    "message": "Usuario actualizado correctamente",
                    "values": serializer.data
                })
            
            return Response({
                "status": 2,
                "error": 1,
                "message": "Error en los datos",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
                
        except Usuario.DoesNotExist:
            return Response({
                "status": 2,
                "error": 1,
                "message": "Usuario no encontrado"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "status": 2,
                "error": 1,
                "message": f"Error al actualizar el usuario: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --------------------------
# PRIVILEGIO 
# --------------------------

@api_view(['GET'])
# @requiere_permiso("Privilegio","leer") 
def listar_privilegios(request):
    privilegios = models.Privilegio.objects.all()
    serializer = PrivilegioSerializer(privilegios, many=True)
    return Response({
        "status": 1,
        "error": 0,
        "message": "LISTADO DE PRIVILEGIOS",
        "values": {"privilegios": serializer.data}
    })

@swagger_auto_schema(
    method="post",
    request_body=PrivilegioSerializer,
    responses={201: PrivilegioSerializer} 
)
@api_view(['POST'])
#@requiere_permiso("Privilegio","crear") 
def asignar_privilegio(request):
    grupo_id = request.data.get('grupo_id')
    componente_id = request.data.get('componente_id')
    permisos = {
        "puede_leer": request.data.get("puede_leer", False),
        "puede_crear": request.data.get("puede_crear", False),
        "puede_actualizar": request.data.get("puede_actualizar", False),
        "puede_eliminar": request.data.get("puede_eliminar", False),
    }

    if not grupo_id or not componente_id:
        return Response({
            "status": 0,
            "error": 1,
            "message": "GRUPO_ID Y COMPONENTE_ID SON REQUERIDOS",
            "values": None
        })

    grupo = get_object_or_404(Grupo, id=grupo_id)
    componente = get_object_or_404(models.Componente, id=componente_id)

    privilegio, created = models.Privilegio.objects.update_or_create(
        grupo=grupo,
        componente=componente,
        defaults=permisos
    )

    serializer = PrivilegioSerializer(privilegio)
    return Response({
        "status": 1,
        "error": 0,
        "message": "PRIVILEGIO ASIGNADO EXITOSAMENTE",
        "values": {"privilegio": serializer.data}
    })

@swagger_auto_schema(
    method="patch",
    request_body=PrivilegioSerializer,
    responses={200: PrivilegioSerializer} 
)
@api_view(['PATCH'])
@requiere_permiso("Privilegio","actualizar") 
def editar_privilegio(request, privilegio_id):
    privilegio = get_object_or_404(models.Privilegio, id=privilegio_id)
    privilegio.puede_leer = request.data.get("puede_leer", privilegio.puede_leer)
    privilegio.puede_crear = request.data.get("puede_crear", privilegio.puede_crear)
    privilegio.puede_actualizar = request.data.get("puede_actualizar", privilegio.puede_actualizar)
    privilegio.puede_eliminar = request.data.get("puede_eliminar", privilegio.puede_eliminar)
    privilegio.puede_activar = request.data.get("puede_activar", privilegio.puede_activar)

    privilegio.save()

    serializer = PrivilegioSerializer(privilegio)
    return Response({
        "status": 1,
        "error": 0,
        "message": "PRIVILEGIO ACTUALIZADO EXITOSAMENTE",
        "values": {"privilegio": serializer.data}
    })
@api_view(['DELETE'])
@requiere_permiso("Privilegio","eliminar") 
def eliminar_privilegio(request, privilegio_id):
    privilegio = get_object_or_404(models.Privilegio, id=privilegio_id)
    privilegio.delete()
    return Response({
        "status": 1,
        "error": 0,
        "message": "PRIVILEGIO ELIMINADO EXITOSAMENTE",
        "values": {"privilegio_id": privilegio_id}
    })


# --------------------------
# ASIGNAR GRUPO A USUARIO
# --------------------------
@swagger_auto_schema(
    method="post",
    request_body=serializers.Serializer(),
    responses={201: PrivilegioSerializer} 
)
@api_view(['POST'])
def asignar_grupo_usuario(request):
    username = request.data.get('username')
    grupo_id = request.data.get('grupo_id')

    if not username or not grupo_id:
        return Response({
            "status": 0,
            "error": 1,
            "message": "USERNAME y GRUPO_ID son requeridos",
            "values": None
        })

    try:
        usuario = get_object_or_404(Usuario, username=username)
        grupo = get_object_or_404(Grupo, id=grupo_id)
    except:
        return Response({
            "status": 0,
            "error": 1,
            "message": "USUARIO O GRUPO NO ENCONTRADO",
            "values": None
        })

    usuario.grupo = grupo
    usuario.save()

    serializer = UserSerializer(usuario)
    return Response({
        "status": 1,
        "error": 0,
        "message": f"Grupo '{grupo.nombre}' asignado correctamente al usuario '{usuario.username}'",
        "values": {"usuario": serializer.data}
    })

# --------------------------
# ASIGNAR PRIVILEGIOS A GRUPO
# --------------------------
@swagger_auto_schema(
    method="post",
    request_body=serializers.Serializer(),
    responses={201: PrivilegioSerializer(many=True)}
)
@api_view(['POST'])
def asignar_privilegios_grupo(request):
    grupo_id = request.data.get('grupo_id')
    privilegios = request.data.get('privilegios')  # lista de dicts: [{"componente_id": 1, "puede_leer": True,...}]

    if not grupo_id :
        return Response({
            "status": 0,
            "error": 1,
            "message": "GRUPO_ID  son requeridos",
            "values": None
        })
    if not privilegios:
        return Response({
            "status": 0,
            "error": 1,
            "message": "PRIVILEGIOS son requeridos",
            "values": None
        })

    try:
        grupo = get_object_or_404(Grupo, id=grupo_id)
    except:
        return Response({
            "status": 0,
            "error": 1,
            "message": "GRUPO NO ENCONTRADO",
            "values": None
        })

    resultados = []
    for priv in privilegios:
        try:
            componente_id = priv.get('componente_id')
            componente = get_object_or_404(models.Componente, id=componente_id)

            obj, created = models.Privilegio.objects.update_or_create(
                grupo=grupo,
                componente=componente,
                defaults={
                    "puede_leer": priv.get("puede_leer", False),
                    "puede_crear": priv.get("puede_crear", False),
                    "puede_actualizar": priv.get("puede_actualizar", False),
                    "puede_eliminar": priv.get("puede_eliminar", False),
                }
            )
            resultados.append(PrivilegioSerializer(obj).data)
        except:
            continue  # ignorar componentes inválidos

    return Response({
        "status": 1,
        "error": 0,
        "message": f"Privilegios asignados al grupo '{grupo.nombre}'",
        "values": {"privilegios": resultados}
    })

# --------------------------
# GRUPO
# --------------------------
@swagger_auto_schema(
    method='post',
    request_body=GrupoSerializer,  # 👈 Le dice a Swagger qué datos espera
    responses={201: GrupoSerializer}
)
@api_view(['POST'])
#@requiere_permiso("Grupo","crear") 
def crear_grupo(request):
    nombre = request.data.get('nombre')
    descripcion = request.data.get('descripcion', '')

    if not nombre:
        return Response({
            "status": 0,
            "error": 1,
            "message": "EL NOMBRE DEL GRUPO ES REQUERIDO",
            "values": None
        })

    grupo, created = Grupo.objects.get_or_create(nombre=nombre, defaults={"descripcion": descripcion})
    if not created:
        return Response({
            "status": 0,
            "error": 1,
            "message": "EL GRUPO YA EXISTE",
            "values": None
        })

    serializer = GrupoSerializer(grupo)
    return Response({
        "status": 1,
        "error": 0,
        "message": "GRUPO CREADO EXITOSAMENTE",
        "values": {"grupo": serializer.data}
    })

@swagger_auto_schema(
    method='patch',
    request_body=GrupoSerializer,  # 👈 Le dice a Swagger qué datos espera
    responses={201: GrupoSerializer}
)
@api_view(['PATCH'])
@requiere_permiso("Grupo","actualizar") 
def editar_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, id=grupo_id)
    nombre = request.data.get('nombre', grupo.nombre)
    descripcion = request.data.get('descripcion', grupo.descripcion)

    grupo.nombre = nombre
    grupo.descripcion = descripcion
    grupo.save()

    serializer = GrupoSerializer(grupo)
    return Response({
        "status": 1,
        "error": 0,
        "message": "GRUPO ACTUALIZADO EXITOSAMENTE",
        "values": {"grupo": serializer.data}
    })

@api_view(['GET'])
# @requiere_permiso("Grupo","leer") 
def listar_grupos(request):
    grupos = Grupo.objects.all()
    serializer = GrupoSerializer(grupos, many=True)
    return Response({
        "status": 1,
        "error": 0,
        "message": "LISTADO DE GRUPOS",
        "values": {"grupos": serializer.data}
    })

@api_view(['DELETE'])
@requiere_permiso("Grupo","eliminar") 
def eliminar_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, id=grupo_id)
    grupo.is_active = False
    grupo.save()
    return Response({
        "status": 1,
        "error": 0,
        "message": "GRUPO DESACTIVADO EXITOSAMENTE",
        "values": None
    })

@api_view(['PATCH'])
@requiere_permiso("Grupo","activar") 
def activar_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, id=grupo_id)
    grupo.is_active = True
    grupo.save()
    return Response({
        "status": 1,
        "error": 0,
        "message": "GRUPO ACTIVADO EXITOSAMENTE",
        "values": None
    })

# --------------------------
# COMPONENTE
# --------------------------

@api_view(['GET'])
#@requiere_permiso("Componente","leer") 
def listar_componentes(request):
    componentes = models.Componente.objects.filter(is_active=True)
    serializer = ComponenteSerializer(componentes, many=True)
    return Response({
        "status": 1,
        "error": 0,
        "message": "LISTADO DE COMPONENTES",
        "values": {"componentes": serializer.data}
    })

@swagger_auto_schema(
    method='post',
    request_body=ComponenteSerializer,  # 👈 Le dice a Swagger qué datos espera
    responses={201: ComponenteSerializer}
)
@api_view(['POST'])
@requiere_permiso("Componente","crear") 
def crear_componente(request):
    serializer = ComponenteSerializer(data=request.data)
    if serializer.is_valid():
        componente = serializer.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "COMPONENTE CREADO EXITOSAMENTE",
            "values": {"componente": ComponenteSerializer(componente).data}
        })
    else:
        return Response({
            "status": 0,
            "error": 1,
            "message": "ERROR AL CREAR COMPONENTE",
            "values": serializer.errors
        })

@swagger_auto_schema(
    method='patch',
    request_body=ComponenteSerializer,  # 👈 Le dice a Swagger qué datos espera
    responses={201: ComponenteSerializer}
)
@api_view(['PATCH'])
@requiere_permiso("Componente","actualizar") 
def editar_componente(request, componente_id):
    componente = get_object_or_404(models.Componente, id=componente_id)
    serializer = ComponenteSerializer(componente, data=request.data, partial=True)
    if serializer.is_valid():
        componente = serializer.save()
        return Response({
            "status": 1,
            "error": 0,
            "message": "COMPONENTE ACTUALIZADO EXITOSAMENTE",
            "values": {"componente": ComponenteSerializer(componente).data}
        })
    else:
        return Response({
            "status": 0,
            "error": 1,
            "message": "ERROR AL EDITAR COMPONENTE",
            "values": serializer.errors
        })


@api_view(['DELETE'])
@requiere_permiso("Componente","eliminar") 
def eliminar_componente(request, componente_id):

    componente = get_object_or_404(models.Componente, id=componente_id)
    componente.is_active = False
    componente.save()
    return Response({
        "status": 1,
        "error": 0,
        "message": "COMPONENTE DESACTIVADO EXITOSAMENTE",
        "values": None
    })


@api_view(['PATCH'])
@requiere_permiso("Componente","activar") 
def activar_componente(request, componente_id):
    componente = get_object_or_404(models.Componente, id=componente_id)
    componente.is_active = True
    componente.save()
    return Response({
        "status": 1,
        "error": 0,
        "message": "COMPONENTE ACTIVADO EXITOSAMENTE",
        "values": None
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registrar_token(request):
    usuario = request.user
    token = request.data.get("token")
    plataforma = request.data.get("plataforma", "android")

    if not token:
        return Response({"status": 0, "error": 1, "message": "no se pudo registrar el token"})

    dispositivo, created = Dispositivo.objects.update_or_create(
        usuario=usuario,
        token=token,
        defaults={"plataforma": plataforma},
    )

    return Response({
                "status": 1,
                "error": 0,
                "message": "Se registró el token",
                "values": token,
    })