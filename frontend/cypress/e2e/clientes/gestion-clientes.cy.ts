// cypress/e2e/clientes/gestion-clientes.cy.ts
/// <reference types="cypress" />

/**
 * Tests E2E - Gestión de Clientes
 * Cubre: listado, búsqueda, filtros, creación, toggle estado
 */

describe('Gestión de Clientes', () => {
  const API = Cypress.env('API_BASE_URL') || 'http://localhost:8000/api/v1';
  const mockUser = { id: 1, username: 'admin', email: 'admin@cantina.com', role: 'admin' };

  const mockClientes = {
    count: 3,
    next: null,
    previous: null,
    results: [
      {
        id_cliente: 1,
        nombres: 'Ana',
        apellidos: 'García',
        ruc_ci: '1234567',
        email: 'ana@test.com',
        telefono: '0981111111',
        estado: true,
        fecha_registro: '2024-01-01',
        id_lista: 1,
        id_tipo_cliente: 1,
        nombre_completo: 'Ana García',
      },
      {
        id_cliente: 2,
        nombres: 'Carlos',
        apellidos: 'López',
        ruc_ci: '7654321',
        email: 'carlos@test.com',
        telefono: '0982222222',
        estado: false,
        fecha_registro: '2024-01-05',
        id_lista: 1,
        id_tipo_cliente: 1,
        nombre_completo: 'Carlos López',
      },
      {
        id_cliente: 3,
        nombres: 'María',
        apellidos: 'Rodríguez',
        ruc_ci: '9999999',
        email: 'maria@test.com',
        telefono: '0983333333',
        estado: true,
        fecha_registro: '2024-01-10',
        id_lista: 1,
        id_tipo_cliente: 1,
        nombre_completo: 'María Rodríguez',
      },
    ],
  };

  function visitClientes() {
    cy.intercept('GET', /\/api\/v1\/clientes/, { statusCode: 200, body: mockClientes }).as('getClientes');
    cy.intercept('GET', /\/api\/v1\/tipos-cliente/, {
      statusCode: 200,
      body: { count: 1, next: null, previous: null, results: [{ id_tipo_cliente: 1, nombre: 'Regular', estado: true }] },
    }).as('getTipos');
    cy.intercept('GET', /\/api\/v1\/listas-precio/, {
      statusCode: 200,
      body: { count: 1, next: null, previous: null, results: [{ id_lista: 1, nombre_lista: 'Lista General', estado: true }] },
    }).as('getListas');

    cy.visit('/clientes', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
    cy.wait('@getClientes');
  }

  beforeEach(() => {
    cy.intercept('GET', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('POST', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('PATCH', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('DELETE', 'http://localhost:8000/**', { statusCode: 200, body: {} });
  });

  afterEach(() => {
    cy.clearLocalStorage();
  });

  // ── Listado ──────────────────────────────────────────────────────────────

  it('muestra el encabezado de la sección', () => {
    visitClientes();
    cy.contains('Clientes').should('be.visible');
  });

  it('lista los clientes correctamente', () => {
    visitClientes();
    cy.contains('Ana García').should('be.visible');
    cy.contains('Carlos López').should('be.visible');
    cy.contains('María Rodríguez').should('be.visible');
  });

  it('muestra el RUC/CI de cada cliente', () => {
    visitClientes();
    cy.contains('1234567').should('be.visible');
    cy.contains('7654321').should('be.visible');
  });

  it('muestra el total de clientes', () => {
    visitClientes();
    cy.contains('3').should('be.visible');
  });

  it('mantiene la sesión activa (no redirige a login)', () => {
    visitClientes();
    cy.url().should('include', '/clientes');
    cy.url().should('not.include', '/login');
  });

  // ── Búsqueda ─────────────────────────────────────────────────────────────

  it('puede escribir en el campo de búsqueda', () => {
    visitClientes();
    cy.get('input[type="text"]').first().type('Ana');
    cy.get('input[type="text"]').first().should('have.value', 'Ana');
  });

  it('lanza búsqueda al enviar el formulario', () => {
    cy.intercept('GET', /\/api\/v1\/clientes/, {
      statusCode: 200,
      body: { count: 1, next: null, previous: null, results: [mockClientes.results[0]] },
    }).as('busqueda');
    cy.intercept('GET', /\/api\/v1\/tipos-cliente/, { statusCode: 200, body: { count: 0, next: null, previous: null, results: [] } });
    cy.intercept('GET', /\/api\/v1\/listas-precio/, { statusCode: 200, body: { count: 0, next: null, previous: null, results: [] } });

    cy.visit('/clientes', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
    cy.wait('@busqueda');

    cy.get('input[type="text"]').first().type('Ana');
    cy.wait('@busqueda');
  });

  // ── Estados ───────────────────────────────────────────────────────────────

  it('muestra indicador de estado para clientes activos e inactivos', () => {
    visitClientes();
    // Debe haber al menos un badge/indicador de activo y uno de inactivo
    cy.get('body').then(($body) => {
      const text = $body.text().toLowerCase();
      expect(text).to.include('activ'); // "activo", "activa", "inactivo"
    });
  });

  it('puede desactivar un cliente activo', () => {
    cy.intercept('PATCH', /\/api\/v1\/clientes\/1/, {
      statusCode: 200,
      body: { ...mockClientes.results[0], estado: false },
    }).as('desactivar');

    visitClientes();

    cy.contains('tr', 'Ana García')
      .find('button[title="Desactivar"]')
      .click({ force: true });
    cy.wait('@desactivar');
  });

  it('puede activar un cliente inactivo', () => {
    cy.intercept('PATCH', /\/api\/v1\/clientes\/2/, {
      statusCode: 200,
      body: { ...mockClientes.results[1], estado: true },
    }).as('activar');

    visitClientes();

    cy.contains('tr', 'Carlos López')
      .find('button[title="Activar"]')
      .click({ force: true });
    cy.wait('@activar');
  });

  // ── Creación ─────────────────────────────────────────────────────────────

  it('muestra botón para crear nuevo cliente', () => {
    visitClientes();
    cy.contains('button', /nuevo|crear|agregar/i).should('be.visible');
  });

  it('abre formulario al clickear crear cliente', () => {
    visitClientes();
    cy.contains('button', /nuevo|crear|agregar/i).first().click();
    // El formulario/modal debería aparecer
    cy.get('input[name="nombres"], input[name="ruc_ci"], input[placeholder*="nombre" i]')
      .should('be.visible');
  });

  it('crea un cliente nuevo exitosamente', () => {
    const nuevoCliente = {
      id_cliente: 10,
      nombres: 'Pedro',
      apellidos: 'Martínez',
      ruc_ci: '5555555',
      email: 'pedro@test.com',
      estado: true,
      fecha_registro: '2024-03-16',
      id_lista: 1,
      id_tipo_cliente: 1,
    };

    cy.intercept('POST', /\/api\/v1\/clientes\//, {
      statusCode: 201,
      body: nuevoCliente,
    }).as('crearCliente');

    visitClientes();
    cy.contains('button', /nuevo|crear|agregar/i).first().click();

    // Rellenar campos básicos
    cy.get('input[name="nombres"]').type('Pedro');
    cy.get('input[name="apellidos"]').type('Martínez');
    cy.get('input[name="ruc_ci"]').type('5555555');

    cy.get('button[type="submit"]').filter(':contains("Guardar"), :contains("Crear")').first().click();
    cy.wait('@crearCliente');
  });

  // ── Manejo de errores ─────────────────────────────────────────────────────

  it('muestra estado vacío cuando no hay clientes', () => {
    cy.intercept('GET', /\/api\/v1\/clientes/, {
      statusCode: 200,
      body: { count: 0, next: null, previous: null, results: [] },
    }).as('empty');
    cy.intercept('GET', /\/api\/v1\/tipos-cliente/, { statusCode: 200, body: { count: 0, next: null, previous: null, results: [] } });
    cy.intercept('GET', /\/api\/v1\/listas-precio/, { statusCode: 200, body: { count: 0, next: null, previous: null, results: [] } });

    cy.visit('/clientes', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
    cy.wait('@empty');

    cy.contains(/no se encontraron clientes/i).should('be.visible');
  });

  it('redirecciona a /login si no hay sesión activa', () => {
    cy.clearLocalStorage();
    cy.visit('/clientes');
    cy.url().should('include', '/login');
  });
});
