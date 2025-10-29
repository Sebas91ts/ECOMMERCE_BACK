from django.db import models

from django.contrib.auth.models import AbstractUser
# Create your models here.

# --------------------------
# Modelo de Grupo
# --------------------------
class Grupo(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    class Meta:
        db_table = "grupo" 

# --------------------------
# Modelo de Usuario
# --------------------------
class Usuario(AbstractUser):

    # Grupo al que pertenece
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="usuarios", null=True, blank=True)

    # Campos opcionales
    ci = models.CharField(max_length=20, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    # Flags mínimos
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Para poder entrar al admin si quieres

    def __str__(self):
        return self.nombre
    class Meta:
        db_table = "usuario"

# --------------------------
# Modelo de Componente
# --------------------------
class Componente(models.Model):
    nombre = models.CharField(max_length=100)   # Ej: "Propiedad, Contrato"
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre}"
    class Meta:
        db_table = "componente"

# --------------------------
# Privilegios (permisos de grupo sobre componente)
# --------------------------
class Privilegio(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="privilegios")
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE, related_name="privilegios")

    puede_leer = models.BooleanField(default=False)
    puede_crear = models.BooleanField(default=False)
    puede_actualizar = models.BooleanField(default=False)
    puede_eliminar = models.BooleanField(default=False)
    puede_activar = models.BooleanField(default=False)

    class Meta:
        unique_together = ("grupo", "componente")

    def __str__(self):
        return f"{self.grupo.nombre} -> {self.componente.nombre}"
    class Meta:
        db_table = "privilegio"
