from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notificacion


@receiver(post_save, sender=Notificacion)
def on_notificacion_created(sender, instance, created, **kwargs):
    if not created:
        return
    from .services import send_push_to_user
    send_push_to_user(
        usuario_id=instance.usuario_id,
        title=instance.titulo,
        body=instance.mensaje,
        url="/notificaciones",
    )
