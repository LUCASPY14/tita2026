"""
Views para app de Notificaciones
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta

from .models import (
    NotificacionesPortal,
    NotificacionesSaldo,
    AlertasSistema,
    PreferenciasNotificacion
)
from .serializers import (
    NotificacionPortalSerializer,
    NotificacionSaldoSerializer,
    AlertaSistemaSerializer,
    PreferenciasNotificacionSerializer
)


class NotificacionesPortalViewSet(viewsets.ModelViewSet):
    """ViewSet para notificaciones del portal"""
    queryset = NotificacionesPortal.objects.all()
    serializer_class = NotificacionPortalSerializer
    
    def get_queryset(self):
        queryset = NotificacionesPortal.objects.all().order_by('-fecha_envio')
        
        # Filtros opcionales
        leida = self.request.query_params.get('leida', None)
        tipo = self.request.query_params.get('tipo', None)
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        
        if leida is not None:
            queryset = queryset.filter(leida=1 if leida.lower() == 'true' else 0)
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        if fecha_desde:
            try:
                fecha = datetime.fromisoformat(fecha_desde.replace('Z', '+00:00'))
                queryset = queryset.filter(fecha_envio__gte=fecha)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha = datetime.fromisoformat(fecha_hasta.replace('Z', '+00:00'))
                queryset = queryset.filter(fecha_envio__lte=fecha)
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def marcar_leida(self, request, pk=None):
        """Marca una notificación como leída"""
        try:
            notificacion = self.get_object()
            notificacion.leida = 1
            notificacion.fecha_lectura = timezone.now()
            notificacion.save()
            
            serializer = self.get_serializer(notificacion)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def marcar_todas_leidas(self, request):
        """Marca todas las notificaciones no leídas como leídas"""
        try:
            id_usuario = request.data.get('id_usuario_portal')
            if not id_usuario:
                return Response(
                    {'error': 'id_usuario_portal es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            NotificacionesPortal.objects.filter(
                id_usuario_portal=id_usuario,
                leida=0
            ).update(
                leida=1,
                fecha_lectura=timezone.now()
            )
            
            return Response({'success': True, 'mensaje': 'Notificaciones marcadas como leídas'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Obtiene un resumen de las notificaciones"""
        try:
            id_usuario = request.query_params.get('id_usuario_portal')
            if not id_usuario:
                return Response(
                    {'error': 'id_usuario_portal es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            queryset = NotificacionesPortal.objects.filter(id_usuario_portal=id_usuario)
            total = queryset.count()
            no_leidas = queryset.filter(leida=0).count()
            hoy = timezone.now().date()
            notificaciones_hoy = queryset.filter(fecha_envio__date=hoy).count()
            
            # Contar alertas críticas del sistema
            alertas_criticas = AlertasSistema.objects.filter(
                Q(estado='Pendiente') | Q(estado__isnull=True),
                tipo='critico'
            ).count()
            
            # Contar notificaciones de saldo
            notificaciones_saldo = NotificacionesSaldo.objects.filter(leida=0).count()
            
            # Contar alertas del sistema
            alertas_sistema = AlertasSistema.objects.filter(
                Q(estado='Pendiente') | Q(estado__isnull=True)
            ).count()
            
            return Response({
                'total_notificaciones': total,
                'no_leidas': no_leidas,
                'notificaciones_hoy': notificaciones_hoy,
                'alertas_criticas': alertas_criticas,
                'notificaciones_saldo': notificaciones_saldo,
                'alertas_sistema': alertas_sistema
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class NotificacionesSaldoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para notificaciones de saldo (solo lectura)"""
    queryset = NotificacionesSaldo.objects.all()
    serializer_class = NotificacionSaldoSerializer
    
    def get_queryset(self):
        queryset = NotificacionesSaldo.objects.select_related(
            'nro_tarjeta',
            'nro_tarjeta__id_hijo'
        ).order_by('-fecha_creacion')
        
        # Filtros opcionales
        nro_tarjeta = self.request.query_params.get('nro_tarjeta', None)
        tipo = self.request.query_params.get('tipo_notificacion', None)
        
        if nro_tarjeta:
            queryset = queryset.filter(nro_tarjeta=nro_tarjeta)
        
        if tipo:
            queryset = queryset.filter(tipo_notificacion=tipo)
        
        return queryset


class AlertasSistemaViewSet(viewsets.ModelViewSet):
    """ViewSet para alertas del sistema"""
    queryset = AlertasSistema.objects.all()
    serializer_class = AlertaSistemaSerializer
    
    def get_queryset(self):
        queryset = AlertasSistema.objects.all().order_by('-fecha_creacion')
        
        # Filtros opcionales
        estado = self.request.query_params.get('estado', None)
        tipo = self.request.query_params.get('tipo', None)
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        if fecha_desde:
            try:
                fecha = datetime.fromisoformat(fecha_desde.replace('Z', '+00:00'))
                queryset = queryset.filter(fecha_creacion__gte=fecha)
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):
        """Resuelve una alerta del sistema"""
        try:
            alerta = self.get_object()
            observaciones = request.data.get('observaciones', '')
            id_empleado = request.data.get('id_empleado_resuelve')
            
            alerta.estado = 'Resuelta'
            alerta.fecha_resolucion = timezone.now()
            alerta.observaciones = observaciones
            if id_empleado:
                alerta.id_empleado_resuelve = id_empleado
            alerta.save()
            
            serializer = self.get_serializer(alerta)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PreferenciasNotificacionViewSet(viewsets.ModelViewSet):
    """ViewSet para preferencias de notificación"""
    queryset = PreferenciasNotificacion.objects.all()
    serializer_class = PreferenciasNotificacionSerializer
    
    @action(detail=False, methods=['get'])
    def obtener_preferencias(self, request):
        """Obtiene las preferencias de un usuario"""
        try:
            id_usuario = request.query_params.get('id_usuario_portal')
            if not id_usuario:
                return Response(
                    {'error': 'id_usuario_portal es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            preferencias = PreferenciasNotificacion.objects.filter(
                id_usuario_portal=id_usuario
            )
            serializer = self.get_serializer(preferencias, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def actualizar_preferencias(self, request):
        """Actualiza o crea preferencias de notificación"""
        try:
            id_usuario = request.data.get('id_usuario_portal')
            tipo_notificacion = request.data.get('tipo_notificacion')
            email_activo = request.data.get('email_activo', 1)
            push_activo = request.data.get('push_activo', 1)
            
            if not id_usuario or not tipo_notificacion:
                return Response(
                    {'error': 'id_usuario_portal y tipo_notificacion son requeridos'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            preferencia, created = PreferenciasNotificacion.objects.update_or_create(
                id_usuario_portal_id=id_usuario,
                tipo_notificacion=tipo_notificacion,
                defaults={
                    'email_activo': 1 if email_activo else 0,
                    'push_activo': 1 if push_activo else 0,
                    'actualizado_en': timezone.now()
                }
            )
            
            serializer = self.get_serializer(preferencia)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
