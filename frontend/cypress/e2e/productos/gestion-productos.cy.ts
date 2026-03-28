// cypress/e2e/productos/gestion-productos.cy.ts
/// <reference types="cypress" />

/**
 * Tests E2E - Gestión de Productos
 * Ruta: /productos
 * Cubre: listado, búsqueda, filtros, creación, toggle estado, vacío, auth guard
 */

describe('Gestión de Productos', () => {
  const API = Cypress.env('API_BASE_URL') || 'http://localhost:8000/api/v1';
  const mockUser = { id: 1, username: 'admin', email: 'admin@cantina.com', role: 'admin' };

  const mockCategorias = {
    count: 2,
    next: null,
    previous: null,
    results: [
      { id_categoria: 1, nombre: 'Bebidas', estado: true },
      { id_categoria: 2, nombre: 'Comidas', estado: true },
    ],
  };

  const mockProductos = {
    count: 3,
    next: null,
    previous: null,
    results: [
      {
        id_producto: 1,
        codigo_barra: 'BEB001',
        descripcion: 'Coca Cola 500ml',
        precio_venta: 5000,
        stock_actual: 50,
        stock_minimo: 10,
        estado: true,
        id_categoria: 1,
        categoria_nombre: 'Bebidas',
        id_impuesto: 1,
        permite_stock_negativo: false,
      },
      {
        id_producto: 2,
        codigo_barra: 'COM001',
        descripcion: 'Hamburguesa completa',
        precio_venta: 25000,
        stock_actual: 15,
        stock_minimo: 5,
        estado: true,
        id_categoria: 2,
        categoria_nombre: 'Comidas',
        id_impuesto: 1,
        permite_stock_negativo: false,
      },
      {
        id_producto: 3,
        codigo_barra: 'BEB002',
        descripcion: 'Agua mineral 1L',
        precio_venta: 3000,
        stock_actual: 2,
        stock_minimo: 10,
        estado: false,
        id_categoria: 1,
        categoria_nombre: 'Bebidas',
        id_impuesto: 1,
        permite_stock_negativo: false,
      },
    ],
  };

  function interceptDefaults() {
    cy.intercept('GET', /\/api\/v1\/productos/, { statusCode: 200, body: mockProductos }).as('getProductos');
    cy.intercept('GET', /\/api\/v1\/categorias/, { statusCode: 200, body: mockCategorias }).as('getCategorias');
    cy.intercept('GET', /\/api\/v1\/unidades-medida/, { statusCode: 200, body: [] });
    cy.intercept('GET', /\/api\/v1\/impuestos/, { statusCode: 200, body: [] });
  }

  function visitProductos() {
    interceptDefaults();
    cy.visit('/productos', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
    cy.wait('@getProductos');
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

  // ── Renderizado general ───────────────────────────────────────────────────

  it('muestra el título Gestión de Productos', () => {
    visitProductos();
    cy.contains('Gestión de Productos').should('be.visible');
  });

  it('muestra el botón Nuevo Producto', () => {
    visitProductos();
    cy.contains('button', /nuevo producto/i).should('be.visible');
  });

  it('muestra las columnas de la tabla', () => {
    visitProductos();
    cy.contains(/código/i).should('be.visible');
    cy.contains(/producto/i).should('be.visible');
    cy.contains(/categoría/i).should('be.visible');
    cy.contains(/stock/i).should('be.visible');
    cy.contains(/precio/i).should('be.visible');
    cy.contains(/estado/i).should('be.visible');
  });

  // ── Listado de productos ──────────────────────────────────────────────────

  it('muestra productos cargados desde la API', () => {
    visitProductos();
    cy.contains('Coca Cola 500ml').should('be.visible');
    cy.contains('Hamburguesa completa').should('be.visible');
  });

  it('muestra el código de barra del producto', () => {
    visitProductos();
    cy.contains('BEB001').should('be.visible');
  });

  it('muestra la categoría del producto', () => {
    visitProductos();
    cy.contains('Bebidas').should('be.visible');
    cy.contains('Comidas').should('be.visible');
  });

  // ── Filtros ───────────────────────────────────────────────────────────────

  it('muestra campo de búsqueda de productos', () => {
    visitProductos();
    cy.get('input[type="text"], input[placeholder*="buscar" i], input[placeholder*="producto" i]')
      .should('be.visible');
  });

  it('filtro Activos limita los resultados', () => {
    cy.intercept('GET', /\/api\/v1\/productos/, (req) => {
      if (req.query.estado === 'true') {
        req.reply({
          statusCode: 200,
          body: { count: 2, next: null, previous: null, results: mockProductos.results.filter(p => p.estado) },
        });
      } else {
        req.reply({ statusCode: 200, body: mockProductos });
      }
    }).as('filtroActivos');
    cy.intercept('GET', /\/api\/v1\/categorias/, { statusCode: 200, body: mockCategorias });
    cy.intercept('GET', /\/api\/v1\/unidades-medida/, { statusCode: 200, body: [] });
    cy.visit('/productos', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
    cy.wait('@filtroActivos');
    cy.contains('button', 'Activos').click();
    cy.wait('@filtroActivos');
  });

  it('el selector de categoría se carga con las categorías disponibles', () => {
    visitProductos();
    cy.contains('Todas las categorías').should('be.visible');
  });

  // ── Creación de producto ──────────────────────────────────────────────────

  it('abre el formulario al hacer clic en Nuevo Producto', () => {
    visitProductos();
    cy.contains('button', /nuevo producto/i).click();
    cy.get('input[name="descripcion"], input[placeholder*="nombre" i], input[placeholder*="descripción" i]')
      .should('be.visible');
  });

  it('muestra el formulario con campos requeridos', () => {
    visitProductos();
    cy.contains('button', /nuevo producto/i).click();
    // Campos básicos del formulario producto
    cy.get('input, select, textarea').should('have.length.greaterThan', 2);
  });

  it('crea un producto nuevo exitosamente y vuelve al listado', () => {
    const nuevoProducto = {
      id_producto: 10,
      codigo_barra: 'NEW001',
      descripcion: 'Producto nuevo',
      precio_venta: 10000,
      stock_actual: 100,
      stock_minimo: 5,
      estado: true,
      id_categoria: 1,
      id_impuesto: 1,
    };

    cy.intercept('POST', /\/api\/v1\/productos\//, {
      statusCode: 201,
      body: nuevoProducto,
    }).as('crearProducto');
    cy.intercept('GET', /\/api\/v1\/productos/, { statusCode: 200, body: mockProductos }).as('getProductos2');
    cy.intercept('GET', /\/api\/v1\/categorias/, { statusCode: 200, body: mockCategorias });
    cy.intercept('GET', /\/api\/v1\/unidades-medida/, { statusCode: 200, body: [] });
    cy.intercept('GET', /\/api\/v1\/impuestos/, { statusCode: 200, body: [{ id_impuesto: 2, nombre_impuesto: 'IVA 10%', valor: 10 }] });

    cy.visit('/productos', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
    cy.wait('@getProductos2');
    cy.contains('button', /nuevo producto/i).click();

    // Llenar formulario
    cy.get('input[name="descripcion"]').type('Producto nuevo');
    cy.get('select[name="id_categoria"]').select('Bebidas');

    cy.intercept('GET', /\/api\/v1\/productos/, { statusCode: 200, body: mockProductos });
    cy.get('button[type="submit"]').click();
    cy.wait('@crearProducto');
    // Debe volver al listado
    cy.contains('h1', 'Gestión de Productos').scrollIntoView().should('be.visible');
  });

  // ── Toggle de estado ──────────────────────────────────────────────────────

  it('muestra botones de acción para cada producto', () => {
    visitProductos();
    cy.get('button[title*="editar" i], button[title*="ver" i], button[title*="estado" i], button[title*="activar" i], button[title*="desactivar" i], button[title*="eliminar" i]')
      .should('have.length.greaterThan', 0);
  });

  it('cambia el estado de un producto al hacer toggle', () => {
    cy.intercept('PATCH', /\/api\/v1\/productos/, {
      statusCode: 200,
      body: { ...mockProductos.results[0], estado: false },
    }).as('toggleEstado');
    interceptDefaults();
    cy.visit('/productos', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
    cy.wait('@getProductos');
    cy.get('button[title*="desactivar" i], button[title*="activar" i]')
      .first()
      .click({ force: true });
    cy.wait('@toggleEstado');
  });

  // ── Estado vacío ──────────────────────────────────────────────────────────

  it('muestra estado vacío cuando no hay productos', () => {
    cy.intercept('GET', /\/api\/v1\/productos/, {
      statusCode: 200,
      body: { count: 0, next: null, previous: null, results: [] },
    }).as('empty');
    cy.intercept('GET', /\/api\/v1\/categorias/, { statusCode: 200, body: mockCategorias });
    cy.intercept('GET', /\/api\/v1\/unidades-medida/, { statusCode: 200, body: [] });
    cy.visit('/productos', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
    cy.wait('@empty');
    cy.contains(/no hay productos/i).should('be.visible');
  });

  // ── Auth guard ────────────────────────────────────────────────────────────

  it('redirige a /login si no hay sesión activa', () => {
    cy.clearLocalStorage();
    cy.visit('/productos');
    cy.url().should('include', '/login');
  });
});
