// cypress/e2e/ventas/historial-ventas.cy.ts
/// <reference types="cypress" />

/**
 * Tests E2E - Gestión de Ventas (Historial + Pago de créditos)
 * Ruta: /ventas/gestion
 * Cubre: listado, filtros, detalle, botón de pago, modal registro pago
 */

describe('Gestión de Ventas - Historial', () => {
  const API = Cypress.env('API_BASE_URL') || 'http://localhost:8000/api/v1';
  const mockUser = { id: 1, username: 'admin', email: 'admin@cantina.com', role: 'admin' };

  const mockVentas = {
    count: 3,
    next: null,
    previous: null,
    results: [
      {
        id_venta: 101,
        nro_factura_venta: 1001,
        fecha: '2026-03-15T10:00:00Z',
        monto_total: 150000,
        saldo_pendiente: 0,
        estado_pago: 'Pagado',
        estado: 'activo',
        tipo_venta: 'Contado',
        cliente_nombre: 'Ana García',
        hijo_nombre: null,
        iva_10: 13636,
        iva_5: 0,
        monto_exenta: 0,
        monto_gravada_10: 136364,
        monto_gravada_5: 0,
      },
      {
        id_venta: 102,
        nro_factura_venta: 1002,
        fecha: '2026-03-15T11:30:00Z',
        monto_total: 80000,
        saldo_pendiente: 80000,
        estado_pago: 'Pendiente',
        estado: 'activo',
        tipo_venta: 'Credito',
        cliente_nombre: 'Carlos López',
        hijo_nombre: null,
        iva_10: 7273,
        iva_5: 0,
        monto_exenta: 0,
        monto_gravada_10: 72727,
        monto_gravada_5: 0,
      },
      {
        id_venta: 103,
        nro_factura_venta: 1003,
        fecha: '2026-03-15T14:00:00Z',
        monto_total: 50000,
        saldo_pendiente: 25000,
        estado_pago: 'Parcial',
        estado: 'activo',
        tipo_venta: 'Credito',
        cliente_nombre: 'María Rodríguez',
        hijo_nombre: null,
        iva_10: 0,
        iva_5: 2381,
        monto_exenta: 0,
        monto_gravada_10: 0,
        monto_gravada_5: 47619,
      },
    ],
  };

  const mockMediosPago = [
    { id_medio_pago: 1, nombre: 'Efectivo', genera_comision: false, estado: true },
    { id_medio_pago: 2, nombre: 'Tarjeta Débito', genera_comision: true, estado: true },
    { id_medio_pago: 3, nombre: 'Transferencia Bancaria', genera_comision: false, estado: true },
  ];

  beforeEach(() => {
    cy.intercept('GET', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('POST', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('PATCH', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('DELETE', 'http://localhost:8000/**', { statusCode: 200, body: {} });
  });

  function interceptDefaults() {
    cy.intercept('GET', /\/api\/v1\/ventas\//, { statusCode: 200, body: mockVentas }).as('getVentas');
    cy.intercept('GET', /\/api\/v1\/medios-pago\//, {
      statusCode: 200,
      body: { count: 3, next: null, previous: null, results: mockMediosPago },
    }).as('getMediosPago');
  }

  function visitGestion() {
    interceptDefaults();
    cy.visit('/ventas/gestion', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
    cy.wait('@getVentas');
  }

  afterEach(() => {
    cy.clearLocalStorage();
  });

  // ── Renderizado general ───────────────────────────────────────────────────

  it('muestra el título de Gestión de Ventas', () => {
    visitGestion();
    cy.contains('Gestión de Ventas').should('be.visible');
  });

  it('muestra descripción de historial y seguimiento de pagos', () => {
    visitGestion();
    cy.contains(/historial|seguimiento/i).should('be.visible');
  });

  it('muestra la barra de búsqueda', () => {
    visitGestion();
    cy.get('input[placeholder*="factura" i], input[placeholder*="cliente" i], input[type="text"]')
      .should('be.visible');
  });

  it('muestra las columnas de la tabla', () => {
    visitGestion();
    cy.contains(/factura/i).should('be.visible');
    cy.contains(/cliente/i).should('be.visible');
    cy.contains(/total/i).should('be.visible');
    cy.contains(/estado/i).should('be.visible');
  });

  // ── Listado de ventas ─────────────────────────────────────────────────────

  it('muestra ventas cargadas desde la API', () => {
    visitGestion();
    cy.contains('#1001').should('be.visible');
    cy.contains('Carlos López').should('be.visible');
    cy.contains('María Rodríguez').should('be.visible');
  });

  it('muestra badge "Pagado" para ventas sin saldo', () => {
    visitGestion();
    cy.contains('Pagado').should('be.visible');
  });

  it('muestra badge "Pendiente" para ventas a crédito sin abono', () => {
    visitGestion();
    cy.contains('Pendiente').should('be.visible');
  });

  it('muestra badge "Parcial" para ventas parcialmente cobradas', () => {
    visitGestion();
    cy.contains('Parcial').should('be.visible');
  });

  it('muestra el saldo pendiente en rojo para ventas con deuda', () => {
    visitGestion();
    cy.contains(/pendiente:/i).should('be.visible');
  });

  // ── Filtros ───────────────────────────────────────────────────────────────

  it('botón Filtros muestra el panel de filtros avanzados', () => {
    visitGestion();
    cy.contains('button', /filtros/i).click();
    cy.contains(/estado de pago/i).should('be.visible');
    cy.contains(/tipo de venta/i).should('be.visible');
  });

  it('filtra por estado de pago Pendiente', () => {
    cy.intercept('GET', /\/api\/v1\/ventas\//, (req) => {
      if (req.query.estado_pago === 'Pendiente') {
        req.reply({ statusCode: 200, body: { count: 1, next: null, previous: null, results: [mockVentas.results[1]] } });
      } else {
        req.reply({ statusCode: 200, body: mockVentas });
      }
    }).as('filtradoPendiente');
    cy.intercept('GET', /\/api\/v1\/medios-pago\//, {
      statusCode: 200,
      body: { count: 3, next: null, previous: null, results: mockMediosPago },
    });
    cy.visit('/ventas/gestion', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
    cy.wait('@filtradoPendiente');
    cy.contains('button', /filtros/i).click();
    cy.get('select').first().select('Pendiente');
    cy.contains('button', /aplicar/i).click();
    cy.wait('@filtradoPendiente');
  });

  // ── Modal de detalle ──────────────────────────────────────────────────────

  it('abre el modal de detalle al hacer clic en el ícono de ojo', () => {
    visitGestion();
    cy.get('button[title*="detalle" i], button[title*="ver" i]').first().click();
    cy.contains(/detalle de venta/i).should('be.visible');
  });

  it('muestra desglose fiscal IVA en el modal de detalle', () => {
    visitGestion();
    cy.get('button[title*="detalle" i], button[title*="ver" i]').first().click();
    cy.contains(/IVA|fiscal|gravada/i).should('be.visible');
  });

  it('cierra el modal de detalle al hacer clic en ✕', () => {
    visitGestion();
    cy.get('button[title*="detalle" i], button[title*="ver" i]').first().click();
    cy.contains(/detalle de venta/i).should('be.visible');
    cy.contains('button', '✕').click();
    cy.contains(/detalle de venta/i).should('not.exist');
  });

  // ── Botón de pago (ventas con saldo_pendiente > 0) ───────────────────────

  it('muestra el botón de pago (Banknote) solo en ventas con saldo pendiente', () => {
    visitGestion();
    // La venta ID 101 (Pagado, saldo=0) NO debe tener botón de pago
    // Las ventas 102 y 103 (Pendiente/Parcial) SÍ deben tenerlo
    cy.get('button[title*="pago" i]').should('have.length', 2);
  });

  it('abre el modal de registro de pago al hacer clic en el botón de pago', () => {
    visitGestion();
    cy.get('button[title*="pago" i]').first().click();
    cy.contains(/registrar pago/i).should('be.visible');
  });

  // ── Modal de registro de pago ─────────────────────────────────────────────

  it('muestra el saldo pendiente en el modal de pago', () => {
    visitGestion();
    cy.get('button[title*="pago" i]').first().click();
    cy.contains(/saldo pendiente/i).should('be.visible');
    cy.contains(/80\.000|80,000/i).should('be.visible');
  });

  it('muestra el campo de monto pre-rellenado con el saldo pendiente', () => {
    visitGestion();
    cy.get('button[title*="pago" i]').first().click();
    cy.get('input[type="number"]').should('have.value', '80000');
  });

  it('muestra el selector de medio de pago cargado desde la API', () => {
    visitGestion();
    cy.get('button[title*="pago" i]').first().click();
    cy.contains('Efectivo').should('be.visible');
    cy.contains('Tarjeta Débito').should('be.visible');
    cy.contains('Transferencia Bancaria').should('be.visible');
  });

  it('muestra campo de referencia de transferencia al seleccionar ese medio', () => {
    visitGestion();
    cy.get('button[title*="pago" i]').first().click();
    cy.get('select').last().select('3'); // Transferencia Bancaria
    cy.get('input[placeholder*="referencia" i], input[placeholder*="operación" i]')
      .should('be.visible');
    cy.get('input[placeholder*="banco" i], input[placeholder*="Banco" i]')
      .should('be.visible');
  });

  it('registra el pago correctamente y recarga la lista', () => {
    cy.intercept('POST', /\/api\/v1\/pagos-venta\//, {
      statusCode: 201,
      body: {
        id_pago: 50,
        id_venta: 102,
        id_medio_pago: 1,
        monto: 80000,
        fecha_pago: '2026-03-16T10:00:00Z',
      },
    }).as('registrarPago');
    cy.intercept('GET', /\/api\/v1\/ventas\//, { statusCode: 200, body: mockVentas }).as('getVentasPost');
    cy.intercept('GET', /\/api\/v1\/medios-pago\//, {
      statusCode: 200,
      body: { count: 3, next: null, previous: null, results: mockMediosPago },
    });
    cy.visit('/ventas/gestion', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
    cy.wait('@getVentasPost');
    cy.get('button[title*="pago" i]').first().click();
    cy.get('select').last().select('1'); // Efectivo
    cy.contains('button', /registrar pago/i).click();
    cy.wait('@registrarPago');
    cy.wait('@getVentasPost');
    // Modal debe cerrarse
    cy.contains(/registrar pago/i).should('not.exist');
  });

  it('muestra error de validación si el monto supera el saldo pendiente', () => {
    visitGestion();
    cy.get('button[title*="pago" i]').first().click();
    cy.get('input[type="number"]').clear().type('999999');
    cy.get('select').last().select('1');
    cy.contains('button', /registrar pago/i).click();
    cy.contains(/no puede superar|saldo pendiente/i).should('be.visible');
  });

  it('cierra el modal de pago al cancelar', () => {
    visitGestion();
    cy.get('button[title*="pago" i]').first().click();
    cy.contains(/registrar pago/i).should('be.visible');
    cy.contains('button', /cancelar/i).click();
    cy.contains(/registrar pago/i).should('not.exist');
  });

  // ── Auth guard ────────────────────────────────────────────────────────────

  it('redirige a /login si no hay sesión activa', () => {
    cy.clearLocalStorage();
    cy.visit('/ventas/gestion');
    cy.url().should('include', '/login');
  });
});
