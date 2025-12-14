import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Pedido(models.Model):
    class Estado(models.TextChoices):
        CREADO = "CREADO", "Creado"
        EN_PREPARACION = "EN_PREPARACION", "En preparación"
        LISTO = "LISTO", "Listo"
        ENTREGADO = "ENTREGADO", "Entregado"
        CERRADO = "CERRADO", "Cerrado"
        CANCELADO = "CANCELADO", "Cancelado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Datos visibles para el mesero
    mesa = models.IntegerField(null=True, blank=True)  # 🔥 CAMBIO CLAVE
    cliente = models.CharField(max_length=100, null=True, blank=True)
    plato = models.CharField(max_length=60, blank=True, default="")

    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.CREADO
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    entregado_en = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk:
            prev = Pedido.objects.filter(pk=self.pk).values_list("estado", flat=True).first()
        else:
            prev = None

        if self.estado == self.Estado.ENTREGADO and self.entregado_en is None:
            self.entregado_en = timezone.now()

        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Pedido {self.id} (mesa={self.mesa or '-'}, estado={self.estado})"
