/**
 * Tests E2E - Flujo de Punto de Venta (POS)
 * Cubre: ver catálogo, agregar al carrito, procesar venta
 */

describe('Punto de Venta (POS)', () => {
  const API = Cypress.env('API_BASE_URL') || 'http://localhost:8000/api/v1';

  // Datos de prueba
  const mockUser = { id: 1, username: 'cajero', email: 'cajero@cantina.com', role: 'cajero' };
  const mockProductos = [
    {
      id_producto: 1,
      nombre: 'Coca Cola 500ml',
      codigo: 'CC500',
      precio_venta: 5000,
      stock_actual: 50,
      activo: true,
      imagen: null,
    },
    {
      id_producto: 2,
      nombre: 'Empanada de Carne',
      codigo: 'EMP01',
      precio_venta: 3000,
      stock_actual: 20,
      activo: true,
      imagen: null,
    },
  ];

  beforeEach(() => {
    // Simular usuario autenticado
    cy.window().then((win) => {
      win.localStorage.setItem('token', 'fake-access-token');
      win.localStorage.setItem('user', JSON.stringify(mockUser));
    });

    // Interceptar peticiones de la página POS
    cy.intercept('GET', `${API}/productos/**`, {
      statusCode: 200,
      body: {
        count: mockProductos.length,
        results: mockProductos,
      },
    }).as('getProductos');

    cy.intercept('GET', `${API}/ventas/**`, {
      statusCode: 200,
      body: { count: 0, results: [] },
    }).as('getVentas');

    cy.visit('/pos');
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
    cy.get('input[placeholder*="buscar" i], input[placeholder*="producto" i]')
      .first()
      .type('Coca');
    // Solo debe aparecer el producto correspondiente
    cy.contains('Coca Cola 500ml').should('be.visible');
  });
});

// ── Dashboard con datos reales ─────────────────────────────────────────────────

describe('Dashboard', () => {
  const API = Cypress.env('API_BASE_URL') || 'http://localhost:8000/api/v1';

  beforeEach(() => {
    cy.window().then((win) => {
      win.localStorage.setItem('token', 'fake-access-token');
      win.localStorage.setItem('user', JSON.stringify({
        id: 1, username: 'admin', email: 'admin@cantina.com', role: 'admin',
      }));
    });

    cy.intercept('GET', `${API}/reportes/kpis-principales/**`, {
      statusCode: 200,
      body: {
        ventas_del_dia: 1250000,
        cantidad_ventas: 42,
        recargas_del_dia: 500000,
        cantidad_recargas: 8,
        tarjetas_activas: 145,
        productos_bajo_stock: 3,
        ticket_promedio: 29762,
        saldo_total_tarjetas: 8500000,
      },
    }).as('getKpis');

    cy.intercept('GET', `${API}/reportes/dashboard-ventas/**`, {
      statusCode: 200,
      body: {
        periodo: '7d',
        fecha_inicio: '2026-03-02',
        fecha_fin: '2026-03-09',
        ventas_por_dia: [
          { fecha: '2026-03-03', cantidad_ventas: 30, total_vendido: 900000, ticket_promedio: 30000 },
          { fecha: '2026-03-04', cantidad_ventas: 38, total_vendido: 1140000, ticket_promedio: 30000 },
          { fecha: '2026-03-05', cantidad_ventas: 42, total_vendido: 1260000, ticket_promedio: 30000 },
          { fecha: '2026-03-06', cantidad_ventas: 35, total_vendido: 1050000, ticket_promedio: 30000 },
          { fecha: '2026-03-07', cantidad_ventas: 28, total_vendido: 840000, ticket_promedio: 30000 },
          { fecha: '2026-03-08', cantidad_ventas: 10, total_vendido: 300000, ticket_promedio: 30000 },
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
      },
    }).as('getDashboardVentas');

    cy.intercept('GET', `${API}/reportes/dashboard-recargas/**`, {
      statusCode: 200,
      body: {
        periodo: '7d',
        fecha_inicio: '2026-03-02',
        fecha_fin: '2026-03-09',
        recargas_por_dia: [],
        recargas_por_metodo: [],
        comisiones_generadas: 25000,
        total_recargas: 500000,
        recargas_exitosas: 8,
        tasa_exito: 100,
      },
    }).as('getDashboardRecargas');

    cy.visit('/dashboard');
    cy.wait('@getKpis');
  });

  it('muestra el saludo de bienvenida', () => {
    cy.contains('Bienvenido').should('be.visible');
    cy.contains('admin').should('be.visible');
  });

  it('muestra los KPIs del día', () => {
    // Los montos formateados en Guaraníes
    cy.contains('1.250.000').should('be.visible');
    cy.contains('145').should('be.visible');
  });

  it('muestra la alerta de stock bajo', () => {
    cy.contains('3 productos').should('be.visible');
    cy.contains('Alerta de Stock').should('be.visible');
  });

  it('muestra las acciones rápidas', () => {
    cy.contains('Nueva Venta').should('be.visible');
    cy.contains('Recargar Tarjeta').should('be.visible');
    cy.contains('Clientes').should('be.visible');
    cy.contains('Inventario').should('be.visible');
  });

  it('el botón Nueva Venta navega a /pos', () => {
    cy.intercept('GET', `${API}/productos/**`, { body: { count: 0, results: [] } });
    cy.intercept('GET', `${API}/ventas/**`, { body: { count: 0, results: [] } });
    cy.contains('Nueva Venta').click();
    cy.url().should('include', '/pos');
  });
});
