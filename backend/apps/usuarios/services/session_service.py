"""
Servicio de gestion de sesiones empresariales.
Alineado con modelos actuales de usuarios.
"""

import json
from datetime import timedelta
from typing import Dict, List

from django.db import transaction
from django.utils import timezone

from apps.usuarios.models import (
    AuditoriaOperaciones,
    Empleados,
    PatronesAcceso,
    RenovacionesSesion,
    SesionesActivas,
)


class SessionService:
    """Servicio de gestion de sesiones con deteccion de patrones."""

    MAX_SESIONES_SIMULTANEAS = 3
    TIEMPO_EXPIRACION_HORAS = 24
    TIEMPO_INACTIVIDAD_MAXIMA_MINUTOS = 30
    RENOVACION_MINIMA_MINUTOS = 5

    @staticmethod
    @transaction.atomic
    def crear_sesion(empleado: Empleados, session_key: str, ip_address: str, user_agent: str = None) -> Dict:
        try:
            sesiones_activas = SesionesActivas.objects.filter(usuario=empleado.usuario, activa=True).count()
            sesiones_cerradas = 0

            if sesiones_activas >= SessionService.MAX_SESIONES_SIMULTANEAS:
                sesion_mas_antigua = (
                    SesionesActivas.objects.filter(usuario=empleado.usuario, activa=True)
                    .order_by("fecha_inicio")
                    .first()
                )
                if sesion_mas_antigua:
                    sesion_mas_antigua.activa = False
                    sesion_mas_antigua.save(update_fields=["activa"])
                    sesiones_cerradas = 1

            sesion = SesionesActivas.objects.create(
                usuario=empleado.usuario,
                tipo_usuario="empleado",
                session_key=session_key[:255],
                ip_address=ip_address,
                user_agent=user_agent[:1000] if user_agent else None,
                fecha_inicio=timezone.now(),
                ultima_actividad=timezone.now(),
                activa=True,
            )

            SessionService._analizar_patron_acceso(empleado, ip_address)

            AuditoriaOperaciones.objects.create(
                usuario=empleado.usuario,
                tipo_usuario="empleado",
                id_usuario=empleado.id_empleado,
                operacion="CREAR_SESION",
                tabla_afectada="SesionesActivas",
                ip_address=ip_address,
                datos_nuevos={
                    "id_sesion": sesion.id_sesion,
                    "sesiones_cerradas": sesiones_cerradas,
                    "timestamp": str(timezone.now()),
                },
                fecha_operacion=timezone.now(),
                resultado="exitoso",
            )

            return {
                "success": True,
                "sesion": sesion,
                "sesiones_cerradas": sesiones_cerradas,
                "mensaje": "Sesion creada exitosamente",
            }

        except Exception as e:
            print(f"Error al crear sesion: {str(e)}")
            return {"success": False, "mensaje": f"Error al crear sesion: {str(e)}"}

    @staticmethod
    @transaction.atomic
    def renovar_sesion(empleado: Empleados, session_key_actual: str, nuevo_session_key: str, ip_address: str) -> Dict:
        try:
            sesion_actual = SesionesActivas.objects.filter(
                usuario=empleado.usuario, session_key=session_key_actual[:255], activa=True
            ).first()
            if not sesion_actual:
                return {"success": False, "mensaje": "Sesion no encontrada o ya expirada"}

            ultima_renovacion = (
                RenovacionesSesion.objects.filter(usuario=empleado.usuario).order_by("-fecha_renovacion").first()
            )
            if ultima_renovacion:
                transcurrido = timezone.now() - ultima_renovacion.fecha_renovacion
                if transcurrido < timedelta(minutes=SessionService.RENOVACION_MINIMA_MINUTOS):
                    return {
                        "success": False,
                        "mensaje": f"Debe esperar al menos {SessionService.RENOVACION_MINIMA_MINUTOS} minutos entre renovaciones",
                    }

            nueva_sesion = SesionesActivas.objects.create(
                usuario=empleado.usuario,
                tipo_usuario="empleado",
                session_key=nuevo_session_key[:255],
                ip_address=sesion_actual.ip_address,
                user_agent=sesion_actual.user_agent,
                fecha_inicio=timezone.now(),
                ultima_actividad=timezone.now(),
                activa=True,
            )

            RenovacionesSesion.objects.create(
                usuario=empleado.usuario,
                session_key_anterior=session_key_actual[:255],
                session_key_nuevo=nuevo_session_key[:255],
                ip_address=ip_address,
                user_agent=sesion_actual.user_agent,
                fecha_renovacion=timezone.now(),
            )

            sesion_actual.activa = False
            sesion_actual.save(update_fields=["activa"])

            AuditoriaOperaciones.objects.create(
                usuario=empleado.usuario,
                tipo_usuario="empleado",
                id_usuario=empleado.id_empleado,
                operacion="RENOVAR_SESION",
                tabla_afectada="SesionesActivas",
                ip_address=ip_address,
                datos_nuevos={
                    "sesion_anterior": sesion_actual.id_sesion,
                    "sesion_nueva": nueva_sesion.id_sesion,
                    "timestamp": str(timezone.now()),
                },
                fecha_operacion=timezone.now(),
                resultado="exitoso",
            )

            return {"success": True, "sesion": nueva_sesion, "mensaje": "Sesion renovada exitosamente"}

        except Exception as e:
            print(f"Error al renovar sesion: {str(e)}")
            return {"success": False, "mensaje": f"Error al renovar sesion: {str(e)}"}

    @staticmethod
    @transaction.atomic
    def actualizar_actividad_sesion(empleado: Empleados, session_key: str) -> Dict:
        try:
            sesion = SesionesActivas.objects.filter(
                usuario=empleado.usuario, session_key=session_key[:255], activa=True
            ).first()
            if not sesion:
                return {"success": False, "mensaje": "Sesion no encontrada"}

            # Expiracion logica por antiguedad total de sesion.
            if timezone.now() > sesion.fecha_inicio + timedelta(hours=SessionService.TIEMPO_EXPIRACION_HORAS):
                sesion.activa = False
                sesion.save(update_fields=["activa"])
                return {"success": False, "mensaje": "Sesion expirada"}

            sesion.ultima_actividad = timezone.now()
            sesion.save(update_fields=["ultima_actividad"])
            return {"success": True, "mensaje": "Actividad actualizada"}

        except Exception as e:
            print(f"Error al actualizar actividad: {str(e)}")
            return {"success": False, "mensaje": f"Error al actualizar actividad: {str(e)}"}

    @staticmethod
    @transaction.atomic
    def cerrar_sesion(empleado: Empleados, session_key: str, ip_address: str) -> Dict:
        try:
            sesion = SesionesActivas.objects.filter(
                usuario=empleado.usuario, session_key=session_key[:255], activa=True
            ).first()
            if not sesion:
                return {"success": False, "mensaje": "Sesion no encontrada"}

            sesion.activa = False
            sesion.save(update_fields=["activa"])

            AuditoriaOperaciones.objects.create(
                usuario=empleado.usuario,
                tipo_usuario="empleado",
                id_usuario=empleado.id_empleado,
                operacion="CERRAR_SESION",
                tabla_afectada="SesionesActivas",
                ip_address=ip_address,
                datos_nuevos={"id_sesion": sesion.id_sesion, "timestamp": str(timezone.now())},
                fecha_operacion=timezone.now(),
                resultado="exitoso",
            )

            return {"success": True, "mensaje": "Sesion cerrada exitosamente"}

        except Exception as e:
            print(f"Error al cerrar sesion: {str(e)}")
            return {"success": False, "mensaje": f"Error al cerrar sesion: {str(e)}"}

    @staticmethod
    @transaction.atomic
    def cerrar_todas_sesiones(empleado: Empleados, ip_address: str, excepto_session_key: str = None) -> Dict:
        try:
            sesiones = SesionesActivas.objects.filter(usuario=empleado.usuario, activa=True)
            if excepto_session_key:
                sesiones = sesiones.exclude(session_key=excepto_session_key[:255])

            num_sesiones = sesiones.count()
            sesiones.update(activa=False)

            AuditoriaOperaciones.objects.create(
                usuario=empleado.usuario,
                tipo_usuario="empleado",
                id_usuario=empleado.id_empleado,
                operacion="CERRAR_TODAS_SESIONES",
                tabla_afectada="SesionesActivas",
                ip_address=ip_address,
                datos_nuevos={"sesiones_cerradas": num_sesiones, "timestamp": str(timezone.now())},
                fecha_operacion=timezone.now(),
                resultado="exitoso",
            )

            return {
                "success": True,
                "sesiones_cerradas": num_sesiones,
                "mensaje": f"{num_sesiones} sesion(es) cerrada(s) exitosamente",
            }

        except Exception as e:
            print(f"Error al cerrar sesiones: {str(e)}")
            return {"success": False, "mensaje": f"Error al cerrar sesiones: {str(e)}"}

    @staticmethod
    def listar_sesiones_activas(empleado: Empleados) -> List[Dict]:
        sesiones = SesionesActivas.objects.filter(usuario=empleado.usuario, activa=True).order_by("-ultima_actividad")
        resultado = []
        for sesion in sesiones:
            tiempo_inactivo = timezone.now() - sesion.ultima_actividad
            resultado.append(
                {
                    "id": sesion.id_sesion,
                    "ip_address": sesion.ip_address,
                    "user_agent": sesion.user_agent,
                    "fecha_inicio": sesion.fecha_inicio,
                    "ultima_actividad": sesion.ultima_actividad,
                    "tiempo_inactivo_minutos": int(tiempo_inactivo.total_seconds() / 60),
                    "es_sesion_actual": False,
                }
            )
        return resultado

    @staticmethod
    def _analizar_patron_acceso(empleado: Empleados, ip_address: str) -> None:
        try:
            patron = PatronesAcceso.objects.filter(usuario=empleado.usuario, ip_address=ip_address).first()
            hora_actual = timezone.now().time()
            dia_semana = timezone.now().weekday()

            if patron:
                patron.frecuencia_accesos = (patron.frecuencia_accesos or 0) + 1
                patron.es_habitual = 1 if patron.frecuencia_accesos >= 5 else 0
                patron.ultima_deteccion = timezone.now()
                patron.horario_inicio = patron.horario_inicio or hora_actual
                patron.horario_fin = hora_actual
                if patron.dias_semana:
                    dias = json.loads(patron.dias_semana)
                    if dia_semana not in dias:
                        dias.append(dia_semana)
                    patron.dias_semana = json.dumps(dias)
                else:
                    patron.dias_semana = json.dumps([dia_semana])
                patron.save()
            else:
                PatronesAcceso.objects.create(
                    usuario=empleado.usuario,
                    tipo_usuario="empleado",
                    ip_address=ip_address,
                    horario_inicio=hora_actual,
                    horario_fin=hora_actual,
                    dias_semana=json.dumps([dia_semana]),
                    primera_deteccion=timezone.now(),
                    ultima_deteccion=timezone.now(),
                    frecuencia_accesos=1,
                    es_habitual=0,
                )
        except Exception as e:  # pragma: no cover
            print(f"Error al analizar patron de acceso: {str(e)}")

    @staticmethod
    def detectar_acceso_inusual(empleado: Empleados, ip_address: str) -> Dict:
        razones = []

        # Sin historial previo no se considera inusual.
        if not PatronesAcceso.objects.filter(usuario=empleado.usuario).exists():
            return {"es_inusual": False, "razones": [], "nivel_riesgo": "bajo"}

        patron_ip = PatronesAcceso.objects.filter(
            usuario=empleado.usuario, ip_address=ip_address, es_habitual=1
        ).first()
        if not patron_ip:
            accesos_total_ip = SesionesActivas.objects.filter(usuario=empleado.usuario, ip_address=ip_address).count()
            if accesos_total_ip == 0:
                razones.append("Nueva IP")
            else:
                razones.append("IP no habitual")
        else:
            return {"es_inusual": False, "razones": [], "nivel_riesgo": "bajo"}

        patrones_habituales = PatronesAcceso.objects.filter(usuario=empleado.usuario, es_habitual=1)
        if patrones_habituales.exists():
            hora_actual = timezone.now().time()
            base = patrones_habituales.first()
            if base.horario_inicio:
                diferencia_horas = abs(hora_actual.hour - base.horario_inicio.hour)
                if diferencia_horas > 4:
                    razones.append("Horario de acceso inusual")

        nivel_riesgo = "bajo"
        if len(razones) >= 2:
            nivel_riesgo = "alto"
        elif len(razones) == 1:
            nivel_riesgo = "medio"

        return {"es_inusual": len(razones) > 0, "razones": razones, "nivel_riesgo": nivel_riesgo}

    @staticmethod
    @transaction.atomic
    def limpiar_sesiones_expiradas() -> Dict:
        try:
            ahora = timezone.now()
            limite_inactividad = ahora - timedelta(minutes=SessionService.TIEMPO_INACTIVIDAD_MAXIMA_MINUTOS)
            limite_antiguedad = ahora - timedelta(hours=SessionService.TIEMPO_EXPIRACION_HORAS)

            sesiones_expiradas = SesionesActivas.objects.filter(activa=True, fecha_inicio__lt=limite_antiguedad)
            num_expiradas = sesiones_expiradas.count()
            sesiones_expiradas.update(activa=False)

            sesiones_inactivas = SesionesActivas.objects.filter(activa=True, ultima_actividad__lt=limite_inactividad)
            num_inactivas = sesiones_inactivas.count()
            sesiones_inactivas.update(activa=False)

            total = num_expiradas + num_inactivas
            return {
                "success": True,
                "sesiones_cerradas": total,
                "sesiones_expiradas": num_expiradas,
                "sesiones_inactivas": num_inactivas,
                "mensaje": f"{total} sesiones cerradas ({num_expiradas} expiradas, {num_inactivas} inactivas)",
            }
        except Exception as e:
            print(f"Error al limpiar sesiones: {str(e)}")
            return {
                "success": False,
                "sesiones_cerradas": 0,
                "sesiones_expiradas": 0,
                "sesiones_inactivas": 0,
                "mensaje": f"Error al limpiar sesiones: {str(e)}",
            }
