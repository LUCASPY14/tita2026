import {
  esAlertaRelevante,
  esNotificacionRelevante,
  filtrarAlertasPorRol,
  filtrarNotificacionesPorRol,
  getCriticidadNivel,
  ordenarAlertasPorCriticidad,
  enriquecerAlertas,
  obtenerResumenCriticidad,
  ALERTAS_CONFIG,
  NOTIFICACIONES_CONFIG,
} from './notificationFilters';
import type { AlertaSistema, NotificacionPortal } from '../types';

describe('notificationFilters', () => {
  // Mock data
  const mockAlertaCritica: AlertaSistema = {
    id_alerta: 1,
    tipo: 'Sistema Caído',
    mensaje: 'El sistema no responde',
    fecha_creacion: '2024-03-01T10:00:00Z',
    estado: 'Pendiente',
    criticidad: 'critico',
    roles_objetivo: ['admin', 'gerente'],
  };

  const mockAlertaStockBajo: AlertaSistema = {
    id_alerta: 2,
    tipo: 'Stock Bajo',
    mensaje: 'Producto con stock bajo',
    fecha_creacion: '2024-03-01T11:00:00Z',
    estado: 'Pendiente',
    criticidad: 'medio',
  };

  const mockAlertaRecordatorio: AlertaSistema = {
    id_alerta: 3,
    tipo: 'Recordatorio',
    mensaje: 'Recordatorio general',
    fecha_creacion: '2024-03-01T12:00:00Z',
    estado: 'Pendiente',
    criticidad: 'bajo',
  };

  const mockNotificacionVenta: NotificacionPortal = {
    id_notificacion: 1,
    tipo: 'Nueva Venta',
    titulo: 'Venta registrada',
    mensaje: 'Nueva venta realizada',
    leida: false,
    fecha_envio: '2024-03-01T10:00:00Z',
    creado_en: '2024-03-01T10:00:00Z',
    id_usuario_portal: 1,
  };

  const mockNotificacionReporte: NotificacionPortal = {
    id_notificacion: 2,
    tipo: 'Reporte Generado',
    titulo: 'Reporte listo',
    mensaje: 'El reporte está disponible',
    leida: false,
    fecha_envio: '2024-03-01T11:00:00Z',
    creado_en: '2024-03-01T11:00:00Z',
    id_usuario_portal: 1,
  };

  describe('esAlertaRelevante', () => {
    test('admin debe ver alerta crítica', () => {
      expect(esAlertaRelevante(mockAlertaCritica, 'admin')).toBe(true);
    });

    test('gerente debe ver alerta crítica', () => {
      expect(esAlertaRelevante(mockAlertaCritica, 'gerente')).toBe(true);
    });

    test('cajero NO debe ver alerta crítica del sistema', () => {
      expect(esAlertaRelevante(mockAlertaCritica, 'cajero')).toBe(false);
    });

    test('empleado NO debe ver alerta crítica', () => {
      expect(esAlertaRelevante(mockAlertaCritica, 'empleado')).toBe(false);
    });

    test('cajero debe ver alerta de stock bajo', () => {
      expect(esAlertaRelevante(mockAlertaStockBajo, 'cajero')).toBe(true);
    });

    test('empleado debe ver recordatorios', () => {
      expect(esAlertaRelevante(mockAlertaRecordatorio, 'empleado')).toBe(true);
    });

    test('alerta sin config debe mostrarse solo a admin y gerente', () => {
      const alertaSinConfig: AlertaSistema = {
        ...mockAlertaCritica,
        tipo: 'Tipo Desconocido',
        roles_objetivo: undefined,
      };
      expect(esAlertaRelevante(alertaSinConfig, 'admin')).toBe(true);
      expect(esAlertaRelevante(alertaSinConfig, 'gerente')).toBe(true);
      expect(esAlertaRelevante(alertaSinConfig, 'cajero')).toBe(false);
    });
  });

  describe('esNotificacionRelevante', () => {
    test('cajero debe ver notificación de venta', () => {
      expect(esNotificacionRelevante(mockNotificacionVenta, 'cajero')).toBe(true);
    });

    test('empleado NO debe ver notificación de venta', () => {
      expect(esNotificacionRelevante(mockNotificacionVenta, 'empleado')).toBe(false);
    });

    test('gerente debe ver notificación de reporte', () => {
      expect(esNotificacionRelevante(mockNotificacionReporte, 'gerente')).toBe(true);
    });

    test('cajero NO debe ver notificación de reporte', () => {
      expect(esNotificacionRelevante(mockNotificacionReporte, 'cajero')).toBe(false);
    });

    test('notificación sin config debe mostrarse a todos', () => {
      const notifSinConfig: NotificacionPortal = {
        ...mockNotificacionVenta,
        tipo: 'Tipo Desconocido',
      };
      expect(esNotificacionRelevante(notifSinConfig, 'admin')).toBe(true);
      expect(esNotificacionRelevante(notifSinConfig, 'empleado')).toBe(true);
    });
  });

  describe('filtrarAlertasPorRol', () => {
    const alertas = [mockAlertaCritica, mockAlertaStockBajo, mockAlertaRecordatorio];

    test('admin debe ver todas las alertas', () => {
      const filtradas = filtrarAlertasPorRol(alertas, 'admin');
      expect(filtradas).toHaveLength(3);
    });

    test('cajero debe ver solo stock bajo y recordatorio', () => {
      const filtradas = filtrarAlertasPorRol(alertas, 'cajero');
      expect(filtradas).toHaveLength(2);
      expect(filtradas.find(a => a.id_alerta === 2)).toBeDefined(); // Stock Bajo
      expect(filtradas.find(a => a.id_alerta === 3)).toBeDefined(); // Recordatorio
    });

    test('empleado debe ver solo recordatorio', () => {
      const filtradas = filtrarAlertasPorRol(alertas, 'empleado');
      expect(filtradas).toHaveLength(1);
      expect(filtradas[0].tipo).toBe('Recordatorio');
    });
  });

  describe('filtrarNotificacionesPorRol', () => {
    const notificaciones = [mockNotificacionVenta, mockNotificacionReporte];

    test('admin debe ver todas las notificaciones', () => {
      const filtradas = filtrarNotificacionesPorRol(notificaciones, 'admin');
      expect(filtradas).toHaveLength(2);
    });

    test('gerente debe ver todas las notificaciones', () => {
      const filtradas = filtrarNotificacionesPorRol(notificaciones, 'gerente');
      expect(filtradas).toHaveLength(2);
    });

    test('cajero debe ver solo venta', () => {
      const filtradas = filtrarNotificacionesPorRol(notificaciones, 'cajero');
      expect(filtradas).toHaveLength(1);
      expect(filtradas[0].tipo).toBe('Nueva Venta');
    });

    test('empleado no debe ver ninguna notificación específica', () => {
      const filtradas = filtrarNotificacionesPorRol(notificaciones, 'empleado');
      expect(filtradas).toHaveLength(0);
    });
  });

  describe('getCriticidadNivel', () => {
    test('debe retornar nivel 4 para crítico', () => {
      expect(getCriticidadNivel('critico')).toBe(4);
    });

    test('debe retornar nivel 3 para alto', () => {
      expect(getCriticidadNivel('alto')).toBe(3);
    });

    test('debe retornar nivel 2 para medio', () => {
      expect(getCriticidadNivel('medio')).toBe(2);
    });

    test('debe retornar nivel 1 para bajo', () => {
      expect(getCriticidadNivel('bajo')).toBe(1);
    });

    test('debe retornar 0 para criticidad desconocida', () => {
      expect(getCriticidadNivel('desconocido')).toBe(0);
    });
  });

  describe('ordenarAlertasPorCriticidad', () => {
    const alertasDesordenadas = [
      mockAlertaRecordatorio, // bajo
      mockAlertaCritica,      // critico
      mockAlertaStockBajo,    // medio
    ];

    test('debe ordenar de más crítica a menos crítica', () => {
      const ordenadas = ordenarAlertasPorCriticidad(alertasDesordenadas);
      expect(ordenadas[0].criticidad).toBe('critico');
      expect(ordenadas[1].criticidad).toBe('medio');
      expect(ordenadas[2].criticidad).toBe('bajo');
    });

    test('no debe mutar el array original', () => {
      const original = [...alertasDesordenadas];
      ordenarAlertasPorCriticidad(alertasDesordenadas);
      expect(alertasDesordenadas).toEqual(original);
    });
  });

  describe('enriquecerAlertas', () => {
    test('debe agregar criticidad a alerta sin ella', () => {
      const alertaSinCriticidad: AlertaSistema = {
        id_alerta: 1,
        tipo: 'Stock Crítico',
        mensaje: 'Stock crítico',
        fecha_creacion: '2024-03-01T10:00:00Z',
        estado: 'Pendiente',
      };

      const enriquecidas = enriquecerAlertas([alertaSinCriticidad]);
      expect(enriquecidas[0].criticidad).toBe('alto');
      expect(enriquecidas[0].roles_objetivo).toEqual(['admin', 'gerente']);
    });

    test('no debe sobrescribir criticidad existente', () => {
      const enriquecidas = enriquecerAlertas([mockAlertaCritica]);
      expect(enriquecidas[0].criticidad).toBe('critico');
    });

    test('debe manejar alertas sin config', () => {
      const alertaSinConfig: AlertaSistema = {
        id_alerta: 1,
        tipo: 'Tipo Inexistente',
        mensaje: 'Mensaje',
        fecha_creacion: '2024-03-01T10:00:00Z',
        estado: 'Pendiente',
      };

      const enriquecidas = enriquecerAlertas([alertaSinConfig]);
      expect(enriquecidas[0]).toEqual(alertaSinConfig); // Sin cambios
    });
  });

  describe('obtenerResumenCriticidad', () => {
    const alertas = [
      { ...mockAlertaCritica, criticidad: 'critico' as const },
      { ...mockAlertaCritica, id_alerta: 4, criticidad: 'critico' as const },
      { ...mockAlertaStockBajo, criticidad: 'medio' as const },
      { ...mockAlertaRecordatorio, criticidad: 'bajo' as const },
      { ...mockAlertaCritica, id_alerta: 5, tipo: 'Stock Crítico', criticidad: 'alto' as const },
    ];

    test('debe contar correctamente las alertas por criticidad', () => {
      const resumen = obtenerResumenCriticidad(alertas);
      expect(resumen.criticas).toBe(2);
      expect(resumen.altas).toBe(1);
      expect(resumen.medias).toBe(1);
      expect(resumen.bajas).toBe(1);
    });

    test('debe retornar resumen vacío para array vacío', () => {
      const resumen = obtenerResumenCriticidad([]);
      expect(resumen).toEqual({
        criticas: 0,
        altas: 0,
        medias: 0,
        bajas: 0,
      });
    });
  });

  describe('Configuraciones', () => {
    test('ALERTAS_CONFIG debe estar definida', () => {
      expect(ALERTAS_CONFIG).toBeDefined();
      expect(Object.keys(ALERTAS_CONFIG).length).toBeGreaterThan(0);
    });

    test('NOTIFICACIONES_CONFIG debe estar definida', () => {
      expect(NOTIFICACIONES_CONFIG).toBeDefined();
      expect(Object.keys(NOTIFICACIONES_CONFIG).length).toBeGreaterThan(0);
    });

    test('todas las alertas críticas deben tener admin en roles objetivo', () => {
      Object.values(ALERTAS_CONFIG).forEach(config => {
        if (config.criticidad === 'critico') {
          expect(config.rolesObjetivo).toContain('admin');
        }
      });
    });

    test('notificaciones de sistema deben incluir admin', () => {
      const actualizacionConfig = NOTIFICACIONES_CONFIG['Actualización Disponible'];
      expect(actualizacionConfig.rolesObjetivo).toContain('admin');
    });
  });
});
