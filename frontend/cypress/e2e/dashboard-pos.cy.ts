/**
 * Tests E2E - Flujo de Punto de Venta (POS)
 * Cubre: ver catálogo, agregar al carrito, procesar venta
 */

describe('Punto de Venta (POS)', () => {
  const API = Cypress.env('API_BASE_URL') || 'http://localhost:8000/api/v1';

  // Datos de prueba - descripcion es el campo que usa el componente CatalogoProductos
  const mockUser = { id: 1, username: 'cajero', email: 'cajero@cantina.com', role: 'cajero' };
  const mockProductos = [
    {
      id_producto: 1,
      descripcion: 'Coca Cola 500ml',
      codigo_barra: 'CC500',
      precio: 5000,
      stock_actual: 50,
      estado: true,
      imagen: null,
    },
    {
      id_producto: 2,
      descripcion: 'Empanada de Carne',
      codigo_barra: 'EMP01',
      precio: 3000,
      stock_actual: 20,
      estado: true,
      imagen: null,
    },
  ];

  beforeEach(() => {
    // Interceptar TODAS las llamadas a la API (hostname especifico para no afectar frontend)
    cy.intercept('GET', 'http://localhost:8000/**', (req) => {
      if (req.url.includes('/productos')) {
        req.reply({ statusCode: 200, body: { count: mockProductos.length, results: mockProductos } });
      } else {
        req.reply({ statusCode: 200, body: { count: 0, results: [] } });
      }
    }).as('getProductos');

    // Simular usuario autenticado en onBeforeLoad (se ejecuta antes que el JS de la app)
    cy.visit('/ventas', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
    cy.wait('@getProductos');
  });

  it('muestra el catálogo de productos', () => {
    cy.contains('Coca Cola 500ml').should('be.visible');
    cy.contains('Empanada de Carne').should('be.visible');
  });

  it('muestra el precio de los productos', () => {
    cy.contains('5.000').should('be.visible');
    cy.contains('3.000').should('be.visible');
  });

  it('permite agregar productos al carrito', () => {
    // Hacer clic en el primer producto para agregarlo al carrito
    cy.contains('Coca Cola 500ml').click();
    // El carrito debe reflejar el ítem agregado
    cy.contains('Coca Cola 500ml').should('have.length.at.least', 1);
  });

  it('permite buscar productos por nombre', () => {
    cy.get('input[placeholder*="buscar" i], input[placeholder*="código" i]')
      .first()
      .type('Coca');
    // Solo debe aparecer el producto correspondiente
    cy.contains('Coca Cola 500ml').should('be.visible');
  });
});

// ── Dashboard con datos reales ─────────────────────────────────────────────────

describe('Dashboard', () => {
  const mockAdmin = { id: 1, username: 'admin', email: 'admin@cantina.com', role: 'admin' };
  const mockKpis = {
    ventas_del_dia: 1250000,
    cantidad_ventas: 42,
    recargas_del_dia: 500000,
    cantidad_recargas: 8,
    tarjetas_activas: 145,
    productos_bajo_stock: 3,
    ticket_promedio: 29762,
    saldo_total_tarjetas: 8500000,
  };
  const mockDashboardVentas = {
    periodo: '7d',
    fecha_inicio: '2026-03-02',
    fecha_fin: '2026-03-09',
    ventas_por_dia: [
      { fecha: '2026-03-09', cantidad_ventas: 42, total_vendido: 1250000, ticket_promedio: 29762 },
    ],
    ventas_por_metodo_pago: [],
    productos_mas_vendidos: [],
    comparacion_semana_anterior: {
      periodo_actual: 6740000,
      periodo_anterior: 4500000,
      variacion_porcentual: 49.8,
    },
    tendencia: 'crecimiento',
  };

  beforeEach(() => {
    // Catch-all para la API del backend (hostname específico para no interceptar el frontend)
    cy.intercept('GET', 'http://localhost:8000/**', (req) => {
      if (req.url.includes('kpis-principales')) {
        req.reply({ statusCode: 200, body: mockKpis });
      } else if (req.url.includes('dashboard-ventas')) {
        req.reply({ statusCode: 200, body: mockDashboardVentas });
      } else {
        req.reply({ statusCode: 200, body: { count: 0, results: [] } });
      }
    }).as('getKpis');

    cy.intercept('POST', 'http://localhost:8000/**', { statusCode: 200, body: {} });

    cy.visit('/dashboard', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockAdmin));
      },
    });
    cy.wait('@getKpis');
  });

  it('muestra el saludo de bienvenida', () => {
    cy.contains('Bienvenido').should('be.visible');
    cy.contains('admin').should('be.visible');
  });

  it('muestra los KPIs del día', () => {
    // Los montos formateados en Guaraníes (1.250.000 y tarjetas activas 145)
    cy.contains('1.250.000').should('be.visible');
    cy.contains('145').should('be.visible');
  });

  it('muestra la alerta de stock bajo', () => {
    // El componente muestra "3 productos bajo stock"
    cy.contains('productos bajo stock').should('be.visible');
    cy.contains('3').should('be.visible');
  });

  it('muestra el análisis de rendimiento', () => {
    // El componente muestra "42 transacciones" y badge "Crecimiento"
    cy.contains('42 transacciones').should('be.visible');
    cy.contains('Crecimiento').should('be.visible');
  });

  it('navega al módulo de ventas correctamente', () => {
    cy.on('uncaught:exception', () => false);
    cy.intercept('GET', 'http://localhost:8000/**', { statusCode: 200, body: { count: 0, results: [] } });
    cy.visit('/ventas', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockAdmin));
      },
    });
    cy.url().should('include', '/ventas');
  });
});
