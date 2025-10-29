# permissions.py
from rest_framework.response import Response
from rest_framework import status
from functools import wraps
from usuario.models import Privilegio, Grupo

def requiere_permiso(componente, accion):
    """
    Decorador genérico para cualquier permiso
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if has_permission(request.user, componente, accion):
                return view_func(request, *args, **kwargs)
            else:
                mensajes = {
                    "leer": "LEER",
                    "crear": "CREAR", 
                    "actualizar": "ACTUALIZAR",
                    "eliminar": "ELIMINAR"
                }
                accion_texto = mensajes.get(accion, accion.upper())
                
                return Response({
                    "status": 2,
                    "error": 1,
                    "message": f"NO TIENE PERMISOS PARA {accion_texto} {componente.upper()}"
                }, status=status.HTTP_403_FORBIDDEN)
        return _wrapped_view
    return decorator

def has_permission(usuario, componente_nombre, accion):
    """Función auxiliar para verificar permisos"""
    if not usuario.is_authenticated:
        return False
    
    # Si es superusuario o staff, tiene todos los permisos
    if usuario.is_superuser or usuario.is_staff:
        return True

    # Si no tiene grupo, no tiene permisos
    if not usuario.grupo:
        return False

    try:
        privilegio = Privilegio.objects.get(
            grupo=usuario.grupo,
            componente__nombre__iexact=componente_nombre,
            componente__is_active=True
        )
    except Privilegio.DoesNotExist:
        return False
    
    mapping = {
        "leer": privilegio.puede_leer,
        "crear": privilegio.puede_crear,
        "actualizar": privilegio.puede_actualizar,
        "eliminar": privilegio.puede_eliminar,
    }
    
    return mapping.get(accion, False)

# Alias para mayor claridad
requiere_lectura = lambda componente: requiere_permiso(componente, "leer")
requiere_creacion = lambda componente: requiere_permiso(componente, "crear")
requiere_actualizacion = lambda componente: requiere_permiso(componente, "actualizar")
requiere_eliminacion = lambda componente: requiere_permiso(componente, "eliminar")

# --------------------------
# Permission Classes para Class-Based Views
# --------------------------
from rest_framework.permissions import BasePermission

class TienePermiso(BasePermission):
    """
    Permission class para Class-Based Views
    """
    def __init__(self, componente, accion):
        self.componente = componente
        self.accion = accion

    def has_permission(self, request, view):
        return has_permission(request.user, self.componente, self.accion)

    def __call__(self):
        return self

# Factory functions para las permission classes
def PuedeLeer(componente):
    return TienePermiso(componente, "leer")

def PuedeCrear(componente):
    return TienePermiso(componente, "crear")

def PuedeActualizar(componente):
    return TienePermiso(componente, "actualizar")

def PuedeEliminar(componente):
    return TienePermiso(componente, "eliminar")