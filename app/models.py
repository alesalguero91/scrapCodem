# models.py
from django.db import models

class ConsultaANSES(models.Model):
    dni = models.CharField(max_length=20)
    cuit = models.CharField(max_length=20, blank=True, null=True)
    nombre = models.CharField(max_length=255, blank=True, null=True)
    cuit_empleador = models.CharField(max_length=20, blank=True, null=True)
    situacion_revista = models.CharField(max_length=255, blank=True, null=True)
    empresa = models.CharField(max_length=255, blank=True, null=True)
    fecha_consulta = models.DateTimeField(auto_now_add=True)
    exito = models.BooleanField(default=False)
    error = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha_consulta']