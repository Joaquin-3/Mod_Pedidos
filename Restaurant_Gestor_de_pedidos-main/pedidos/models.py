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

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ----------------- Datos visibles -----------------
    mesa = models.CharField(max_length=20)
    cliente = models.CharField(max_length=100)
    plato = models.CharField(max_length=60)

    # ----------------- Estado y tiempos -----------------
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.CREADO
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    entregado_en = models.DateTimeField(null=True, blank=True)

    # ----------------- Reglas de negocio -----------------
    def clean(self):
        """
        Regla: una mesa no puede tener dos pedidos activos.
        Activos = todos excepto CERRADO y CANCELADO.
        SOLO se valida al CREAR.
        """
        if not self.pk:  # 🔥 SOLO CUANDO SE CREA
            activos = Pedido.objects.exclude(
                estado__in=[self.Estado.CERRADO, self.Estado.CANCELADO]
            )
            if activos.filter(mesa=self.mesa).exists():
                raise ValidationError(
                    {"mesa": "La mesa ya tiene un pedido activo."}
                )

    def save(self, *args, **kwargs):
        # Ejecutar clean SOLO al crear
        if not self.pk:
            self.full_clean()

        # Setear entregado_en cuando pasa a ENTREGADO
        if self.estado == self.Estado.ENTREGADO and self.entregado_en is None:
            self.entregado_en = timezone.now()

        super().save(*args, **kwargs)

    # ----------------- Transiciones de estado -----------------
    def confirmar(self):
        if self.estado != self.Estado.CREADO:
            raise ValidationError(
                "Solo se puede confirmar un pedido en estado CREADO."
            )
        self.estado = self.Estado.EN_PREPARACION
        self.save(update_fields=["estado", "actualizado_en"])

    def marcar_listo(self):
        if self.estado != self.Estado.EN_PREPARACION:
            raise ValidationError(
                "Solo se puede marcar LISTO desde EN_PREPARACION."
            )
        self.estado = self.Estado.LISTO
        self.save(update_fields=["estado", "actualizado_en"])

    def entregar(self):
        if self.estado != self.Estado.LISTO:
            raise ValidationError(
                "Solo se puede ENTREGAR un pedido LISTO."
            )
        self.estado = self.Estado.ENTREGADO
        self.save(update_fields=["estado", "actualizado_en", "entregado_en"])

    def cerrar(self):
        if self.estado != self.Estado.ENTREGADO:
            raise ValidationError(
                "Solo se puede CERRAR un pedido ENTREGADO."
            )
        self.estado = self.Estado.CERRADO
        self.save(update_fields=["estado", "actualizado_en"])

    def cancelar(self):
        if self.estado in [self.Estado.CERRADO, self.Estado.CANCELADO]:
            raise ValidationError(
                "El pedido ya está finalizado."
            )
        self.estado = self.Estado.CANCELADO
        self.save(update_fields=["estado", "actualizado_en"])

    # ----------------- Meta -----------------
    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Pedido {self.id} | Mesa {self.mesa} | {self.estado}"
