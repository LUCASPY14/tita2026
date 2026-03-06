"""
Servicio de gestión de sesiones empresariales
Maneja sesiones activas, renovaciones, detección de patrones sospechosos
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib
import secrets

from django.db import transaction
from django.utils import timezone

from apps.usuarios.models import (
    Empleados,
    SesionesActivas,
    RenovacionesSesion,
    PatronesAcceso,
    AuditoriaOperaciones,
)


class SessionService:
    """
    Servicio de gestión de sesiones con análisis de patrones de acceso.
    """

    # Configuración
    MAX_SESIONES_SIMULTANEAS = 3
    TIEMPO_EXPIRACION_HORAS = 24
    TIEMPO_INACTIVIDAD_MAXIMA_MINUTOS = 30
    RENOVACION_MINIMA_MINUTOS = 5

    @staticmethod
    @transaction.atomic
    def crear_sesion(
        empleado: Empleados, session_key: str, ip_address: str, user_agent: str = None
    ) -> Dict:
        """
        Crea una nueva sesión para un empleado.

        Returns:
            {
                'success': bool,
                'sesion': SesionesActivas,
                'sesiones_cerradas': int,
                'mensaje': str
            }
        """
        try:
            # Verificar número de sesiones activas
            sesiones_activas = SesionesActivas.objects.filter(
                id_empleado=empleado, activa=True
            ).count()

            sesiones_cerradas = 0

            if sesiones_activas >= SessionService.MAX_SESIONES_SIMULTANEAS:
                # Cerrar la sesión más antigua
                sesion_mas_antigua = (
                    SesionesActivas.objects.filter(id_empleado=empleado, activa=True)
                    .order_by("fecha_inicio")
                    .first()
                )

                if sesion_mas_antigua:
                    sesion_mas_antigua.activa = False
                    sesion_mas_antigua.fecha_cierre = timezone.now()
                    sesion_mas_antigua.save()
                    sesiones_cerradas = 1

            # Crear nueva sesión
            sesion = SesionesActivas.objects.create(
                id_empleado=empleado,
                session_key=session_key[:255],
                ip_address=ip_address,
                user_agent=user_agent[:500] if user_agent else None,
                fecha_inicio=timezone.now(),
                fecha_ultima_actividad=timezone.now(),
                fecha_expiracion=timezone.now()
                + timedelta(hours=SessionService.TIEMPO_EXPIRACION_HORAS),
                activa=True,
            )

            # Analizar patrón de acceso
            SessionService._analizar_patron_acceso(empleado, ip_address)

            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                id_empleado=empleado,
                operacion="CREAR_SESION",
                tabla_afectada="SesionesActivas",
                ip_origen=ip_address,
                datos_nuevos={
                    "id_sesion": sesion.id,
                    "sesiones_cerradas": sesiones_cerradas,
                    "timestamp": str(timezone.now()),
                },
            )

            return {
                "success": True,
                "sesion": sesion,
                "sesiones_cerradas": sesiones_cerradas,
                "mensaje": "Sesión creada exitosamente",
            }

        except Exception as e:
            print(f"Error al crear sesión: {str(e)}")
            return {"success": False, "mensaje": f"Error al crear sesión: {str(e)}"}

    @staticmethod
    @transaction.atomic
    def renovar_sesion(
        empleado: Empleados, session_key_actual: str, nuevo_session_key: str, ip_address: str
    ) -> Dict:
        """
        Renueva una sesión existente (rotación de tokens).

        Returns:
            {'success': bool, 'sesion': SesionesActivas, 'mensaje': str}
        """
        try:
            # Buscar sesión actual
            sesion_actual = SesionesActivas.objects.filter(
                id_empleado=empleado, session_key=session_key_actual[:255], activa=True
            ).first()

            if not sesion_actual:
                return {"success": False, "mensaje": "Sesión no encontrada o ya expirada"}

            # Verificar si ha pasado suficiente tiempo desde la última renovación
            ultima_renovacion = (
                RenovacionesSesion.objects.filter(session_key_anterior=session_key_actual[:255])
                .order_by("-fecha_renovacion")
                .first()
            )

            if ultima_renovacion:
                tiempo_transcurrido = timezone.now() - ultima_renovacion.fecha_renovacion
                if tiempo_transcurrido < timedelta(
                    minutes=SessionService.RENOVACION_MINIMA_MINUTOS
                ):
                    return {
                        "success": False,
                        "mensaje": f"Debe esperar al menos {SessionService.RENOVACION_MINIMA_MINUTOS} minutos entre renovaciones",
                    }

            # Crear nueva sesión
            nueva_sesion = SesionesActivas.objects.create(
                id_empleado=empleado,
                session_key=nuevo_session_key[:255],
                ip_address=sesion_actual.ip_address,
                user_agent=sesion_actual.user_agent,
                fecha_inicio=timezone.now(),
                fecha_ultima_actividad=timezone.now(),
                fecha_expiracion=timezone.now()
                + timedelta(hours=SessionService.TIEMPO_EXPIRACION_HORAS),
                activa=True,
            )

            # Registrar renovación
            RenovacionesSesion.objects.create(
                id_empleado=empleado,
                session_key_anterior=session_key_actual[:255],
                session_key_nuevo=nuevo_session_key[:255],
                fecha_renovacion=timezone.now(),
                ip_address=ip_address,
            )

            # Invalidar sesión anterior
            sesion_actual.activa = False
            sesion_actual.fecha_cierre = timezone.now()
            sesion_actual.save()

            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                id_empleado=empleado,
                operacion="RENOVAR_SESION",
                tabla_afectada="SesionesActivas",
                ip_origen=ip_address,
                datos_nuevos={
                    "sesion_anterior": sesion_actual.id,
                    "sesion_nueva": nueva_sesion.id,
                    "timestamp": str(timezone.now()),
                },
            )

            return {
                "success": True,
                "sesion": nueva_sesion,
                "mensaje": "Sesión renovada exitosamente",
            }

        except Exception as e:
            print(f"Error al renovar sesión: {str(e)}")
            return {"success": False, "mensaje": f"Error al renovar sesión: {str(e)}"}

    @staticmethod
    @transaction.atomic
    def actualizar_actividad_sesion(empleado: Empleados, session_key: str) -> Dict:
        """
        Actualiza la última actividad de una sesión.

        Returns:
            {'success': bool, 'mensaje': str}
        """
        try:
            sesion = SesionesActivas.objects.filter(
                id_empleado=empleado, session_key=session_key[:255], activa=True
            ).first()

            if not sesion:
                return {"success": False, "mensaje": "Sesión no encontrada"}

            # Verificar si la sesión ha expirado
            if timezone.now() > sesion.fecha_expiracion:
                sesion.activa = False
                sesion.fecha_cierre = timezone.now()
                sesion.save()
                return {"success": False, "mensaje": "Sesión expirada"}

            # Actualizar última actividad
            sesion.fecha_ultima_actividad = timezone.now()
            sesion.save()

            return {"success": True, "mensaje": "Actividad actualizada"}

        except Exception as e:
            print(f"Error al actualizar actividad: {str(e)}")
            return {"success": False, "mensaje": f"Error al actualizar actividad: {str(e)}"}

    @staticmethod
    @transaction.atomic
    def cerrar_sesion(empleado: Empleados, session_key: str, ip_address: str) -> Dict:
        """
        Cierra una sesión específica.

        Returns:
            {'success': bool, 'mensaje': str}
        """
        try:
            sesion = SesionesActivas.objects.filter(
                id_empleado=empleado, session_key=session_key[:255], activa=True
            ).first()

            if not sesion:
                return {"success": False, "mensaje": "Sesión no encontrada"}

            sesion.activa = False
            sesion.fecha_cierre = timezone.now()
            sesion.save()

            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                id_empleado=empleado,
                operacion="CERRAR_SESION",
                tabla_afectada="SesionesActivas",
                ip_origen=ip_address,
                datos_nuevos={"id_sesion": sesion.id, "timestamp": str(timezone.now())},
            )

            return {"success": True, "mensaje": "Sesión cerrada exitosamente"}

        except Exception as e:
            print(f"Error al cerrar sesión: {str(e)}")
            return {"success": False, "mensaje": f"Error al cerrar sesión: {str(e)}"}

    @staticmethod
    @transaction.atomic
    def cerrar_todas_sesiones(
        empleado: Empleados, ip_address: str, excepto_session_key: str = None
    ) -> Dict:
        """
        Cierra todas las sesiones de un empleado.

        Args:
            excepto_session_key: Si se proporciona, no cierra esta sesión (útil para "cerrar otras sesiones")

        Returns:
            {'success': bool, 'sesiones_cerradas': int, 'mensaje': str}
        """
        try:
            sesiones = SesionesActivas.objects.filter(id_empleado=empleado, activa=True)

            if excepto_session_key:
                sesiones = sesiones.exclude(session_key=excepto_session_key[:255])

            num_sesiones = sesiones.count()

            sesiones.update(activa=False, fecha_cierre=timezone.now())

            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                id_empleado=empleado,
                operacion="CERRAR_TODAS_SESIONES",
                tabla_afectada="SesionesActivas",
                ip_origen=ip_address,
                datos_nuevos={"sesiones_cerradas": num_sesiones, "timestamp": str(timezone.now())},
            )

            return {
                "success": True,
                "sesiones_cerradas": num_sesiones,
                "mensaje": f"{num_sesiones} sesión(es) cerrada(s) exitosamente",
            }

        except Exception as e:
            print(f"Error al cerrar sesiones: {str(e)}")
            return {"success": False, "mensaje": f"Error al cerrar sesiones: {str(e)}"}

    @staticmethod
    def listar_sesiones_activas(empleado: Empleados) -> List[Dict]:
        """
        Lista todas las sesiones activas de un empleado.

        Returns:
            Lista de diccionarios con información de sesiones
        """
        sesiones = SesionesActivas.objects.filter(id_empleado=empleado, activa=True).order_by(
            "-fecha_ultima_actividad"
        )

        resultado = []
        for sesion in sesiones:
            tiempo_inactivo = timezone.now() - sesion.fecha_ultima_actividad

            resultado.append(
                {
                    "id": sesion.id,
                    "ip_address": sesion.ip_address,
                    "user_agent": sesion.user_agent,
                    "fecha_inicio": sesion.fecha_inicio,
                    "fecha_ultima_actividad": sesion.fecha_ultima_actividad,
                    "fecha_expiracion": sesion.fecha_expiracion,
                    "tiempo_inactivo_minutos": int(tiempo_inactivo.total_seconds() / 60),
                    "es_sesion_actual": False,  # Se puede marcar desde el frontend
                }
            )

        return resultado

    @staticmethod
    def _analizar_patron_acceso(empleado: Empleados, ip_address: str) -> None:
        """
        Analiza y registra patrones de acceso del empleado.
        Identifica IPs habituales y horarios de acceso.
        """
        try:
            # Buscar patrón existente para esta IP
            patron = PatronesAcceso.objects.filter(
                id_empleado=empleado, ip_address=ip_address
            ).first()

            hora_actual = timezone.now().hour
            dia_semana = timezone.now().weekday()  # 0 = Lunes, 6 = Domingo

            if patron:
                # Actualizar patrón existente
                accesos_desde_ip = SesionesActivas.objects.filter(
                    id_empleado=empleado, ip_address=ip_address
                ).count()

                # Considerar habitual si tiene más de 5 accesos desde esta IP
                patron.es_habitual = accesos_desde_ip > 5
                patron.ultimo_acceso = timezone.now()

                # Actualizar horario habitual (promedio simple)
                if patron.horario_habitual:
                    patron.horario_habitual = (patron.horario_habitual + hora_actual) // 2
                else:
                    patron.horario_habitual = hora_actual

                # Actualizar días de la semana (lista JSON)
                if patron.dias_semana_habituales:
                    import json

                    dias = json.loads(patron.dias_semana_habituales)
                    if dia_semana not in dias:
                        dias.append(dia_semana)
                    patron.dias_semana_habituales = json.dumps(dias)
                else:
                    import json

                    patron.dias_semana_habituales = json.dumps([dia_semana])

                patron.save()
            else:
                # Crear nuevo patrón
                import json

                PatronesAcceso.objects.create(
                    id_empleado=empleado,
                    ip_address=ip_address,
                    horario_habitual=hora_actual,
                    dias_semana_habituales=json.dumps([dia_semana]),
                    es_habitual=False,
                    primer_acceso=timezone.now(),
                    ultimo_acceso=timezone.now(),
                )

        except Exception as e:
            print(f"Error al analizar patrón de acceso: {str(e)}")

    @staticmethod
    def detectar_acceso_inusual(empleado: Empleados, ip_address: str) -> Dict:
        """
        Detecta si un acceso es inusual basado en patrones históricos.

        Returns:
            {
                'es_inusual': bool,
                'razones': List[str],
                'nivel_riesgo': str  # 'bajo', 'medio', 'alto'
            }
        """
        razones = []

        # Verificar si la IP es habitual
        patron_ip = PatronesAcceso.objects.filter(
            id_empleado=empleado, ip_address=ip_address, es_habitual=True
        ).first()

        if not patron_ip:
            # IP no habitual
            accesos_total_ip = SesionesActivas.objects.filter(
                id_empleado=empleado, ip_address=ip_address
            ).count()

            if accesos_total_ip == 0:
                razones.append("Primera vez que accede desde esta IP")
            else:
                razones.append("IP no habitual (menos de 5 accesos históricos)")

        # Verificar horario
        hora_actual = timezone.now().hour
        patrones = PatronesAcceso.objects.filter(id_empleado=empleado, es_habitual=True)

        if patrones.exists():
            horarios_habituales = [p.horario_habitual for p in patrones if p.horario_habitual]
            if horarios_habituales:
                horario_promedio = sum(horarios_habituales) / len(horarios_habituales)
                diferencia = abs(hora_actual - horario_promedio)

                if diferencia > 4:  # Más de 4 horas de diferencia
                    razones.append(
                        f"Horario inusual (normalmente accede alrededor de las {int(horario_promedio)}:00)"
                    )

        # Verificar día de la semana
        dia_actual = timezone.now().weekday()
        if patrones.exists():
            import json

            for patron in patrones:
                if patron.dias_semana_habituales:
                    dias_habituales = json.loads(patron.dias_semana_habituales)
                    if dia_actual not in dias_habituales:
                        dias_nombres = [
                            "Lunes",
                            "Martes",
                            "Miércoles",
                            "Jueves",
                            "Viernes",
                            "Sábado",
                            "Domingo",
                        ]
                        razones.append(
                            f"Día inusual (normalmente no accede los {dias_nombres[dia_actual]})"
                        )
                        break

        # Determinar nivel de riesgo
        nivel_riesgo = "bajo"
        if len(razones) >= 2:
            nivel_riesgo = "alto"
        elif len(razones) == 1:
            nivel_riesgo = "medio"

        return {"es_inusual": len(razones) > 0, "razones": razones, "nivel_riesgo": nivel_riesgo}

    @staticmethod
    @transaction.atomic
    def limpiar_sesiones_expiradas() -> Dict:
        """
        Limpia sesiones expiradas o inactivas.
        Debe ejecutarse periódicamente (ej: cada hora con cron job).

        Returns:
            {'sesiones_cerradas': int, 'mensaje': str}
        """
        try:
            # Cerrar sesiones expiradas por fecha
            sesiones_expiradas = SesionesActivas.objects.filter(
                activa=True, fecha_expiracion__lt=timezone.now()
            )

            num_expiradas = sesiones_expiradas.count()
            sesiones_expiradas.update(activa=False, fecha_cierre=timezone.now())

            # Cerrar sesiones inactivas
            tiempo_limite_inactividad = timezone.now() - timedelta(
                minutes=SessionService.TIEMPO_INACTIVIDAD_MAXIMA_MINUTOS
            )

            sesiones_inactivas = SesionesActivas.objects.filter(
                activa=True, fecha_ultima_actividad__lt=tiempo_limite_inactividad
            )

            num_inactivas = sesiones_inactivas.count()
            sesiones_inactivas.update(activa=False, fecha_cierre=timezone.now())

            total = num_expiradas + num_inactivas

            return {
                "sesiones_cerradas": total,
                "sesiones_expiradas": num_expiradas,
                "sesiones_inactivas": num_inactivas,
                "mensaje": f"{total} sesiones cerradas ({num_expiradas} expiradas, {num_inactivas} inactivas)",
            }

        except Exception as e:
            print(f"Error al limpiar sesiones: {str(e)}")
            return {"sesiones_cerradas": 0, "mensaje": f"Error al limpiar sesiones: {str(e)}"}
