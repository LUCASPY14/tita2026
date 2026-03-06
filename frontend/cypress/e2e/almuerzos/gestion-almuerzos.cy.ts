// cypress/e2e/almuerzos/gestion-almuerzos.cy.ts
/// <reference types="cypress" />

describe('Gestión de Almuerzos', () => {
  beforeEach(() => {
    cy.fixture('users').then((users) => {
      cy.login(users.admin.email, users.admin.password)
    })
    cy.visit('/almuerzos')
  })

  afterEach(() => {
    cy.logout()
  })

  it('debe mostrar interfaz de gestión de almuerzos', () => {
    cy.get('[data-testid="lunch-management"]').should('be.visible')
    cy.get('[data-testid="lunch-calendar"]').should('be.visible')
    cy.get('[data-testid="menu-configurator"]').should('be.visible')
    cy.get('[data-testid="student-list"]').should('be.visible')
  })

  it('debe configurar menú del día', () => {
    // Seleccionar fecha
    cy.get('[data-testid="date-picker"]').click()
    cy.get('[data-testid="tomorrow-date"]').click()
    
    // Configurar menú
    cy.get('[data-testid="setup-menu-button"]').click()
    cy.get('[data-testid="menu-modal"]').should('be.visible')
    
    // Añadir plato principal
    cy.get('[data-testid="main-dish-input"]').type('Milanesa con puré')
    cy.get('[data-testid="main-dish-price"]').clear().type('25000')
    
    // Añadir acompañamiento
    cy.get('[data-testid="side-dish-input"]').type('Ensalada fresca')
    
    // Añadir postre
    cy.get('[data-testid="dessert-input"]').type('Flan casero')
    
    // Guardar menú
    cy.get('[data-testid="save-menu-button"]').click()
    
    cy.verifySuccessToast('Menú configurado exitosamente')
    cy.get('[data-testid="menu-preview"]').should('contain.text', 'Milanesa con puré')
  })

  it('debe registrar almuerzo de estudiante', () => {
    cy.fixture('tarjetas').then((tarjetas) => {
      // Escanear tarjeta de estudiante
      cy.get('[data-testid="student-card-input"]').type(tarjetas.tarjeta_activa.nro_tarjeta)
      cy.get('[data-testid="scan-student-card"]').click()
      
      cy.waitForLoad()
      
      // Verificar información del estudiante
      cy.get('[data-testid="student-info"]').should('be.visible')
      cy.get('[data-testid="student-name"]').should('be.visible')
      cy.get('[data-testid="card-balance"]').should('be.visible')
      
      // Registrar almuerzo
      cy.get('[data-testid="register-lunch-button"]').should('not.be.disabled')
      cy.clickWhenReady('[data-testid="register-lunch-button"]')
      
      // Confirmar registro
      cy.get('[data-testid="lunch-confirmation"]').should('be.visible')
      cy.get('[data-testid="confirm-lunch-button"]').click()
      
      cy.verifySuccessToast('Almuerzo registrado exitosamente')
      cy.get('[data-testid="lunch-receipt"]').should('be.visible')
    })
  })

  it('debe validar restricciones de horario', () => {
    // Simular horario fuera del permitido
    cy.clock(new Date(2024, 2, 6, 15, 30)) // 3:30 PM
    
    cy.fixture('tarjetas').then((tarjetas) => {
      cy.get('[data-testid="student-card-input"]').type(tarjetas.tarjeta_activa.nro_tarjeta)
      cy.get('[data-testid="scan-student-card"]').click()
      
      cy.get('[data-testid="register-lunch-button"]').click()
      
      // Verificar restricción de horario
      cy.verifyErrorToast('Horario de almuerzo cerrado')
      cy.get('[data-testid="schedule-restriction-modal"]').should('be.visible')
    })
  })

  it('debe prevenir doble registro de almuerzo', () => {
    cy.fixture('tarjetas').then((tarjetas) => {
      // Primer registro
      cy.get('[data-testid="student-card-input"]').type(tarjetas.tarjeta_activa.nro_tarjeta)
      cy.get('[data-testid="scan-student-card"]').click()
      cy.clickWhenReady('[data-testid="register-lunch-button"]')
      cy.get('[data-testid="confirm-lunch-button"]').click()
      
      // Intentar segundo registro el mismo día
      cy.get('[data-testid="student-card-input"]').clear().type(tarjetas.tarjeta_activa.nro_tarjeta)
      cy.get('[data-testid="scan-student-card"]').click()
      
      // Verificar prevención de doble registro
      cy.get('[data-testid="already-registered-warning"]').should('be.visible')
      cy.get('[data-testid="register-lunch-button"]').should('be.disabled')
    })
  })

  it('debe generar reporte de almuerzos del día', () => {
    // Ir a reportes
    cy.get('[data-testid="reports-tab"]').click()
    
    // Generar reporte diario
    cy.get('[data-testid="daily-report-button"]').click()
    cy.get('[data-testid="report-modal"]').should('be.visible')
    
    // Verificar contenido del reporte
    cy.get('[data-testid="total-lunches"]').should('be.visible')
    cy.get('[data-testid="total-revenue"]').should('be.visible')
    cy.get('[data-testid="students-list"]').should('be.visible')
    
    // Exportar reporte
    cy.get('[data-testid="export-pdf-button"]').click()
    cy.verifySuccessToast('Reporte exportado exitosamente')
  })

  it('debe manejar estudiantes con saldo insuficiente', () => {
    cy.fixture('tarjetas').then((tarjetas) => {
      // Escanear tarjeta con poco saldo
      cy.get('[data-testid="student-card-input"]').type('SALDO_BAJO_001')
      cy.get('[data-testid="scan-student-card"]').click()
      
      // Intentar registrar almuerzo
      cy.get('[data-testid="register-lunch-button"]').click()
      
      // Verificar manejo de saldo insuficiente
      cy.get('[data-testid="insufficient-balance-modal"]').should('be.visible')
      cy.get('[data-testid="suggest-recharge-button"]').should('be.visible')
      cy.get('[data-testid="allow-debt-button"]').should('be.visible')
      
      // Permitir deuda (si está configurado)
      cy.get('[data-testid="allow-debt-button"]').click()
      cy.get('[data-testid="debt-authorization-input"]').type('Autorización supervisor')
      cy.get('[data-testid="confirm-debt-button"]').click()
      
      cy.verifySuccessToast('Almuerzo registrado con deuda autorizada')
    })
  })

  it('debe configurar menú especial para eventos', () => {
    // Crear evento especial
    cy.get('[data-testid="special-event-button"]').click()
    cy.get('[data-testid="event-modal"]').should('be.visible')
    
    // Configurar evento
    cy.get('[data-testid="event-name"]').type('Día del Estudiante')
    cy.get('[data-testid="event-date"]').type('2024-03-15')
    cy.get('[data-testid="special-menu"]').type('Pizza party con bebida')
    cy.get('[data-testid="special-price"]').clear().type('30000')
    
    // Guardar evento
    cy.get('[data-testid="save-event-button"]').click()
    
    cy.verifySuccessToast('Evento especial configurado')
    cy.get('[data-testid="calendar"]')
      .should('contain.text', 'Día del Estudiante')
  })

  it('debe visualizar estadísticas de consumo', () => {
    // Ir a estadísticas
    cy.get('[data-testid="statistics-tab"]').click()
    
    // Verificar gráficos y métricas
    cy.get('[data-testid="consumption-chart"]').should('be.visible')
    cy.get('[data-testid="weekly-stats"]').should('be.visible')
    cy.get('[data-testid="top-students"]').should('be.visible')
    cy.get('[data-testid="revenue-metrics"]').should('be.visible')
    
    // Filtrar por rango de fechas
    cy.get('[data-testid="date-range-picker"]').click()
    cy.get('[data-testid="last-month"]').click()
    
    cy.waitForLoad()
    
    // Verificar actualización de datos
    cy.get('[data-testid="stats-last-updated"]').should('be.visible')
  })
})