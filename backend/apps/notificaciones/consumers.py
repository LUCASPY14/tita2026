import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.tokens import AccessToken


class NotificacionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        token_str = self._parse_token(self.scope["query_string"].decode())
        user = await self._authenticate(token_str)
        if user is None:
            await self.close(code=4001)
            return
        self.group_name = f"notificaciones_{user.pk}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def notificacion_nueva(self, event):
        await self.send(text_data=json.dumps(event["data"]))

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_token(query_string: str) -> str:
        for part in query_string.split("&"):
            if part.startswith("token="):
                return part[len("token="):]
        return ""

    @database_sync_to_async
    def _authenticate(self, token_str: str):
        from apps.usuarios.models import Usuario
        try:
            payload = AccessToken(token_str)
            return Usuario.objects.get(pk=payload["user_id"])
        except Exception:
            return None
