// cypress/e2e/dashboard/dashboard.cy.ts
/// <reference types="cypress" />

/**
 * Tests E2E - Dashboard / Panel de Control
 * Ruta: /dashboard
 * Cubre: renderizado de KPIs, selector de período, acceso autenticado,
 *         estado de carga, tendencias y auth guard
 */

describe('Dashboard - Panel de Control', () => {
  const API = Cypress.env('API_BASE_URL') || 'http://localhost:8000/api/v1';
  const mockUser = { id: 1, username: 'gerente01', email: 'gerente@cantina.com', role: 'gerente' };

  const mockKpis = {
    fecha: new Date().toISOString().split('T')[0],
    ventas_del_dia: 1250000,
    cantidad_ventas: 15,
    recargas_del_dia: 320000,
    cantidad_recargas: 5,
    tarjetas_activas: 42,
    productos_bajo_stock: 3,
    ticket_promedio: 83333,
    saldo_total_tarjetas: 450000,
  };

  const mockDashboardVentas = {
    periodo: '7 días',
    fecha_inicio: '2026-03-10',
    fecha_fin: '2026-03-16',
    tendencia: 'crecimiento' as const,
    comparacion_semana_anterior: {
      periodo_actual: 8500000,
      periodo_anterior: 7200000,
      variacion_porcentual: 18.05,
    },
    ventas_por_dia: [
      { fecha: '2026-03-10', total_vendido: 1100000, cantidad_ventas: 13, ticket_promedio: 84615 },
      { fecha: '2026-03-11', total_vendido: 1350000, cantidad_ventas: 16, ticket_promedio: 84375 },
      { fecha: '2026-03-12', total_vendido: 1200000, cantidad_ventas: 14, ticket_promedio: 85714 },
      { fecha: '2026-03-13', total_vendido: 900000, cantidad_ventas: 11, ticket_promedio: 81818 },
      { fecha: '2026-03-14', total_vendido: 1400000, cantidad_ventas: 17, ticket_promedio: 82352 },
      { fecha: '2026-03-15', total_vendido: 1300000, cantidad_ventas: 16, ticket_promedio: 81250 },
      { fecha: '2026-03-16', total_vendido: 1250000, cantidad_ventas: 15, ticket_promedio: 83333 },
    ],
    ventas_por_metodo_pago: [
      { metodo_pago: 'Efectivo', total: 4200000, cantidad: 51 },
      { metodo_pago: 'Tarjeta Débito', total: 3000000, cantidad: 36 },
      { metodo_pago: 'Transferencia', total: 1300000, cantidad: 15 },
    ],
    productos_mas_vendidos: [
      { id_producto__nombre: 'Empanada', id_producto__codigo: 'EMP001', cantidad_vendida: 120, total_vendido: 360000 },
      { id_producto__nombre: 'Tarta', id_producto__codigo: 'TAR001', cantidad_vendida: 95, total_vendido: 285000 },
    ],
  };

  beforeEach(() => {
    // Catch-all: evita que requests no interceptados lleguen al backend real con token falso
    cy.intercept('GET', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('POST', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('PATCH', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('DELETE', 'http://localhost:8000/**', { statusCode: 200, body: {} });
  });

  function interceptDefaults(periodo = 7) {
    // Usar regex para que coincida con URLs con query params (e.g., ?fees=7&...)
    cy.intercept('GET', /\/api\/v1\/reportes\/kpis-principales/, {
      statusCode: 200,
      body: mockKpis,
    }).as('getKpis');
    cy.intercept('GET', /\/api\/v1\/reportes\/dashboard-ventas/, {
      statusCode: 200,
      body: mockDashboardVentas,
    }).as('getDashboardVentas');
    cy.intercept('GET', /\/api\/v1\/reportes\/dashboard-recargas/, {
      statusCode: 200,
      body: { total_recargas: 15, monto_total: 320000 },
    }).as('getDashboardRecargas');
  }

  function visitDashboard() {
    interceptDefaults();
    cy.visit('/dashboard', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
  }

  afterEach(() => {
    cy.clearLocalStorage();
  });

  // ── Renderizado general ───────────────────────────────────────────────────

  it('muestra el título del panel de control', () => {
    visitDashboard();
    cy.contains(/panel de control|bienvenido/i).should('be.visible');
  });

  it('muestra el nombre del usuario en el saludo', () => {
    visitDashboard();
    cy.contains(/gerente01/i).should('be.visible');
  });

  it('muestra la fecha actual en el panel', () => {
    visitDashboard();
    // La fecha se muestra en español en el subtítulo del panel
    cy.contains(/panel de control -/i).should('be.visible');
  });

  // ── Selector de período ───────────────────────────────────────────────────

  it('muestra los botones de período 7, 15 y 30 días', () => {
    visitDashboard();
    cy.contains('button', '7 días').should('be.visible');
    cy.contains('button', '15 días').should('be.visible');
    cy.contains('button', '30 días').should('be.visible');
  });

  it('el período de 7 días está seleccionado por defecto', () => {
    visitDashboard();
    cy.contains('button', '7 días').should('have.class', 'bg-purple-100');
  });

  it('cambia al período de 30 días al hacer clic', () => {
    interceptDefaults(30);
    cy.visit('/dashboard', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
    cy.contains('button', '30 días').click();
    cy.contains('button', '30 días').should('have.class', 'bg-purple-100');
  });

  it('el botón Actualizar refresca los datos', () => {
    interceptDefaults();
    cy.visit('/dashboard', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
    cy.contains('button', /actualizar/i).click();
    cy.wait('@getKpis');
  });

  // ── KPI Cards ─────────────────────────────────────────────────────────────

  it('muestra la card de Ventas del Día', () => {
    visitDashboard();
    cy.contains(/ventas del día/i).should('be.visible');
  });

  it('muestra la card de Recargas del Día', () => {
    visitDashboard();
    cy.contains(/recargas del día/i).should('be.visible');
  });

  it('muestra la card de Tarjetas Activas', () => {
    visitDashboard();
    cy.contains(/tarjetas activas/i).should('be.visible');
  });

  it('muestra la card de Ticket Promedio', () => {
    visitDashboard();
    cy.contains(/ticket promedio/i).should('be.visible');
  });

  it('muestra las 4 cards KPI con datos cargados', () => {
    visitDashboard();
    cy.wait('@getKpis');
    // Todas las KPI cards deben estar presentes
    cy.contains(/ventas del día/i).should('be.visible');
    cy.contains(/recargas del día/i).should('be.visible');
    cy.contains(/tarjetas activas/i).should('be.visible');
    cy.contains(/ticket promedio/i).should('be.visible');
  });

  it('muestra el número de transacciones del día', () => {
    visitDashboard();
    cy.wait('@getKpis');
    cy.contains(/15 transacciones/i).should('be.visible');
  });

  it('muestra alerta de productos bajo stock cuando corresponde', () => {
    visitDashboard();
    cy.wait('@getKpis');
    cy.contains(/3 productos bajo stock/i).should('be.visible');
  });

  // ── Dashboard de ventas ───────────────────────────────────────────────────

  it('muestra la sección de período actual con monto', () => {
    visitDashboard();
    cy.wait('@getDashboardVentas');
    cy.contains(/período actual/i).should('be.visible');
  });

  it('muestra la comparación con el período anterior', () => {
    visitDashboard();
    cy.wait('@getDashboardVentas');
    cy.contains(/período anterior/i).should('be.visible');
  });

  it('muestra indicador de tendencia positiva (crecimiento)', () => {
    visitDashboard();
    cy.wait('@getDashboardVentas');
    cy.contains(/crecimiento|↑|subiendo/i).should('be.visible');
  });

  // ── Auth guard ────────────────────────────────────────────────────────────

  it('redirige a /login si no hay sesión activa', () => {
    cy.clearLocalStorage();
    cy.visit('/dashboard');
    cy.url().should('include', '/login');
  });

  it('permanece en /dashboard con sesión válida', () => {
    visitDashboard();
    cy.url().should('include', '/dashboard');
    cy.url().should('not.include', '/login');
  });
});
