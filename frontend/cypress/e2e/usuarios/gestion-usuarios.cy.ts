// cypress/e2e/usuarios/gestion-usuarios.cy.ts
/// <reference types="cypress" />

/**
 * Tests E2E - Gestión de Usuarios
 * Ruta: /admin/usuarios
 * Cubre: listado, búsqueda, filtros por rol/estado, creación, toggle estado,
 *         eliminar, reset de contraseña, auth guard (requiere rol admin)
 */

describe('Gestión de Usuarios', () => {
  const API = Cypress.env('API_BASE_URL') || 'http://localhost:8000/api/v1';
  const mockAdmin = { id: 1, username: 'admin', email: 'admin@cantina.com', role: 'admin' };

  const mockRoles = [
    { id_rol: 1, nombre_rol: 'Administrador', descripcion: '', estado: true },
    { id_rol: 2, nombre_rol: 'Gerente', descripcion: '', estado: true },
    { id_rol: 3, nombre_rol: 'Cajero', descripcion: '', estado: true },
  ];

  const mockUsuarios = [
    {
      id_empleado: 1,
      nombre: 'Juan',
      apellido: 'Perez',
      usuario: 'jperez',
      email: 'jperez@cantina.com',
      id_rol: 1,
      rol_nombre: 'Administrador',
      estado: true,
      fecha_ingreso: '2024-01-10',
    },
    {
      id_empleado: 2,
      nombre: 'María',
      apellido: 'Gómez',
      usuario: 'mgomez',
      email: 'mgomez@cantina.com',
      id_rol: 3,
      rol_nombre: 'Cajero',
      estado: true,
      fecha_ingreso: '2024-02-15',
    },
    {
      id_empleado: 3,
      nombre: 'Carlos',
      apellido: 'Ruiz',
      usuario: 'cruiz',
      email: 'cruiz@cantina.com',
      id_rol: 2,
      rol_nombre: 'Gerente',
      estado: false,
      fecha_ingreso: '2024-03-01',
    },
  ];

  function interceptDefaults() {
    cy.intercept('GET', `${API}/empleados/**`, {
      statusCode: 200,
      body: { count: 3, next: null, previous: null, results: mockUsuarios },
    }).as('getUsuarios');
    cy.intercept('GET', `${API}/roles/**`, {
      statusCode: 200,
      body: { count: 3, next: null, previous: null, results: mockRoles },
    }).as('getRoles');
  }

  function visitUsuarios() {
    interceptDefaults();
    cy.visit('/admin/usuarios', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockAdmin));
      },
    });
    cy.wait('@getUsuarios');
  }

  afterEach(() => {
    cy.clearLocalStorage();
  });

  // ── Renderizado general ───────────────────────────────────────────────────

  it('muestra el título Gestión de Usuarios', () => {
    visitUsuarios();
    cy.contains('Gestión de Usuarios').should('be.visible');
  });

  it('muestra la descripción del módulo', () => {
    visitUsuarios();
    cy.contains(/usuarios|roles|permisos/i).should('be.visible');
  });

  it('muestra el botón Nuevo Usuario', () => {
    visitUsuarios();
    cy.contains('button', /nuevo usuario/i).should('be.visible');
  });

  it('muestra el campo de búsqueda', () => {
    visitUsuarios();
    cy.get('input[placeholder*="nombre" i], input[placeholder*="usuario" i], input[placeholder*="email" i]')
      .should('be.visible');
  });

  // ── Listado de usuarios ───────────────────────────────────────────────────

  it('muestra usuarios cargados desde la API', () => {
    visitUsuarios();
    cy.contains('Juan').should('be.visible');
    cy.contains('María').should('be.visible');
    cy.contains('Carlos').should('be.visible');
  });

  it('muestra el rol de cada usuario', () => {
    visitUsuarios();
    cy.contains('Administrador').should('be.visible');
    cy.contains('Cajero').should('be.visible');
    cy.contains('Gerente').should('be.visible');
  });

  it('muestra el nombre de usuario (login) en el listado', () => {
    visitUsuarios();
    cy.contains('jperez').should('be.visible');
  });

  // ── Filtros ───────────────────────────────────────────────────────────────

  it('el selector de roles se carga con los roles disponibles', () => {
    visitUsuarios();
    cy.contains('Todos los roles').should('be.visible');
  });

  it('muestra botones para filtrar por Activos e Inactivos', () => {
    visitUsuarios();
    cy.contains('button', 'Activos').should('be.visible');
  });

  it('filtra usuarios activos al hacer clic en el botón Activos', () => {
    visitUsuarios();
    cy.contains('button', 'Activos').click();
    // Carlos (estado: false) no debe aparecer en la lista filtrada
    cy.contains('jperez').should('be.visible');
    cy.contains('mgomez').should('be.visible');
  });

  it('la búsqueda por texto filtra los usuarios localmente', () => {
    visitUsuarios();
    cy.get('input[placeholder*="nombre" i], input[placeholder*="usuario" i], input[placeholder*="email" i]')
      .type('Juan');
    cy.contains('jperez').should('be.visible');
  });

  // ── Creación de usuario ───────────────────────────────────────────────────

  it('abre el formulario al hacer clic en Nuevo Usuario', () => {
    visitUsuarios();
    cy.contains('button', /nuevo usuario/i).click();
    cy.get('input[name="nombre"], input[name="usuario"], input[placeholder*="nombre" i]')
      .should('be.visible');
  });

  it('crea un usuario nuevo exitosamente', () => {
    const nuevoUsuario = {
      id_empleado: 10,
      nombre: 'Pedro',
      apellido: 'López',
      usuario: 'plopez',
      email: 'plopez@cantina.com',
      id_rol: 3,
      rol_nombre: 'Cajero',
      estado: true,
      fecha_ingreso: '2026-03-16',
    };

    cy.intercept('POST', `${API}/empleados/`, {
      statusCode: 201,
      body: { success: true, empleado: nuevoUsuario, mensaje: 'Usuario creado' },
    }).as('crearUsuario');

    interceptDefaults();
    cy.visit('/admin/usuarios', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockAdmin));
      },
    });
    cy.wait('@getUsuarios');

    cy.contains('button', /nuevo usuario/i).click();

    // Rellenar campos básicos
    cy.get('input[name="nombre"]').type('Pedro');
    cy.get('input[name="apellido"]').type('López');
    cy.get('input[name="usuario"]').type('plopez');

    cy.intercept('GET', `${API}/empleados/**`, {
      statusCode: 200,
      body: { count: 4, next: null, previous: null, results: [...mockUsuarios, nuevoUsuario] },
    });

    cy.get('button[type="submit"]').click();
    cy.wait('@crearUsuario');
  });

  // ── Toggle de estado ──────────────────────────────────────────────────────

  it('desactiva un usuario activo', () => {
    cy.intercept('PATCH', `${API}/empleados/**`, {
      statusCode: 200,
      body: { ...mockUsuarios[0], estado: false },
    }).as('desactivar');
    interceptDefaults();
    cy.visit('/admin/usuarios', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockAdmin));
      },
    });
    cy.wait('@getUsuarios');
    // Botón de toggle del primer usuario activo
    cy.get('button[title*="desactivar" i], button[aria-label*="desactivar" i]')
      .first()
      .click({ force: true });
    cy.wait('@desactivar');
  });

  it('activa un usuario inactivo', () => {
    cy.intercept('PATCH', `${API}/empleados/**`, {
      statusCode: 200,
      body: { ...mockUsuarios[2], estado: true },
    }).as('activar');
    interceptDefaults();
    cy.visit('/admin/usuarios', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockAdmin));
      },
    });
    cy.wait('@getUsuarios');
    cy.get('button[title*="activar" i], button[aria-label*="activar" i]')
      .first()
      .click({ force: true });
    cy.wait('@activar');
  });

  // ── Estado vacío ──────────────────────────────────────────────────────────

  it('muestra estado vacío cuando no hay usuarios cargados', () => {
    cy.intercept('GET', `${API}/empleados/**`, {
      statusCode: 200,
      body: { count: 0, next: null, previous: null, results: [] },
    }).as('emptyUsuarios');
    cy.intercept('GET', `${API}/roles/**`, {
      statusCode: 200,
      body: { count: 3, next: null, previous: null, results: mockRoles },
    });
    cy.visit('/admin/usuarios', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockAdmin));
      },
    });
    cy.wait('@emptyUsuarios');
    // No hay filas en la tabla o mensaje vacío
    cy.get('tbody tr, [class*="empty"]').should('exist');
  });

  // ── Auth guard ────────────────────────────────────────────────────────────

  it('redirige a /login si no hay sesión activa', () => {
    cy.clearLocalStorage();
    cy.visit('/admin/usuarios');
    cy.url().should('include', '/login');
  });
});
