"""Servicio de recuperacion de contrasenas y verificacion de email."""

import hashlib
import secrets
from datetime import timedelta
from typing import Dict

from django.db import transaction
from django.utils import timezone

from apps.usuarios.models import (
    AuditoriaOperaciones,
    Empleados,
    SesionesActivas,
    TokensRecuperacion,
)
from apps.usuarios.services.auth_service import AuthenticationService


class PasswordRecoveryService:
    """Servicio de recuperacion y verificacion de email para empleados."""

    TOKEN_EXPIRACION_HORAS = 2
    TOKEN_LENGTH = 32  # 32 bytes -> 64 chars hex
    MAX_INTENTOS_RECUPERACION_DIA = 5

    @staticmethod
    def _generar_token_seguro() -> str:
        return secrets.token_hex(PasswordRecoveryService.TOKEN_LENGTH)

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    @transaction.atomic
    def solicitar_recuperacion_empleado(email: str, ip_address: str) -> Dict:
        """Solicita token de recuperacion para empleado."""
        try:
            empleado = Empleados.objects.filter(email=email, estado=True).first()

            # Mensaje generico para evitar enumeracion de usuarios.
            generic_ok = {
                "success": True,
                "mensaje": "Si el email existe, recibira instrucciones para recuperar su contrasena",
                "token": None,
            }

            if not empleado:
                return generic_ok

            hoy_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            solicitudes_hoy = TokensRecuperacion.objects.filter(
                id_empleado=empleado,
                tipo="password_recovery",
                fecha_creacion__gte=hoy_inicio,
            ).count()
            if solicitudes_hoy >= PasswordRecoveryService.MAX_INTENTOS_RECUPERACION_DIA:
                return {
                    "success": False,
                    "mensaje": (
                        f"Ha excedido el límite de "
                        f"{PasswordRecoveryService.MAX_INTENTOS_RECUPERACION_DIA} solicitudes por día"
                    ),
                }

            token = PasswordRecoveryService._generar_token_seguro()
            token_hash = PasswordRecoveryService._hash_token(token)
            ahora = timezone.now()
            expira = ahora + timedelta(hours=PasswordRecoveryService.TOKEN_EXPIRACION_HORAS)

            # Invalidar tokens previos no usados para el mismo empleado.
            TokensRecuperacion.objects.filter(
                id_empleado=empleado,
                tipo="password_recovery",
                usado=False,
                fecha_expiracion__gt=ahora,
            ).update(usado=True)

            TokensRecuperacion.objects.create(
                id_empleado=empleado,
                tipo="password_recovery",
                token_hash=token_hash,
                fecha_creacion=ahora,
                fecha_expiracion=expira,
                ip_solicitud=ip_address,
                usado=False,
            )

            try:
                AuditoriaOperaciones.objects.create(
                    usuario=empleado.usuario,
                    tipo_usuario="empleado",
                    id_usuario=empleado.id_empleado,
                    operacion="SOLICITAR_RECUPERACION_PASSWORD",
                    tabla_afectada="Empleados",
                    ip_address=ip_address,
                    datos_nuevos={
                        "email": email,
                        "expira_en_horas": PasswordRecoveryService.TOKEN_EXPIRACION_HORAS,
                        "timestamp": str(ahora),
                    },
                    fecha_operacion=ahora,
                    resultado="exitoso",
                )
            except Exception:
                pass

            return {
                "success": True,
                "token": token,
                "mensaje": "Token de recuperacion generado exitosamente",
                "expira_en_minutos": PasswordRecoveryService.TOKEN_EXPIRACION_HORAS * 60,
            }

        except Exception as e:
            print(f"Error al solicitar recuperacion: {str(e)}")
            return {"success": False, "mensaje": "Error al procesar solicitud de recuperacion"}

    @staticmethod
    def validar_token_recuperacion(token: str, tipo_usuario: str = "empleado") -> Dict:
        """Valida token de recuperacion para empleado."""
        try:
            token_hash = PasswordRecoveryService._hash_token(token)
            token_db = TokensRecuperacion.objects.filter(token_hash=token_hash).first()
            if not token_db:
                return {"success": False, "valido": False, "mensaje": "Token invalido"}

            if token_db.usado:
                return {"success": False, "valido": False, "mensaje": "Token ya usado"}

            if token_db.fecha_expiracion <= timezone.now():
                return {"success": False, "valido": False, "mensaje": "Token expirado"}

            empleado = Empleados.objects.filter(email=token_db.id_cliente.email, estado=True).first()
            if not empleado:
                return {"success": False, "valido": False, "mensaje": "Empleado no disponible"}

            return {"success": True, "valido": True, "empleado": empleado, "mensaje": "Token valido"}

        except Exception as e:
            print(f"Error al validar token: {str(e)}")
            return {"success": False, "valido": False, "mensaje": "Error al validar token"}

    @staticmethod
    @transaction.atomic
    def restablecer_password_con_token(token: str, nueva_password: str, ip_address: str) -> Dict:
        """Restablece contrasena usando token temporal."""
        try:
            resultado_validacion = PasswordRecoveryService.validar_token_recuperacion(token)
            if not resultado_validacion["valido"]:
                return {"success": False, "mensaje": resultado_validacion["mensaje"]}

            empleado = resultado_validacion["empleado"]

            es_valida, mensaje_error = AuthenticationService.validar_fortaleza_password(nueva_password)
            if not es_valida:
                return {"success": False, "mensaje": mensaje_error}

            hash_anterior = empleado.contrasena_hash
            empleado.contrasena_hash = AuthenticationService._hash_password(nueva_password)
            empleado.save(update_fields=["contrasena_hash"])

            token_hash = PasswordRecoveryService._hash_token(token)
            TokensRecuperacion.objects.filter(token_hash=token_hash).update(
                usado=True,
                fecha_uso=timezone.now(),
            )

            try:
                AuditoriaOperaciones.objects.create(
                    usuario=empleado.usuario,
                    tipo_usuario="empleado",
                    id_usuario=empleado.id_empleado,
                    operacion="RESTABLECER_PASSWORD_TOKEN",
                    tabla_afectada="Empleados",
                    ip_address=ip_address,
                    datos_anteriores={"hash_password": hash_anterior[:20] + "..."},
                    datos_nuevos={
                        "hash_password": empleado.contrasena_hash[:20] + "...",
                        "timestamp": str(timezone.now()),
                    },
                    fecha_operacion=timezone.now(),
                    resultado="exitoso",
                )
            except Exception:
                pass

            SesionesActivas.objects.filter(usuario=empleado.usuario, activa=True).update(activa=False)

            return {
                "success": True,
                "mensaje": "Contrasena restablecida exitosamente. Por favor, inicie sesion con su nueva contrasena.",
            }

        except Exception as e:
            print(f"Error al restablecer contrasena: {str(e)}")
            return {"success": False, "mensaje": f"Error al restablecer contrasena: {str(e)}"}

    @staticmethod
    @transaction.atomic
    def solicitar_verificacion_email(empleado: Empleados, ip_address: str) -> Dict:
        """Genera token para verificar email de empleado."""
        try:
            token = PasswordRecoveryService._generar_token_seguro()
            token_hash = PasswordRecoveryService._hash_token(token)
            ahora = timezone.now()

            TokensRecuperacion.objects.filter(
                id_empleado=empleado,
                tipo="email_verification",
                usado=False,
            ).update(usado=True)

            TokensRecuperacion.objects.create(
                id_empleado=empleado,
                tipo="email_verification",
                token_hash=token_hash,
                fecha_creacion=ahora,
                fecha_expiracion=ahora + timedelta(hours=24),
                ip_solicitud=ip_address,
                usado=False,
            )

            try:
                AuditoriaOperaciones.objects.create(
                    usuario=empleado.usuario,
                    tipo_usuario="empleado",
                    id_usuario=empleado.id_empleado,
                    operacion="SOLICITAR_VERIFICACION_EMAIL",
                    tabla_afectada="Empleados",
                    ip_address=ip_address,
                    datos_nuevos={"email": empleado.email, "timestamp": str(ahora)},
                    fecha_operacion=ahora,
                    resultado="exitoso",
                )
            except Exception:
                pass

            return {"success": True, "token": token, "mensaje": "Token de verificacion generado"}

        except Exception as e:
            print(f"Error al generar token de verificacion: {str(e)}")
            return {"success": False, "mensaje": f"Error al generar token: {str(e)}"}

    @staticmethod
    @transaction.atomic
    def verificar_email(token: str, ip_address: str) -> Dict:
        """Verifica email de empleado usando token temporal."""
        try:
            token_hash = PasswordRecoveryService._hash_token(token)
            token_db = TokensRecuperacion.objects.filter(token_hash=token_hash).first()
            if not token_db or token_db.usado:
                return {"success": False, "mensaje": "Token invalido o expirado"}

            if token_db.fecha_expiracion <= timezone.now():
                return {"success": False, "mensaje": "Token invalido o expirado"}

            empleado = Empleados.objects.filter(email=token_db.id_cliente.email, estado=True).first()
            if not empleado:
                return {"success": False, "mensaje": "Empleado no disponible"}

            token_db.usado = True
            token_db.fecha_uso = timezone.now()
            token_db.save(update_fields=["usado", "fecha_uso"])

            try:
                AuditoriaOperaciones.objects.create(
                    usuario=empleado.usuario,
                    tipo_usuario="empleado",
                    id_usuario=empleado.id_empleado,
                    operacion="VERIFICAR_EMAIL",
                    tabla_afectada="Empleados",
                    ip_address=ip_address,
                    datos_nuevos={"email_verificado": True, "timestamp": str(timezone.now())},
                    fecha_operacion=timezone.now(),
                    resultado="exitoso",
                )
            except Exception:
                pass

            return {"success": True, "mensaje": "Email verificado exitosamente"}

        except Exception as e:
            print(f"Error al verificar email: {str(e)}")
            return {"success": False, "mensaje": f"Error al verificar email: {str(e)}"}

    @staticmethod
    @transaction.atomic
    def limpiar_tokens_expirados() -> Dict:
        """Elimina tokens expirados hace mas de 7 dias."""
        try:
            fecha_limite = timezone.now() - timedelta(days=7)
            qs = TokensRecuperacion.objects.filter(fecha_expiracion__lt=fecha_limite)
            eliminados = qs.count()
            qs.delete()

            return {
                "success": True,
                "tokens_eliminados": eliminados,
                "mensaje": f"{eliminados} tokens expirados eliminados",
            }
        except Exception as e:
            print(f"Error al limpiar tokens: {str(e)}")
            return {
                "success": False,
                "tokens_eliminados": 0,
                "mensaje": f"Error al limpiar tokens: {str(e)}",
            }
