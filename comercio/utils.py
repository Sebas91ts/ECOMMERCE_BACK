import os
from django.conf import settings
import firebase_admin
from firebase_admin import credentials, messaging
import json
import logging
from usuario.models import Dispositivo, Usuario, Grupo  # 🔹 Usa tu modelo Usuario
# from django.contrib.auth.models import Group
from django.db.models import Q

def initialize_firebase():
    if not firebase_admin._apps:
        try:
            # Opción 1: Buscar en la ruta de Secrets Files de Render
            render_secrets_path = '/etc/secrets/firebase_key.json'
            
            # Opción 2: Ruta local de desarrollo
            local_secrets_path = os.path.join(settings.BASE_DIR, 'secrets', 'firebase_key.json')
            
            # Opción 3: Desde variable de entorno (backup)
            firebase_config_json = os.environ.get('FIREBASE_CONFIG')
            
            if os.path.exists(render_secrets_path):
                # Render Secrets Files
                cred = credentials.Certificate(render_secrets_path)
                print("Firebase initialized from Render Secrets Files")
            elif os.path.exists(local_secrets_path):
                # Desarrollo local
                cred = credentials.Certificate(local_secrets_path)
                print("Firebase initialized from local file")
            elif firebase_config_json:
                # Desde variable de entorno
                firebase_config = json.loads(firebase_config_json)
                cred = credentials.Certificate(firebase_config)
                print("Firebase initialized from environment variable")
            else:
                raise Exception("No Firebase configuration found")
            
            firebase_admin.initialize_app(cred)
            
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            # No raises exception para no detener la aplicación

# Inicializar al importar
initialize_firebase()

def enviar_notificacion(token, titulo, mensaje):
    # Tu función existente
    try:
        # Verificar si Firebase está inicializado
        if not firebase_admin._apps:
            initialize_firebase()
            if not firebase_admin._apps:
                return False, "Firebase not initialized"
        
        message = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=mensaje,
            ),
            token=token,
        )
        response = messaging.send(message)
        return True, response
    except Exception as e:
        return False, str(e)
    
# services/notificacion_service.py


logger = logging.getLogger(__name__)

class NotificacionService:
    
    @staticmethod
    def enviar_a_usuario(usuario_id, titulo, mensaje, data_extra=None):
        """Enviar notificación a un usuario específico por ID"""
        try:
            usuario = Usuario.objects.get(id=usuario_id)  # 🔹 Usa tu modelo Usuario
            return NotificacionService._enviar_a_usuario_obj(usuario, titulo, mensaje, data_extra)
        except Usuario.DoesNotExist:
            logger.error(f"Usuario con ID {usuario_id} no encontrado")
            return False

    @staticmethod
    def enviar_a_usuario_por_username(username, titulo, mensaje, data_extra=None):
        """Enviar notificación a un usuario específico por username"""
        try:
            usuario = Usuario.objects.get(username=username)
            return NotificacionService._enviar_a_usuario_obj(usuario, titulo, mensaje, data_extra)
        except Usuario.DoesNotExist:
            logger.error(f"Usuario {username} no encontrado")
            return False

    @staticmethod
    def _enviar_a_usuario_obj(usuario, titulo, mensaje, data_extra=None):
        """Enviar notificación a un objeto usuario"""
        try:
            # 🔹 Usa tu modelo Dispositivo con el campo 'token'
            dispositivos = Dispositivo.objects.filter(usuario=usuario)
            
            if not dispositivos.exists():
                logger.warning(f"Usuario {usuario.username} no tiene dispositivos registrados")
                return False

            exitosos = 0
            for dispositivo in dispositivos:
                # 🔹 Usa dispositivo.token en lugar de token_fcm
                success, _ = enviar_notificacion(
                    dispositivo.token,  # 🔹 Campo correcto
                    titulo, 
                    mensaje
                )
                if success:
                    exitosos += 1

            logger.info(f"Notificación enviada a {exitosos}/{dispositivos.count()} dispositivos de {usuario.username}")
            return exitosos > 0

        except Exception as e:
            logger.error(f"Error enviando a usuario {usuario.username}: {e}")
            return False

    @staticmethod
    def enviar_a_grupo(nombre_grupo, titulo, mensaje, data_extra=None):
        """Enviar notificación a todos los usuarios de un grupo/rol"""
        try:
            grupo = Grupo.objects.get(name=nombre_grupo)
            usuarios = grupo.user_set.all()
            
            total_notificaciones = 0
            for usuario in usuarios:
                if NotificacionService._enviar_a_usuario_obj(usuario, titulo, mensaje, data_extra):
                    total_notificaciones += 1

            logger.info(f"Notificación enviada a {total_notificaciones}/{usuarios.count()} usuarios del grupo {nombre_grupo}")
            return total_notificaciones > 0

        except Grupo.DoesNotExist:
            logger.error(f"Grupo {nombre_grupo} no encontrado")
            return False

    @staticmethod
    def enviar_a_clientes(titulo, mensaje, data_extra=None):
        """Enviar notificación a todos los clientes"""
        return NotificacionService.enviar_a_grupo('cliente', titulo, mensaje, data_extra)

    @staticmethod
    def enviar_a_administradores(titulo, mensaje, data_extra=None):
        """Enviar notificación a todos los administradores"""
        return NotificacionService.enviar_a_grupo('administrador', titulo, mensaje, data_extra)

    @staticmethod
    def enviar_a_varios_usuarios(usuarios_ids, titulo, mensaje, data_extra=None):
        """Enviar notificación a una lista específica de usuarios"""
        try:
            usuarios = Usuario.objects.filter(id__in=usuarios_ids)  # 🔹 Usa tu modelo Usuario
            exitosos = 0
            
            for usuario in usuarios:
                if NotificacionService._enviar_a_usuario_obj(usuario, titulo, mensaje, data_extra):
                    exitosos += 1

            logger.info(f"Notificación enviada a {exitosos}/{len(usuarios_ids)} usuarios específicos")
            return exitosos > 0

        except Exception as e:
            logger.error(f"Error enviando a lista de usuarios: {e}")
            return False

    @staticmethod
    def enviar_a_todos(titulo, mensaje, data_extra=None):
        """Enviar notificación a TODOS los usuarios (útil para anuncios)"""
        try:
            usuarios_con_dispositivos = Usuario.objects.filter(  # 🔹 Usa tu modelo Usuario
                dispositivo__isnull=False  # 🔹 Relación inversa con tu modelo
            ).distinct()
            
            total_enviados = 0
            for usuario in usuarios_con_dispositivos:
                if NotificacionService._enviar_a_usuario_obj(usuario, titulo, mensaje, data_extra):
                    total_enviados += 1

            logger.info(f"Notificación global enviada a {total_enviados} usuarios")
            return total_enviados > 0

        except Exception as e:
            logger.error(f"Error en notificación global: {e}")
            return False

    @staticmethod
    def registrar_dispositivo(usuario, token, plataforma="android"):
        """Registrar o actualizar un dispositivo usando tu modelo"""
        try:
            # 🔹 Usa tu modelo Dispositivo exacto
            dispositivo, creado = Dispositivo.objects.update_or_create(
                token=token,  # 🔹 Campo 'token' de tu modelo
                defaults={
                    'usuario': usuario,
                    'plataforma': plataforma,  # 🔹 Campo 'plataforma' de tu modelo
                }
            )
            
            accion = "registrado" if creado else "actualizado"
            logger.info(f"Dispositivo {accion} para {usuario.username}")
            return True, accion
            
        except Exception as e:
            logger.error(f"Error registrando dispositivo: {e}")
            return False, str(e)

    @staticmethod
    def eliminar_dispositivo(token):
        """Eliminar un dispositivo (usando tu modelo)"""
        try:
            # 🔹 Eliminar por token (campo único en tu modelo)
            eliminados, _ = Dispositivo.objects.filter(token=token).delete()
            
            logger.info(f"Eliminados {eliminados} dispositivos con token {token[:20]}...")
            return eliminados > 0
            
        except Exception as e:
            logger.error(f"Error eliminando dispositivo: {e}")
            return False

    @staticmethod
    def obtener_dispositivos_usuario(usuario_id):
        """Obtener todos los dispositivos de un usuario"""
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            return Dispositivo.objects.filter(usuario=usuario)
        except Usuario.DoesNotExist:
            return Dispositivo.objects.none()

    @staticmethod
    def usuario_tiene_dispositivos(usuario_id):
        """Verificar si un usuario tiene dispositivos registrados"""
        return Dispositivo.objects.filter(usuario_id=usuario_id).exists()