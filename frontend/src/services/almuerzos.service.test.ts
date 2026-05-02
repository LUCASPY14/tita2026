import api from './api';
import { 
  almuerzosService, 
  PlanParams, 
  TipoParams, 
  SuscripcionParams,
  RegistroParams,
  PlanData,
  TipoData,
  SuscripcionData
} from './almuerzos.service';
import type { 
  PaginatedResponse,
  RegistroConsumoData,
  Alergeno
} from '../types';

vi.mock('./api');
const mockedApi = api as vi.Mocked<typeof api>;

describe('Almuerzos Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // === PLANES DE ALMUERZO ===
  describe('Planes de Almuerzo', () => {
    const mockPlanes = [
      {
        id_plan_almuerzo: 1,
        nombre_plan: 'Plan Completo',
        descripcion: 'Incluye almuerzo todos los días',
        precio_mensual: 500000,
        dias_semana_incluidos: 'Lunes,Martes,Miércoles,Jueves,Viernes',
        estado: true,
        fecha_creacion: '2024-01-01'
      },
      {
        id_plan_almuerzo: 2,
        nombre_plan: 'Plan 3 Días',
        descripcion: 'Almuerzo 3 días por semana',
        precio_mensual: 300000,
        dias_semana_incluidos: 'Lunes,Miércoles,Viernes',
        estado: true,
        fecha_creacion: '2024-01-01'
      }
    ];

    const mockResponse: PaginatedResponse<typeof mockPlanes[0]> = {
      count: 2,
      next: null,
      previous: null,
      results: mockPlanes
    };

    describe('getPlanes', () => {
      test('debe obtener planes sin parámetros', async () => {
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await almuerzosService.getPlanes();

        expect(mockedApi.get).toHaveBeenCalledWith('/planes-almuerzo/', { params: undefined });
        expect(result).toEqual(mockResponse);
      });

      test('debe obtener planes con filtros', async () => {
        const params: PlanParams = { estado: true };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getPlanes(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/planes-almuerzo/', { params });
      });

      test('debe buscar planes por término de búsqueda', async () => {
        const params: PlanParams = { search: 'Completo' };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getPlanes(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/planes-almuerzo/', { params });
      });
    });

    describe('getPlanById', () => {
      test('debe obtener plan por ID', async () => {
        mockedApi.get.mockResolvedValue({ data: mockPlanes[0] });

        const result = await almuerzosService.getPlanById(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/planes-almuerzo/1/');
        expect(result).toEqual(mockPlanes[0]);
      });
    });

    describe('crearPlan', () => {
      const planData: PlanData = {
        nombre_plan: 'Plan Nuevo',
        descripcion: 'Plan de prueba',
        precio_mensual: 400000,
        dias_semana_incluidos: 'Lunes,Martes,Jueves',
        estado: true
      };

      test('debe crear plan nuevo', async () => {
        const planCreado = { id_plan_almuerzo: 3, ...planData, fecha_creacion: '2024-01-15' };
        mockedApi.post.mockResolvedValue({ data: planCreado });

        const result = await almuerzosService.crearPlan(planData);

        expect(mockedApi.post).toHaveBeenCalledWith('/planes-almuerzo/', planData);
        expect(result).toEqual(planCreado);
      });
    });

    describe('actualizarPlan', () => {
      test('debe actualizar plan', async () => {
        const updateData = { precio_mensual: 550000 };
        const planActualizado = { ...mockPlanes[0], ...updateData };
        mockedApi.patch.mockResolvedValue({ data: planActualizado });

        const result = await almuerzosService.actualizarPlan(1, updateData);

        expect(mockedApi.patch).toHaveBeenCalledWith('/planes-almuerzo/1/', updateData);
        expect(result.precio_mensual).toBe(550000);
      });
    });

    describe('eliminarPlan', () => {
      test('debe eliminar plan', async () => {
        mockedApi.delete.mockResolvedValue({ data: null });

        await almuerzosService.eliminarPlan(1);

        expect(mockedApi.delete).toHaveBeenCalledWith('/planes-almuerzo/1/');
      });
    });

    describe('toggleEstadoPlan', () => {
      test('debe desactivar plan', async () => {
        const planInactivo = { ...mockPlanes[0], estado: false };
        mockedApi.patch.mockResolvedValue({ data: planInactivo });

        const result = await almuerzosService.toggleEstadoPlan(1, false);

        expect(mockedApi.patch).toHaveBeenCalledWith('/planes-almuerzo/1/', { estado: false });
        expect(result.estado).toBe(false);
      });
    });
  });

  // === TIPOS DE ALMUERZO ===
  describe('Tipos de Almuerzo', () => {
    const mockTipos = [
      {
        id_tipo_almuerzo: 1,
        nombre: 'Completo',
        descripcion: 'Almuerzo completo con plato principal, postre y bebida',
        precio_unitario: 25000,
        incluye_plato_principal: true,
        incluye_postre: true,
        incluye_bebida: true,
        estado: true,
        fecha_creacion: '2024-01-01'
      },
      {
        id_tipo_almuerzo: 2,
        nombre: 'Básico',
        descripcion: 'Solo plato principal',
        precio_unitario: 15000,
        incluye_plato_principal: true,
        incluye_postre: false,
        incluye_bebida: false,
        estado: true,
        fecha_creacion: '2024-01-01'
      }
    ];

    const mockResponse: PaginatedResponse<typeof mockTipos[0]> = {
      count: 2,
      next: null,
      previous: null,
      results: mockTipos
    };

    describe('getTipos', () => {
      test('debe obtener tipos de almuerzo', async () => {
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await almuerzosService.getTipos();

        expect(mockedApi.get).toHaveBeenCalledWith('/tipos-almuerzo/', { params: undefined });
        expect(result).toEqual(mockResponse);
      });

      test('debe filtrar tipos activos', async () => {
        const params: TipoParams = { estado: true };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getTipos(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/tipos-almuerzo/', { params });
      });
    });

    describe('getTipoById', () => {
      test('debe obtener tipo por ID', async () => {
        mockedApi.get.mockResolvedValue({ data: mockTipos[0] });

        const result = await almuerzosService.getTipoById(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/tipos-almuerzo/1/');
        expect(result).toEqual(mockTipos[0]);
      });
    });

    describe('crearTipo', () => {
      const tipoData: TipoData = {
        nombre: 'Premium',
        descripcion: 'Almuerzo premium',
        precio_unitario: 35000,
        incluye_plato_principal: true,
        incluye_postre: true,
        incluye_bebida: true,
        estado: true
      };

      test('debe crear tipo nuevo', async () => {
        const tipoCreado = { id_tipo_almuerzo: 3, ...tipoData, fecha_creacion: '2024-01-15' };
        mockedApi.post.mockResolvedValue({ data: tipoCreado });

        const result = await almuerzosService.crearTipo(tipoData);

        expect(mockedApi.post).toHaveBeenCalledWith('/tipos-almuerzo/', tipoData);
        expect(result).toEqual(tipoCreado);
      });
    });

    describe('actualizarTipo', () => {
      test('debe actualizar tipo', async () => {
        const updateData = { precio_unitario: 27000 };
        const tipoActualizado = { ...mockTipos[0], ...updateData };
        mockedApi.patch.mockResolvedValue({ data: tipoActualizado });

        const result = await almuerzosService.actualizarTipo(1, updateData);

        expect(mockedApi.patch).toHaveBeenCalledWith('/tipos-almuerzo/1/', updateData);
        expect(result.precio_unitario).toBe(27000);
      });
    });

    describe('eliminarTipo', () => {
      test('debe eliminar tipo', async () => {
        mockedApi.delete.mockResolvedValue({ data: null });

        await almuerzosService.eliminarTipo(1);

        expect(mockedApi.delete).toHaveBeenCalledWith('/tipos-almuerzo/1/');
      });
    });

    describe('toggleEstadoTipo', () => {
      test('debe desactivar tipo', async () => {
        const tipoInactivo = { ...mockTipos[0], estado: false };
        mockedApi.patch.mockResolvedValue({ data: tipoInactivo });

        const result = await almuerzosService.toggleEstadoTipo(1, false);

        expect(mockedApi.patch).toHaveBeenCalledWith('/tipos-almuerzo/1/', { estado: false });
        expect(result.estado).toBe(false);
      });
    });
  });

  // === SUSCRIPCIONES ===
  describe('Suscripciones', () => {
    const mockSuscripciones = [
      {
        id_suscripcion: 1,
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-12-31',
        estado: 'Activa',
        id_hijo: 1,
        id_plan_almuerzo: 1,
        fecha_creacion: '2024-01-01'
      },
      {
        id_suscripcion: 2,
        fecha_inicio: '2024-01-15',
        fecha_fin: '2024-06-15',
        estado: 'Activa',
        id_hijo: 2,
        id_plan_almuerzo: 2,
        fecha_creacion: '2024-01-15'
      }
    ];

    const mockResponse: PaginatedResponse<typeof mockSuscripciones[0]> = {
      count: 2,
      next: null,
      previous: null,
      results: mockSuscripciones
    };

    describe('getSuscripciones', () => {
      test('debe obtener suscripciones sin filtros', async () => {
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await almuerzosService.getSuscripciones();

        expect(mockedApi.get).toHaveBeenCalledWith('/suscripciones-almuerzo/', { params: undefined });
        expect(result).toEqual(mockResponse);
      });

      test('debe filtrar suscripciones activas', async () => {
        const params: SuscripcionParams = { estado: 'Activa' };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getSuscripciones(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/suscripciones-almuerzo/', { params });
      });

      test('debe filtrar suscripciones por hijo', async () => {
        const params: SuscripcionParams = { id_hijo: 1 };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getSuscripciones(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/suscripciones-almuerzo/', { params });
      });
    });

    describe('getSuscripcionById', () => {
      test('debe obtener suscripción por ID', async () => {
        mockedApi.get.mockResolvedValue({ data: mockSuscripciones[0] });

        const result = await almuerzosService.getSuscripcionById(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/suscripciones-almuerzo/1/');
        expect(result).toEqual(mockSuscripciones[0]);
      });
    });

    describe('crearSuscripcion', () => {
      const suscripcionData: SuscripcionData = {
        fecha_inicio: '2024-02-01',
        fecha_fin: '2024-07-01',
        estado: 'Activa',
        id_hijo: 3,
        id_plan_almuerzo: 1
      };

      test('debe crear suscripción nueva', async () => {
        const suscripcionCreada = { id_suscripcion: 3, ...suscripcionData, fecha_creacion: '2024-02-01' };
        mockedApi.post.mockResolvedValue({ data: suscripcionCreada });

        const result = await almuerzosService.crearSuscripcion(suscripcionData);

        expect(mockedApi.post).toHaveBeenCalledWith('/suscripciones-almuerzo/', suscripcionData);
        expect(result).toEqual(suscripcionCreada);
      });
    });

    describe('actualizarSuscripcion', () => {
      test('debe actualizar suscripción', async () => {
        const updateData = { estado: 'Finalizada' };
        const suscripcionActualizada = { ...mockSuscripciones[0], ...updateData };
        mockedApi.patch.mockResolvedValue({ data: suscripcionActualizada });

        const result = await almuerzosService.actualizarSuscripcion(1, updateData);

        expect(mockedApi.patch).toHaveBeenCalledWith('/suscripciones-almuerzo/1/', updateData);
        expect(result.estado).toBe('Finalizada');
      });
    });

    describe('eliminarSuscripcion', () => {
      test('debe eliminar suscripción', async () => {
        mockedApi.delete.mockResolvedValue({ data: null });

        await almuerzosService.eliminarSuscripcion(1);

        expect(mockedApi.delete).toHaveBeenCalledWith('/suscripciones-almuerzo/1/');
      });
    });

    describe('getSuscripcionesPorHijo', () => {
      test('debe obtener suscripciones de un hijo específico', async () => {
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getSuscripcionesPorHijo(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/suscripciones-almuerzo/', {
          params: { id_hijo: 1 }
        });
      });
    });

    describe('getSuscripcionesActivas', () => {
      test('debe obtener solo suscripciones activas', async () => {
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getSuscripcionesActivas();

        expect(mockedApi.get).toHaveBeenCalledWith('/suscripciones-almuerzo/', {
          params: { estado: 'Activa' }
        });
      });
    });
  });

  // === REGISTROS DE CONSUMO ===
  describe('Registros de Consumo', () => {
    const mockRegistros = [
      {
        id_registro: 1,
        fecha_consumo: '2024-01-15',
        hora_registro: '12:30:00',
        estado: 'Confirmado',
        id_hijo: 1,
        nro_tarjeta: '1234567890',
        id_tipo_almuerzo: 1,
        id_suscripcion: 1,
        fecha_creacion: '2024-01-15T12:30:00'
      },
      {
        id_registro: 2,
        fecha_consumo: '2024-01-15',
        hora_registro: '12:45:00',
        estado: 'Confirmado',
        id_hijo: 2,
        nro_tarjeta: '0987654321',
        id_tipo_almuerzo: 2,
        id_suscripcion: 2,
        fecha_creacion: '2024-01-15T12:45:00'
      }
    ];

    const mockResponse: PaginatedResponse<typeof mockRegistros[0]> = {
      count: 2,
      next: null,
      previous: null,
      results: mockRegistros
    };

    describe('getRegistros', () => {
      test('debe obtener registros sin filtros', async () => {
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await almuerzosService.getRegistros();

        expect(mockedApi.get).toHaveBeenCalledWith('/registros-consumo-almuerzo/', { params: undefined });
        expect(result).toEqual(mockResponse);
      });

      test('debe filtrar registros por estado', async () => {
        const params: RegistroParams = { estado: 'Confirmado' };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getRegistros(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/registros-consumo-almuerzo/', { params });
      });

      test('debe filtrar registros por hijo', async () => {
        const params: RegistroParams = { id_hijo: 1 };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getRegistros(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/registros-consumo-almuerzo/', { params });
      });

      test('debe filtrar registros por rango de fechas', async () => {
        const params: RegistroParams = { 
          fecha_desde: '2024-01-01', 
          fecha_hasta: '2024-01-31' 
        };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getRegistros(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/registros-consumo-almuerzo/', { params });
      });
    });

    describe('getRegistroById', () => {
      test('debe obtener registro por ID', async () => {
        mockedApi.get.mockResolvedValue({ data: mockRegistros[0] });

        const result = await almuerzosService.getRegistroById(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/registros-consumo-almuerzo/1/');
        expect(result).toEqual(mockRegistros[0]);
      });
    });

    describe('registrarConsumo', () => {
      const consumoData: RegistroConsumoData = {
        fecha_consumo: '2024-01-16',
        id_hijo: 1,
        nro_tarjeta: '1234567890',
        id_tipo_almuerzo: 1,
        id_suscripcion: 1
      };

      test('debe registrar consumo nuevo', async () => {
        const consumoCreado = { 
          id_registro: 3, 
          ...consumoData, 
          estado: 'Confirmado',
          hora_registro: '12:00:00',
          fecha_creacion: '2024-01-16T12:00:00'
        };
        mockedApi.post.mockResolvedValue({ data: consumoCreado });

        const result = await almuerzosService.registrarConsumo(consumoData);

        expect(mockedApi.post).toHaveBeenCalledWith('/registros-consumo-almuerzo/', consumoData);
        expect(result).toEqual(consumoCreado);
      });
    });

    describe('getRegistrosHoy', () => {
      test('debe obtener registros del día actual sin filtro de hijo', async () => {
        const hoy = new Date().toISOString().split('T')[0];
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getRegistrosHoy();

        expect(mockedApi.get).toHaveBeenCalledWith('/registros-consumo-almuerzo/', {
          params: { fecha_consumo: hoy }
        });
      });

      test('debe obtener registros del día actual de un hijo específico', async () => {
        const hoy = new Date().toISOString().split('T')[0];
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getRegistrosHoy(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/registros-consumo-almuerzo/', {
          params: { fecha_consumo: hoy, id_hijo: 1 }
        });
      });
    });

    describe('getRegistrosPorHijo', () => {
      test('debe obtener registros de un hijo sin rango de fechas', async () => {
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getRegistrosPorHijo(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/registros-consumo-almuerzo/', {
          params: { 
            id_hijo: 1, 
            ordering: '-fecha_consumo,-hora_registro' 
          }
        });
      });

      test('debe obtener registros de un hijo con rango de fechas', async () => {
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getRegistrosPorHijo(1, '2024-01-01', '2024-01-31');

        expect(mockedApi.get).toHaveBeenCalledWith('/registros-consumo-almuerzo/', {
          params: { 
            id_hijo: 1,
            fecha_desde: '2024-01-01',
            fecha_hasta: '2024-01-31',
            ordering: '-fecha_consumo,-hora_registro' 
          }
        });
      });
    });

    describe('getRegistrosDelDia', () => {
      test('debe obtener registros de una fecha específica', async () => {
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getRegistrosDelDia('2024-01-15');

        expect(mockedApi.get).toHaveBeenCalledWith('/registros-consumo-almuerzo/', {
          params: { 
            fecha_consumo: '2024-01-15', 
            ordering: '-hora_registro' 
          }
        });
      });
    });
  });

  // === CUENTAS MENSUALES ===
  describe('Cuentas Mensuales', () => {
    const mockCuentas = [
      {
        id_cuenta: 1,
        id_hijo: 1,
        anio: 2024,
        mes: 1,
        total_consumos: 20,
        monto_total: 500000,
        monto_pagado: 500000,
        saldo_pendiente: 0,
        estado: 'Pagado',
        fecha_generacion: '2024-02-01'
      }
    ];

    const mockResponse: PaginatedResponse<typeof mockCuentas[0]> = {
      count: 1,
      next: null,
      previous: null,
      results: mockCuentas
    };

    describe('getCuentasMensuales', () => {
      test('debe obtener cuentas mensuales sin filtros', async () => {
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await almuerzosService.getCuentasMensuales();

        expect(mockedApi.get).toHaveBeenCalledWith('/cuentas-almuerzo-mensual/', { params: undefined });
        expect(result).toEqual(mockResponse);
      });

      test('debe filtrar cuentas por hijo', async () => {
        const params = { id_hijo: 1 };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getCuentasMensuales(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/cuentas-almuerzo-mensual/', { params });
      });

      test('debe filtrar cuentas por año y mes', async () => {
        const params = { anio: 2024, mes: 1 };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getCuentasMensuales(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/cuentas-almuerzo-mensual/', { params });
      });
    });

    describe('getCuentaMensualById', () => {
      test('debe obtener cuenta mensual por ID', async () => {
        mockedApi.get.mockResolvedValue({ data: mockCuentas[0] });

        const result = await almuerzosService.getCuentaMensualById(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/cuentas-almuerzo-mensual/1/');
        expect(result).toEqual(mockCuentas[0]);
      });
    });
  });

  // === ALÉRGENOS ===
  describe('Alérgenos', () => {
    const mockAlergenos: Alergeno[] = [
      {
        id_alergeno: 1,
        nombre: 'Gluten',
        descripcion: 'Proteína del trigo, cebada y centeno',
        palabras_clave: ['trigo', 'pan', 'harina'],
        nivel_severidad: 'Alto',
        icono: '🌾',
        estado: true,
        fecha_creacion: '2024-01-01',
        usuario_creacion: 'admin'
      },
      {
        id_alergeno: 2,
        nombre: 'Lactosa',
        descripcion: 'Azúcar de la leche',
        palabras_clave: ['leche', 'queso', 'yogur'],
        nivel_severidad: 'Medio',
        icono: '🥛',
        estado: true,
        fecha_creacion: '2024-01-01',
        usuario_creacion: 'admin'
      }
    ];

    const mockResponse: PaginatedResponse<Alergeno> = {
      count: 2,
      next: null,
      previous: null,
      results: mockAlergenos
    };

    describe('getAlergenos', () => {
      test('debe obtener alérgenos sin filtros', async () => {
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await almuerzosService.getAlergenos();

        expect(mockedApi.get).toHaveBeenCalledWith('/alergenos/', { params: undefined });
        expect(result).toEqual(mockResponse);
      });

      test('debe filtrar alérgenos activos', async () => {
        const params = { estado: true };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getAlergenos(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/alergenos/', { params });
      });

      test('debe buscar alérgenos por término', async () => {
        const params = { search: 'Gluten' };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await almuerzosService.getAlergenos(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/alergenos/', { params });
      });
    });

    describe('getAlergenoById', () => {
      test('debe obtener alérgeno por ID', async () => {
        mockedApi.get.mockResolvedValue({ data: mockAlergenos[0] });

        const result = await almuerzosService.getAlergenoById(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/alergenos/1/');
        expect(result).toEqual(mockAlergenos[0]);
      });
    });

    describe('crearAlergeno', () => {
      const alergenoData: Partial<Alergeno> = {
        nombre: 'Maní',
        descripcion: 'Frutos secos - cacahuetes',
        palabras_clave: ['maní', 'cacahuete', 'fruto seco'],
        nivel_severidad: 'Alto',
        icono: '🥜',
        estado: true
      };

      test('debe crear alérgeno nuevo', async () => {
        const alergenoCreado: Alergeno = { 
          ...alergenoData as Alergeno,
          id_alergeno: 3, 
          fecha_creacion: '2024-01-15',
          usuario_creacion: 'admin'
        };
        mockedApi.post.mockResolvedValue({ data: alergenoCreado });

        const result = await almuerzosService.crearAlergeno(alergenoData);

        expect(mockedApi.post).toHaveBeenCalledWith('/alergenos/', alergenoData);
        expect(result).toEqual(alergenoCreado);
      });
    });

    describe('actualizarAlergeno', () => {
      test('debe actualizar alérgeno', async () => {
        const updateData = { nivel_severidad: 'Medio' as const };
        const alergenoActualizado = { ...mockAlergenos[0], ...updateData };
        mockedApi.patch.mockResolvedValue({ data: alergenoActualizado });

        const result = await almuerzosService.actualizarAlergeno(1, updateData);

        expect(mockedApi.patch).toHaveBeenCalledWith('/alergenos/1/', updateData);
        expect(result.nivel_severidad).toBe('Medio');
      });
    });

    describe('eliminarAlergeno', () => {
      test('debe eliminar alérgeno', async () => {
        mockedApi.delete.mockResolvedValue({ data: null });

        await almuerzosService.eliminarAlergeno(1);

        expect(mockedApi.delete).toHaveBeenCalledWith('/alergenos/1/');
      });
    });
  });

  // === ESTADÍSTICAS ===
  describe('Estadísticas', () => {
    describe('getEstadisticasConsumos', () => {
      const mockEstadisticas: PaginatedResponse<any> = {
        count: 50,
        next: null,
        previous: null,
        results: []
      };

      test('debe obtener estadísticas generales', async () => {
        mockedApi.get.mockResolvedValue({ data: mockEstadisticas });

        await almuerzosService.getEstadisticasConsumos();

        expect(mockedApi.get).toHaveBeenCalledWith('/registros-consumo-almuerzo/', {
          params: { estado: 'Confirmado' }
        });
      });

      test('debe obtener estadísticas de un hijo específico', async () => {
        mockedApi.get.mockResolvedValue({ data: mockEstadisticas });

        await almuerzosService.getEstadisticasConsumos(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/registros-consumo-almuerzo/', {
          params: { id_hijo: 1, estado: 'Confirmado' }
        });
      });
    });
  });
});
