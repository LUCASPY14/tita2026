"""
Views para la app usuarios
"""

import base64
import hashlib
import hmac as hmac_mod
import secrets
import struct
import time

from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from common.permissions import IsAdmin


# ── TOTP helpers (RFC 6238, sin dependencias externas) ────────────────────────

def _generate_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode("utf-8")


def _compute_totp(secret_b32, timestamp=None, step=30):
    key = base64.b32decode(secret_b32.upper(), casefold=True)
    t = int((timestamp if timestamp is not None else time.time()) // step)
    counter = struct.pack(">Q", t)
    mac = hmac_mod.new(key, counter, hashlib.sha1).digest()
    offset = mac[-1] & 0x0F
    value = struct.unpack(">I", mac[offset:offset + 4])[0] & 0x7FFFFFFF
    return f"{value % 1_000_000:06d}"


def _verify_totp(secret_b32, codigo, step=30, tolerance=1):
    now = time.time()
    for delta in range(-tolerance, tolerance + 1):
        expected = _compute_totp(secret_b32, now + delta * step)
        if hmac_mod.compare_digest(codigo.strip(), expected):
            return True
    return False


def _generate_backup_codes(n=8):
    return [secrets.token_hex(3).upper() for _ in range(n)]

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as drf_filters

from .models import (
    Usuario,
    Empleado,
    Rol,
    Permiso,
    RolPermiso,
    PerfilUsuario,
)
from .serializers import (
    UsuarioSerializer,
    UsuarioCreateSerializer,
    CambiarPasswordSerializer,
    RecuperarPasswordSerializer,
    ConfirmarPasswordSerializer,
    EmpleadoSerializer,
    RolSerializer,
    PermisoSerializer,
    RolPermisoSerializer,
    PerfilUsuarioSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Login que devuelve tokens + datos del usuario."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = request.user
            if user and user.is_authenticated:
                response.data['user'] = {
                    'id': user.id,
                    'email': user.email,
                    'nombre': user.nombre,
                    'apellido': user.apellido,
                    'rol': user.rol,
                    'cliente_id': user.cliente_id if user.cliente else None,
                }
        return response


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = ["rol", "is_active"]
    search_fields = ["email", "nombre", "apellido"]
    ordering_fields = ["email", "nombre", "fecha_creacion"]
    ordering = ["-fecha_creacion"]

    def get_permissions(self):
        if self.action == "me":
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.action == "create":
            return UsuarioCreateSerializer
        return UsuarioSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'email': user.email,
            'nombre': user.nombre,
            'apellido': user.apellido,
            'rol': user.rol,
            'cliente_id': user.cliente_id if user.cliente else None,
        })

    @action(detail=False, methods=['post'], url_path='cambiar-password')
    def cambiar_password(self, request):
        serializer = CambiarPasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['password_nuevo'])
        request.user.save(update_fields=['password'])
        return Response({'detail': 'Contraseña actualizada correctamente.'})


class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related("id_rol").all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado", "id_rol"]


class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAdmin]


class PermisoViewSet(viewsets.ModelViewSet):
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer
    permission_classes = [IsAdmin]


class RolPermisoViewSet(viewsets.ModelViewSet):
    queryset = RolPermiso.objects.select_related("id_rol", "id_permiso").all()
    serializer_class = RolPermisoSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id_rol", "id_permiso"]


class PerfilUsuarioViewSet(viewsets.ModelViewSet):
    queryset = PerfilUsuario.objects.select_related("usuario").all()
    serializer_class = PerfilUsuarioSerializer
    permission_classes = [IsAdmin]


class PortalMiHijoView(APIView):
    """
    GET /api/usuarios/portal/mi-hijo/
    Datos del portal para CLIENTE_WEB: hijos con tarjeta, consumos del mes y cuenta mensual.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.cliente:
            return Response(
                {"detail": "No tenés un cliente vinculado a tu cuenta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from datetime import date
        from apps.clientes.models import RestriccionHijo
        from apps.almuerzos.models import RegistroConsumoAlmuerzo, CuentaAlmuerzoMensual

        hoy = date.today()
        hijos_data = []

        for hijo in user.cliente.hijos.filter(activo=True):
            # Tarjeta
            tarjeta_data = None
            try:
                t = hijo.tarjeta
                tarjeta_data = {
                    "nro_tarjeta": t.nro_tarjeta,
                    "saldo_actual": int(t.saldo_actual),
                    "estado": t.estado,
                    "en_alerta": t.esta_en_alerta,
                }
            except Exception:
                pass

            # Restricciones activas
            restricciones = list(
                RestriccionHijo.objects.filter(hijo=hijo, activo=True)
                .values("tipo", "severidad", "descripcion", "requiere_autorizacion")
            )

            # Consumos del mes actual
            consumos_qs = RegistroConsumoAlmuerzo.objects.filter(
                hijo=hijo,
                fecha_consumo__year=hoy.year,
                fecha_consumo__month=hoy.month,
                estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            ).order_by("-fecha_consumo")

            ultimos_consumos = list(
                consumos_qs.values("fecha_consumo", "costo_almuerzo", "ya_cobrado")[:10]
            )

            # Cuenta mensual
            cuenta = CuentaAlmuerzoMensual.objects.filter(
                hijo=hijo, anio=hoy.year, mes=hoy.month
            ).first()
            cuenta_data = None
            if cuenta:
                cuenta_data = {
                    "cantidad_almuerzos": cuenta.cantidad_almuerzos,
                    "monto_total": int(cuenta.monto_total),
                    "monto_pagado": int(cuenta.monto_pagado),
                    "monto_pendiente": int(cuenta.monto_total - cuenta.monto_pagado),
                    "estado": cuenta.estado,
                }

            hijos_data.append({
                "id": hijo.id,
                "nombre": hijo.nombre_completo,
                "grado": hijo.grado,
                "tarjeta": tarjeta_data,
                "restricciones": restricciones,
                "consumos_mes": {
                    "total": consumos_qs.count(),
                    "cobrados": consumos_qs.filter(ya_cobrado=True).count(),
                    "ultimos": ultimos_consumos,
                },
                "cuenta_mensual": cuenta_data,
            })

        return Response({
            "cliente": {
                "id": user.cliente.id,
                "nombre": user.cliente.nombre_completo,
                "email": user.cliente.email,
            },
            "mes": {"anio": hoy.year, "mes": hoy.month},
            "hijos": hijos_data,
        })


class RecuperarPasswordView(APIView):
    """
    POST /api/usuarios/recuperar-password/
    Envía un email con enlace para restablecer contraseña.
    Accesible sin autenticación.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RecuperarPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = Usuario.objects.get(email=email, is_active=True)
        except Usuario.DoesNotExist:
            # No revelar si el email existe
            return Response({"detail": "Si el email existe, recibirás las instrucciones."})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        from apps.notificaciones.services import EmailService
        from django.conf import settings as django_settings

        portal_url = getattr(django_settings, "PORTAL_FRONTEND_URL", "http://localhost:5173")
        link = f"{portal_url}/portal/reset-password?uid={uid}&token={token}"

        EmailService.enviar_simple(
            destinatario_email=email,
            destinatario_nombre=f"{user.nombre} {user.apellido}".strip(),
            asunto="Restablecer contraseña — Cantina Tita",
            cuerpo=(
                f"Hola {user.nombre},\n\n"
                f"Para restablecer tu contraseña hacé clic en el siguiente enlace:\n\n"
                f"{link}\n\n"
                f"El enlace expira en 24 horas.\n\n"
                f"Si no solicitaste este cambio, ignorá este mensaje."
            ),
        )

        return Response({"detail": "Si el email existe, recibirás las instrucciones."})


class ConfirmarPasswordView(APIView):
    """
    POST /api/usuarios/recuperar-password/confirmar/
    Valida el token y establece la nueva contraseña.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ConfirmarPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        password_nuevo = serializer.validated_data["password_nuevo"]

        try:
            pk = force_str(urlsafe_base64_decode(uid))
            user = Usuario.objects.get(pk=pk, is_active=True)
        except (Usuario.DoesNotExist, ValueError, OverflowError):
            return Response(
                {"error": "Enlace inválido o expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "El enlace ya fue usado o expiró."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password_nuevo)
        user.save(update_fields=["password"])
        return Response({"detail": "Contraseña restablecida correctamente."})


# ==============================================================================
# 2FA — Autenticación de dos factores
# ==============================================================================

class TwoFAEstadoView(APIView):
    """GET /api/usuarios/2fa/estado/ — estado actual de 2FA del usuario autenticado."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            auth = request.user.auth_2fa
            return Response({
                "habilitado": auth.habilitado,
                "fecha_activacion": auth.fecha_activacion,
                "ultima_verificacion": auth.ultima_verificacion,
                "tiene_backup_codes": bool(auth.backup_codes),
            })
        except Exception:
            return Response({"habilitado": False, "fecha_activacion": None,
                             "ultima_verificacion": None, "tiene_backup_codes": False})


class TwoFAConfigurarView(APIView):
    """
    POST /api/usuarios/2fa/configurar/
    Genera (o regenera) el secret TOTP y los backup codes.
    Devuelve la URI para el QR y los backup codes en texto plano (solo esta vez).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .models import Autenticacion2FA
        secret = _generate_secret()
        backup_codes = _generate_backup_codes()

        auth, _ = Autenticacion2FA.objects.get_or_create(usuario=request.user)
        auth.secret_key = secret
        auth.backup_codes = backup_codes
        auth.habilitado = False
        auth.fecha_activacion = None
        auth.save(update_fields=["secret_key", "backup_codes", "habilitado", "fecha_activacion"])

        email_safe = request.user.email.replace("@", "%40")
        otp_uri = (
            f"otpauth://totp/CantinaT%20{email_safe}"
            f"?secret={secret}&issuer=CantinaT"
        )
        return Response({
            "otp_uri": otp_uri,
            "secret": secret,
            "backup_codes": backup_codes,
            "instruccion": "Escaneá el QR con tu app TOTP y luego llamá a /2fa/activar/ con un código válido.",
        })


class TwoFAActivarView(APIView):
    """
    POST /api/usuarios/2fa/activar/
    Body: {"codigo": "123456"}
    Valida el TOTP y activa 2FA para el usuario.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .models import Autenticacion2FA, Intento2FA
        codigo = request.data.get("codigo", "")
        ip = request.META.get("REMOTE_ADDR")

        try:
            auth = request.user.auth_2fa
        except Exception:
            return Response(
                {"error": "Primero llamá a /2fa/configurar/ para generar el secret."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if auth.habilitado:
            return Response({"error": "El 2FA ya está activo."}, status=status.HTTP_400_BAD_REQUEST)

        valido = _verify_totp(auth.secret_key, codigo)
        Intento2FA.objects.create(
            usuario=request.user, ip_address=ip,
            codigo_ingresado=codigo, exitoso=valido,
        )

        if not valido:
            return Response({"error": "Código inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST)

        auth.habilitado = True
        auth.fecha_activacion = timezone.now()
        auth.save(update_fields=["habilitado", "fecha_activacion"])
        return Response({"detail": "2FA activado correctamente."})


class TwoFAVerificarView(APIView):
    """
    POST /api/usuarios/2fa/verificar/
    Body: {"codigo": "123456"}  — puede ser TOTP o backup code.
    Registra el intento. Retorna 200 si válido, 400 si no.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .models import Autenticacion2FA, Intento2FA
        codigo = (request.data.get("codigo") or "").strip().upper()
        ip = request.META.get("REMOTE_ADDR")

        try:
            auth = request.user.auth_2fa
        except Exception:
            return Response({"error": "2FA no configurado."}, status=status.HTTP_400_BAD_REQUEST)

        if not auth.habilitado:
            return Response({"error": "2FA no está activo para este usuario."}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar TOTP
        valido = _verify_totp(auth.secret_key, codigo.lower())

        # Verificar backup code si TOTP falla
        if not valido and codigo in auth.backup_codes:
            valido = True
            new_codes = [c for c in auth.backup_codes if c != codigo]
            auth.backup_codes = new_codes
            auth.save(update_fields=["backup_codes"])

        Intento2FA.objects.create(
            usuario=request.user, ip_address=ip,
            codigo_ingresado=codigo, exitoso=valido,
        )

        if not valido:
            return Response({"error": "Código inválido."}, status=status.HTTP_400_BAD_REQUEST)

        auth.ultima_verificacion = timezone.now()
        auth.save(update_fields=["ultima_verificacion"])
        return Response({"detail": "Verificación exitosa."})


class TwoFADesactivarView(APIView):
    """
    POST /api/usuarios/2fa/desactivar/
    Desactiva 2FA. Admins pueden desactivar para cualquier usuario (body: {"usuario_id": X}).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .models import Autenticacion2FA
        usuario_id = request.data.get("usuario_id")

        if usuario_id and request.user.rol == Usuario.Rol.ADMIN:
            try:
                target = Usuario.objects.get(pk=usuario_id)
            except Usuario.DoesNotExist:
                return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        else:
            target = request.user

        try:
            auth = target.auth_2fa
        except Exception:
            return Response({"error": "2FA no está configurado para este usuario."}, status=status.HTTP_400_BAD_REQUEST)

        auth.habilitado = False
        auth.fecha_activacion = None
        auth.secret_key = ""
        auth.backup_codes = []
        auth.save(update_fields=["habilitado", "fecha_activacion", "secret_key", "backup_codes"])
        return Response({"detail": f"2FA desactivado para {target.email}."})