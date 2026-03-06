// cypress/support/component.ts
// Import commands.js using ES2015 syntax:
import './commands'

// React Testing Library
import { mount } from '@cypress/react'

// Augment the Cypress namespace to include type definitions for
// your custom command.
declare global {
  namespace Cypress {
    interface Chainable {
      mount: typeof mount
    }
  }
}

Cypress.Commands.add('mount', mount)

// Example use:
// cy.mount(<MyComponent />)