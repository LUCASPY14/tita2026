"""
Views para la app usuarios
"""

import base64
import hashlib
import hmac as hmac_mod
import logging
import secrets
import struct
import time
import uuid
from datetime import timedelta

from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from common.permissions import IsAdmin
from common.throttling import LoginRateThrottle, PortalRateThrottle
from .auditoria import registrar_auditoria

logger = logging.getLogger(__name__)


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

from django.conf import settings as django_settings
from django.core.cache import cache

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as drf_filters

from django.db.models import Count, Max, Q, Avg
from django.db.models.functions import TruncDate

from .models import (
    Usuario,
    Empleado,
    Rol,
    Permiso,
    RolPermiso,
    PerfilUsuario,
    SesionActiva,
    AuditoriaOperacion,
    IntentoLogin,
    BloqueoCuenta,
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


def _user_data(user):
    return {
        "id": user.id,
        "email": user.email,
        "nombre": user.nombre,
        "apellido": user.apellido,
        "rol": user.rol,
        "cliente_id": user.cliente_id if user.cliente else None,
        "debe_cambiar_contrasena": user.debe_cambiar_contrasena,
    }


# Número máximo de sesiones concurrentes por rol
_MAX_SESIONES = {
    "CAJERO": 1,
    "COBRADOR": 1,
    "COCINA": 1,
    "SUPERVISOR": 2,
    "ADMIN": 3,
    "CLIENTE_WEB": 3,
}


def _registrar_sesion(user, request) -> str:
    """
    Crea una SesionActiva para el usuario.
    - Auto-expira sesiones iniciadas hace más de 8 horas (access_token dura 1h,
      por lo que cualquier sesión de 8h+ ya no puede tener token válido).
    - Cierra las sesiones activas más antiguas si se supera el límite por rol.
    - Devuelve el session_key UUID del nuevo registro.
    """
    ip = request.META.get("REMOTE_ADDR")
    ua = (request.META.get("HTTP_USER_AGENT") or "")[:500]

    SesionActiva.objects.filter(
        usuario=user,
        activa=True,
        fecha_inicio__lt=timezone.now() - timedelta(hours=8),
    ).update(activa=False)

    max_s = _MAX_SESIONES.get(getattr(user, "rol", ""), 2)
    activas_qs = SesionActiva.objects.filter(usuario=user, activa=True).order_by("fecha_inicio")
    exceso = activas_qs.count() - (max_s - 1)
    if exceso > 0:
        ids_cerrar = list(activas_qs.values_list("id_sesion", flat=True)[:exceso])
        SesionActiva.objects.filter(id_sesion__in=ids_cerrar).update(activa=False)

    session_key = str(uuid.uuid4())
    SesionActiva.objects.create(
        usuario=user,
        session_key=session_key,
        ip_address=ip,
        user_agent=ua,
        activa=True,
    )
    user.ultimo_acceso = timezone.now()
    user.save(update_fields=["ultimo_acceso"])
    return session_key


# ── Bloqueo automático de cuenta ──────────────────────────────────────────────

def _cache_key_email(email: str) -> str:
    h = hashlib.sha256(email.lower().encode()).hexdigest()[:20]
    return f"login_fail:email:{h}"


def _cache_key_ip(ip: str) -> str:
    return f"login_fail:ip:{ip}"


def _esta_bloqueado_cache(email: str, ip: str) -> bool:
    """Chequeo O(1) en cache antes de autenticar."""
    max_i = django_settings.LOGIN_MAX_INTENTOS
    if email and cache.get(_cache_key_email(email), 0) >= max_i:
        return True
    if ip and cache.get(_cache_key_ip(ip), 0) >= max_i:
        return True
    return False


def _registrar_fallo_login(email: str, ip: str) -> None:
    """
    Incrementa contadores de fallos en cache y crea BloqueoCuenta cuando se
    supera LOGIN_MAX_INTENTOS. La ventana de conteo expira sola (TTL en cache).
    """
    max_i    = django_settings.LOGIN_MAX_INTENTOS
    ventana  = django_settings.LOGIN_VENTANA_MINUTOS * 60
    bloqueo  = django_settings.LOGIN_BLOQUEO_MINUTOS

    # Incrementar contador por email (no atómico en LocMemCache, aceptable para este caso)
    count_email = 0
    if email:
        count_email = cache.get(_cache_key_email(email), 0) + 1
        cache.set(_cache_key_email(email), count_email, timeout=ventana)

    # Incrementar contador por IP
    if ip:
        count_ip = cache.get(_cache_key_ip(ip), 0) + 1
        cache.set(_cache_key_ip(ip), count_ip, timeout=ventana)

    # Si el email supera el umbral y el usuario existe, crear BloqueoCuenta
    if email and count_email >= max_i:
        try:
            user = Usuario.objects.only("id").get(email__iexact=email, is_active=True)
            if not BloqueoCuenta.objects.filter(usuario=user, estado=True).exists():
                BloqueoCuenta.objects.create(
                    usuario=user,
                    motivo=f"Bloqueo automático: {count_email} intentos fallidos en {django_settings.LOGIN_VENTANA_MINUTOS} min",
                    fecha_desbloqueo=timezone.now() + timedelta(minutes=bloqueo),
                    ip_address=ip or None,
                    estado=True,
                )
        except Usuario.DoesNotExist:
            pass


def _limpiar_contadores_login(email: str, ip: str) -> None:
    """Borra los contadores de fallo al producirse un login exitoso."""
    if email:
        cache.delete(_cache_key_email(email))
    if ip:
        cache.delete(_cache_key_ip(ip))


# ──────────────────────────────────────────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Login estándar por email, con soporte adicional de CI/RUC para el portal de padres.
    Si el identificador no contiene '@', se interpreta como CI/RUC y se resuelve al
    email del usuario portal vinculado al cliente con ese ruc_ci.
    """

    def validate(self, attrs):
        identifier = attrs.get(self.username_field, "")
        if "@" not in identifier:
            # Buscar por CI/RUC → resolver al email del usuario portal
            try:
                from apps.clientes.models import Cliente
                cliente = Cliente.objects.select_related("usuario_portal").get(
                    ruc_ci=identifier.strip()
                )
                attrs[self.username_field] = cliente.usuario_portal.email
            except Exception:
                pass  # Dejamos que falle con "credenciales incorrectas"
        return super().validate(attrs)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Login con soporte de 2FA.
    - Sin 2FA: devuelve access + refresh + datos del usuario.
    - Con 2FA: devuelve requires_2fa=True + pre_auth_token (válido 5 min).
      El cliente debe completar el login en POST /api/usuarios/2fa/login/.
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *_args, **_kwargs):
        email = (request.data.get("email") or request.data.get("username") or "").strip().lower()[:254]
        ip    = request.META.get("REMOTE_ADDR") or "0.0.0.0"

        # ── 1. Check cache (O(1) — cubre bloqueos automáticos recientes) ──────
        if _esta_bloqueado_cache(email, ip):
            return Response(
                {"detail": "Demasiados intentos fallidos. Intentá de nuevo en unos minutos."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # ── 2. Check BloqueoCuenta DB (cubre bloqueos manuales y persistentes) ─
        if email:
            try:
                _check_user = Usuario.objects.only("id").get(email__iexact=email, is_active=True)
                bloqueo = (
                    BloqueoCuenta.objects
                    .filter(usuario=_check_user, estado=True)
                    .order_by("-fecha_bloqueo")
                    .first()
                )
                if bloqueo:
                    if bloqueo.fecha_desbloqueo and bloqueo.fecha_desbloqueo <= timezone.now():
                        # Expiró — limpiar inline
                        bloqueo.estado = False
                        bloqueo.save(update_fields=["estado"])
                    else:
                        msg = "Cuenta bloqueada temporalmente."
                        if bloqueo.fecha_desbloqueo:
                            msg += f" Disponible después de las {bloqueo.fecha_desbloqueo.strftime('%H:%M')}."
                        return Response({"detail": msg}, status=status.HTTP_403_FORBIDDEN)
            except Usuario.DoesNotExist:
                pass

        # ── 3. Autenticar ─────────────────────────────────────────────────────
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        except Exception as e:
            # Con ATOMIC_REQUESTS=True, un re-raise haría rollback de los registros
            # de auditoría. Retornamos la Response directamente para que la transacción
            # haga commit y queden persistidos IntentoLogin + AuditoriaOperacion.
            motivo = str(getattr(e, "detail", e))[:100]
            _registrar_fallo_login(email, ip)
            try:
                IntentoLogin.objects.create(
                    email=email or "unknown@audit",
                    ip_address=ip,
                    exitoso=False,
                    motivo_fallo=motivo,
                )
            except Exception:
                logger.warning("No se pudo registrar IntentoLogin (login fallido)", exc_info=True)
            registrar_auditoria(
                request=request,
                operacion="LOGIN",
                tabla="usuarios_usuario",
                descripcion=f"Login fallido para {email}",
                resultado="FALLA",
                mensaje_error=motivo,
            )
            err_status = getattr(e, "status_code", status.HTTP_401_UNAUTHORIZED)
            err_detail = getattr(e, "detail", {"detail": str(e)})
            return Response(err_detail, status=err_status)

        # ── 4. Login exitoso — limpiar contadores ─────────────────────────────
        user = serializer.user
        _limpiar_contadores_login(email, ip)

        try:
            if user.auth_2fa.habilitado:
                pre_auth = signing.dumps({"user_id": user.id}, salt="2fa-pre-auth")
                registrar_auditoria(
                    usuario=user, request=request,
                    operacion="LOGIN_2FA_INICIO",
                    tabla="usuarios_usuario",
                    id_registro=user.id,
                    descripcion=f"Login paso 1 OK — esperando 2FA ({user.email})",
                )
                return Response({"requires_2fa": True, "pre_auth_token": pre_auth})
        except ObjectDoesNotExist:
            pass

        session_key = _registrar_sesion(user, request)
        try:
            IntentoLogin.objects.create(
                email=user.email,
                ip_address=ip,
                exitoso=True,
            )
        except Exception:
            logger.warning("No se pudo registrar IntentoLogin (login exitoso)", exc_info=True)
        registrar_auditoria(
            usuario=user, request=request,
            operacion="LOGIN",
            tabla="usuarios_usuario",
            id_registro=user.id,
            descripcion=f"Login exitoso ({user.email}) rol={user.rol}",
        )
        return Response({**serializer.validated_data, "user": _user_data(user), "session_key": session_key})


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = ["rol", "is_active"]
    search_fields = ["email", "nombre", "apellido"]
    ordering_fields = ["email", "nombre", "fecha_creacion"]
    ordering = ["-fecha_creacion"]

    def get_permissions(self):
        if self.action in ("me", "cambiar_password"):
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.action == "create":
            return UsuarioCreateSerializer
        return UsuarioSerializer

    def perform_create(self, serializer):
        usuario = serializer.save()
        registrar_auditoria(
            request=self.request,
            operacion="CREAR_USUARIO",
            tabla="usuarios_usuario",
            id_registro=usuario.id,
            descripcion=f"Usuario creado: {usuario.email} rol={usuario.rol}",
        )

    def perform_update(self, serializer):
        anterior_rol = serializer.instance.rol
        usuario = serializer.save()
        desc = f"Usuario modificado: {usuario.email}"
        if anterior_rol != usuario.rol:
            desc += f" (rol {anterior_rol}→{usuario.rol})"
        registrar_auditoria(
            request=self.request,
            operacion="MODIFICAR_USUARIO",
            tabla="usuarios_usuario",
            id_registro=usuario.id,
            descripcion=desc,
        )

    def perform_destroy(self, instance):
        registrar_auditoria(
            request=self.request,
            operacion="ELIMINAR_USUARIO",
            tabla="usuarios_usuario",
            id_registro=instance.id,
            descripcion=f"Usuario eliminado: {instance.email} rol={instance.rol}",
        )
        instance.delete()

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
        user = request.user
        user.set_password(serializer.validated_data['password_nuevo'])
        user.debe_cambiar_contrasena = False
        user.save(update_fields=['password', 'debe_cambiar_contrasena'])
        registrar_auditoria(
            request=request,
            operacion="CAMBIO_PASSWORD",
            tabla="usuarios_usuario",
            id_registro=user.id,
            descripcion=f"Cambio de contraseña ({user.email})",
        )
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
    throttle_classes = [PortalRateThrottle]

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
                    "id": cuenta.id,
                    "cantidad_almuerzos": cuenta.cantidad_almuerzos,
                    "monto_total": int(cuenta.monto_total),
                    "monto_pagado": int(cuenta.monto_pagado),
                    "monto_pendiente": int(cuenta.monto_total - cuenta.monto_pagado),
                    "estado": cuenta.estado,
                }

            hijos_data.append({
                "id": hijo.id,
                "nombre": hijo.nombre_completo,
                "grado": hijo.grado_nombre,
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
                "pin_es_defecto": user.cliente.check_pin("0000"),
            },
            "mes": {"anio": hoy.year, "mes": hoy.month},
            "hijos": hijos_data,
        })


class PortalHistorialConsumos(APIView):
    """
    GET /api/v1/usuarios/portal/historial-consumos/?hijo_id=X&anio=2026&mes=5
    Historial de consumos de almuerzos de un hijo del padre autenticado.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [PortalRateThrottle]

    def get(self, request):
        from datetime import date
        from apps.almuerzos.models import RegistroConsumoAlmuerzo

        user = request.user
        if not user.cliente:
            return Response({"detail": "Sin cliente vinculado."}, status=400)

        hijo_id = request.query_params.get("hijo_id")
        anio = int(request.query_params.get("anio", date.today().year))
        mes = int(request.query_params.get("mes", date.today().month))

        hijo = user.cliente.hijos.filter(id=hijo_id, activo=True).first()
        if not hijo:
            return Response({"detail": "Hijo no encontrado."}, status=404)

        consumos_qs = (
            RegistroConsumoAlmuerzo.objects
            .filter(
                hijo=hijo,
                fecha_consumo__year=anio,
                fecha_consumo__month=mes,
                estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            )
            .order_by("-fecha_consumo")
        )

        consumos = list(
            consumos_qs.values(
                "id", "fecha_consumo", "costo_almuerzo", "ya_cobrado",
            )
        )

        return Response({
            "anio": anio,
            "mes": mes,
            "hijo": {"id": hijo.id, "nombre": hijo.nombre_completo},
            "consumos": consumos,
            "total": len(consumos),
            "monto_total": sum(int(c["costo_almuerzo"]) for c in consumos),
            "cobrados": sum(1 for c in consumos if c["ya_cobrado"]),
        })


class PortalHistorialCantina(APIView):
    """
    GET /api/usuarios/portal/historial-cantina/?hijo_id=X&page=1&page_size=15
    Historial de compras en cantina (ventas con tarjeta RFID) del hijo autenticado.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [PortalRateThrottle]

    def get(self, request):
        from apps.ventas.models import Venta

        user = request.user
        if not user.cliente:
            return Response({"detail": "Sin cliente vinculado."}, status=400)

        hijo_id = request.query_params.get("hijo_id")
        if not hijo_id:
            return Response({"detail": "Se requiere hijo_id."}, status=400)

        hijo = user.cliente.hijos.filter(id=hijo_id, activo=True).first()
        if not hijo:
            return Response({"detail": "Hijo no encontrado."}, status=404)

        page_size = min(int(request.query_params.get("page_size", 15)), 50)
        page = max(int(request.query_params.get("page", 1)), 1)
        offset = (page - 1) * page_size

        qs = (
            Venta.objects
            .filter(hijo=hijo, estado=Venta.Estado.ACTIVA)
            .prefetch_related("detalles", "detalles__producto")
            .order_by("-fecha")
        )
        total = qs.count()
        ventas = qs[offset:offset + page_size]

        results = []
        for v in ventas:
            detalles = [
                {
                    "producto_nombre": d.producto.descripcion if d.producto else "—",
                    "cantidad": int(d.cantidad),
                    "precio_unitario": int(d.precio_unitario),
                    "subtotal": int(d.subtotal),
                }
                for d in v.detalles.all()
            ]
            results.append({
                "id": v.id,
                "fecha": v.fecha.isoformat(),
                "monto_total": int(v.monto_total),
                "detalles": detalles,
            })

        return Response({
            "count": total,
            "next": total > offset + page_size,
            "results": results,
        })


class PortalMisFacturas(APIView):
    """
    GET /api/v1/usuarios/portal/mis-facturas/
    Facturas emitidas para el cliente del padre autenticado.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [PortalRateThrottle]

    def get(self, request):
        from apps.contabilidad.models import Factura

        user = request.user
        if not user.cliente:
            return Response({"detail": "Sin cliente vinculado."}, status=400)

        facturas = (
            Factura.objects
            .filter(cliente=user.cliente, estado=Factura.Estado.EMITIDA)
            .order_by("-fecha_emision")
            .values("id", "nro_factura", "fecha_emision", "monto_total", "iva_10", "estado")
        )

        return Response(list(facturas))


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
        if user.rol == Usuario.Rol.CLIENTE_WEB:
            link = f"{portal_url}/portal/reset-password?uid={uid}&token={token}"
        else:
            link = f"{portal_url}/reset-password?uid={uid}&token={token}"

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
        from .models import Intento2FA
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
        from .models import Intento2FA
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
        auth.secret_key = ""  # nosec B105 — vaciando campo 2FA, no es una password hardcodeada
        auth.backup_codes = []
        auth.save(update_fields=["habilitado", "fecha_activacion", "secret_key", "backup_codes"])
        return Response({"detail": f"2FA desactivado para {target.email}."})


class TwoFALoginVerificarView(APIView):
    """
    POST /api/usuarios/2fa/login/
    Segundo paso del login cuando el usuario tiene 2FA habilitado.
    Body: {"pre_auth_token": "...", "codigo": "123456"}
    Emite el JWT real si el código TOTP (o backup code) es válido.
    """
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        from .models import Intento2FA

        pre_auth = request.data.get("pre_auth_token", "")
        codigo = (request.data.get("codigo") or "").strip()
        ip = request.META.get("REMOTE_ADDR")

        if not pre_auth or not codigo:
            return Response(
                {"error": "Se requieren pre_auth_token y codigo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = signing.loads(pre_auth, salt="2fa-pre-auth", max_age=300)
            user = Usuario.objects.get(pk=data["user_id"], is_active=True)
        except (signing.BadSignature, Usuario.DoesNotExist):
            return Response(
                {"error": "Token inválido o expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            auth = user.auth_2fa
        except Exception:
            return Response({"error": "2FA no configurado."}, status=status.HTTP_400_BAD_REQUEST)

        codigo_upper = codigo.upper()
        valido = _verify_totp(auth.secret_key, codigo.lower())

        if not valido and codigo_upper in auth.backup_codes:
            valido = True
            auth.backup_codes = [c for c in auth.backup_codes if c != codigo_upper]
            auth.save(update_fields=["backup_codes"])

        Intento2FA.objects.create(
            usuario=user, ip_address=ip, codigo_ingresado=codigo, exitoso=valido,
        )

        if not valido:
            registrar_auditoria(
                usuario=user, request=request,
                operacion="LOGIN_2FA",
                tabla="usuarios_usuario",
                id_registro=user.id,
                descripcion=f"Código 2FA inválido ({user.email})",
                resultado="FALLA",
                mensaje_error="Código TOTP/backup incorrecto",
            )
            return Response({"error": "Código inválido."}, status=status.HTTP_400_BAD_REQUEST)

        auth.ultima_verificacion = timezone.now()
        auth.save(update_fields=["ultima_verificacion"])

        session_key = _registrar_sesion(user, request)
        registrar_auditoria(
            usuario=user, request=request,
            operacion="LOGIN_2FA",
            tabla="usuarios_usuario",
            id_registro=user.id,
            descripcion=f"Login 2FA exitoso ({user.email})",
        )
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": _user_data(user),
            "session_key": session_key,
        })


class LogoutView(APIView):
    """
    POST /api/v1/usuarios/logout/
    Marca la SesionActiva como inactiva y blacklistea el refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_key = request.data.get("session_key", "")
        if session_key:
            SesionActiva.objects.filter(
                usuario=request.user,
                session_key=session_key,
            ).update(activa=False)

        refresh_token = request.data.get("refresh_token", "")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        registrar_auditoria(
            request=request,
            operacion="LOGOUT",
            tabla="usuarios_usuario",
            id_registro=request.user.id,
            descripcion=f"Logout ({request.user.email})",
        )
        return Response({"detail": "Sesión cerrada."})


# ── Reportes de seguridad y auditoría ────────────────────────────────────────

class ReporteAuditoriaView(APIView):
    """
    GET /api/v1/usuarios/reporte-auditoria/
    Parámetros: desde, hasta (YYYY-MM-DD), operacion, tabla, resultado
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")
        operacion_f = request.query_params.get("operacion")
        tabla_f = request.query_params.get("tabla")
        resultado_f = request.query_params.get("resultado")

        qs = AuditoriaOperacion.objects.all()
        if desde:
            qs = qs.filter(fecha_operacion__date__gte=desde)
        if hasta:
            qs = qs.filter(fecha_operacion__date__lte=hasta)
        if operacion_f:
            qs = qs.filter(operacion__icontains=operacion_f)
        if tabla_f:
            qs = qs.filter(tabla_afectada__icontains=tabla_f)
        if resultado_f:
            qs = qs.filter(resultado=resultado_f)

        por_resultado = list(
            qs.values("resultado").annotate(count=Count("id_auditoria")).order_by("-count")
        )
        top_operaciones = list(
            qs.values("operacion").annotate(count=Count("id_auditoria")).order_by("-count")[:10]
        )
        top_tablas = list(
            qs.exclude(tabla_afectada=None).exclude(tabla_afectada="")
            .values("tabla_afectada").annotate(count=Count("id_auditoria")).order_by("-count")[:10]
        )

        total = qs.count()

        detalle = list(
            qs.select_related("usuario")
            .order_by("-fecha_operacion")[:200]
            .values(
                "id_auditoria",
                "fecha_operacion",
                "usuario__email",
                "operacion",
                "tabla_afectada",
                "id_registro",
                "resultado",
                "ip_address",
                "descripcion",
                "mensaje_error",
            )
        )

        return Response({
            "resumen": {
                "total": total,
                "por_resultado": por_resultado,
                "top_operaciones": top_operaciones,
                "top_tablas": top_tablas,
            },
            "detalle": detalle,
        })


class ReporteIntentosLoginView(APIView):
    """
    GET /api/v1/usuarios/reporte-intentos-login/
    Parámetros: desde, hasta (YYYY-MM-DD)
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")

        qs = IntentoLogin.objects.all()
        if desde:
            qs = qs.filter(fecha_intento__date__gte=desde)
        if hasta:
            qs = qs.filter(fecha_intento__date__lte=hasta)

        total    = qs.count()
        fallidos = qs.filter(exitoso=False).count()
        exitosos = qs.filter(exitoso=True).count()
        tasa_fallo = round(fallidos / total * 100, 1) if total else 0

        # IPs con BloqueoCuenta activo (para marcar columna "bloqueada" en el reporte)
        ips_bloqueadas_set = set(
            BloqueoCuenta.objects.filter(estado=True)
            .exclude(ip_address=None)
            .values_list("ip_address", flat=True)
        )

        top_ips = [
            {
                "ip": row["ip_address"],
                "exitosos": row["_exitosos"],
                "fallidos": row["_fallidos"],
                "bloqueada": row["ip_address"] in ips_bloqueadas_set,
            }
            for row in qs.values("ip_address").annotate(
                _exitosos=Count("id_intento", filter=Q(exitoso=True)),
                _fallidos=Count("id_intento", filter=Q(exitoso=False)),
            ).order_by("-_fallidos")[:20]
        ]

        top_emails = list(
            qs.filter(exitoso=False)
            .values("email")
            .annotate(
                fallidos=Count("id_intento"),
                ultimo_intento=Max("fecha_intento"),
            )
            .order_by("-fallidos")[:20]
            .values("email", "fallidos", "ultimo_intento")
        )

        por_motivo = [
            {"motivo": r["motivo_fallo"], "n": r["_n"]}
            for r in qs.filter(exitoso=False)
            .exclude(motivo_fallo=None).exclude(motivo_fallo="")
            .values("motivo_fallo")
            .annotate(_n=Count("id_intento"))
            .order_by("-_n")
        ]

        tendencia = list(
            qs.annotate(fecha=TruncDate("fecha_intento"))
            .values("fecha")
            .annotate(
                total=Count("id_intento"),
                fallidos=Count("id_intento", filter=Q(exitoso=False)),
                exitosos=Count("id_intento", filter=Q(exitoso=True)),
            )
            .order_by("fecha")
        )

        return Response({
            "resumen": {
                "total_intentos": total,
                "fallidos": fallidos,
                "exitosos": exitosos,
                "tasa_fallo": tasa_fallo,
                "ips_bloqueadas": len(ips_bloqueadas_set),
            },
            "top_ips": top_ips,
            "top_emails": top_emails,
            "por_motivo": por_motivo,
            "tendencia": tendencia,
        })


class ReportePersonalInactivoView(APIView):
    """
    GET /api/v1/usuarios/reporte-personal-inactivo/
    Parámetro: dias (default 30) — umbral de inactividad
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        try:
            dias = int(request.query_params.get("dias", 30))
        except (TypeError, ValueError):
            dias = 30

        umbral = timezone.now() - timedelta(days=dias)
        roles_staff = ["ADMIN", "SUPERVISOR", "CAJERO", "COBRADOR", "COCINA"]

        qs = Usuario.objects.filter(rol__in=roles_staff)
        total = qs.count()
        activos = qs.filter(is_active=True).count()
        inactivos = qs.filter(is_active=False).count()
        sin_acceso = qs.filter(
            is_active=True
        ).filter(
            Q(ultimo_acceso__isnull=True) | Q(ultimo_acceso__lt=umbral)
        ).count()

        por_rol = []
        for rol in roles_staff:
            qs_rol = qs.filter(rol=rol)
            por_rol.append({
                "rol": rol,
                "total": qs_rol.count(),
                "activos": qs_rol.filter(is_active=True).count(),
                "sin_acceso": qs_rol.filter(is_active=True).filter(
                    Q(ultimo_acceso__isnull=True) | Q(ultimo_acceso__lt=umbral)
                ).count(),
            })

        detalle = list(
            qs.filter(is_active=True).filter(
                Q(ultimo_acceso__isnull=True) | Q(ultimo_acceso__lt=umbral)
            )
            .order_by("ultimo_acceso")
            .values("id", "email", "nombre", "apellido", "rol", "ultimo_acceso", "fecha_creacion")
        )

        return Response({
            "resumen": {
                "total": total,
                "activos": activos,
                "inactivos": inactivos,
                "sin_acceso": sin_acceso,
                "n_dias": dias,
            },
            "por_rol": por_rol,
            "detalle": detalle,
        })
