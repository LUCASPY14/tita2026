# Testing - Aplicación Móvil Cantina Tita

## Configuración

El proyecto usa **Jest** con **React Native Testing Library** para las pruebas.

### Dependencias instaladas

```json
{
  "@testing-library/jest-native": "^5.4.3",
  "@testing-library/react-native": "^12.4.2",
  "jest": "^29.7.0",
  "jest-expo": "^50.0.1",
  "react-test-renderer": "18.2.0"
}
```

## Ejecutar Tests

```bash
# Ejecutar todos los tests
npm test

# Ejecutar tests en modo watch
npm run test:watch

# Ejecutar tests con cobertura
npm run test:coverage
```

## Estructura de Tests

```
mobile/
├── src/
│   ├── services/
│   │   └── __tests__/
│   │       ├── api.test.js
│   │       ├── auth.service.test.js
│   │       └── sipap.service.test.js
│   ├── screens/
│   │   └── __tests__/
│   │       ├── LoginScreen.test.js
│   │       ├── CartScreen.test.js
│   │       └── SIPAPPaymentScreen.test.js
│   └── __tests__/
│       └── testUtils.js
├── jest.setup.js
└── package.json
```

## Tests Implementados

### Servicios (src/services/__tests__/)

#### api.test.js
- ✅ Creación de instancia axios con configuración correcta
- ✅ Interceptor de request (adjunta token)
- ✅ Interceptor de response (maneja 401)

#### auth.service.test.js
- ✅ Login exitoso y almacenamiento de token
- ✅ Logout y limpieza de datos
- ✅ Obtención de token almacenado
- ✅ Verificación de autenticación
- ✅ Manejo de errores

#### sipap.service.test.js
- ✅ Generación de QR SIPAP
- ✅ Consulta de estado de pago
- ✅ Polling para confirmación de pago
- ✅ Timeout y manejo de errores
- ✅ Estados: aprobado, rechazado, expirado

### Pantallas (src/screens/__tests__/)

#### LoginScreen.test.js
- ✅ Renderizado del formulario
- ✅ Validación de campos vacíos
- ✅ Login exitoso y navegación
- ✅ Manejo de errores de autenticación
- ✅ Estados de carga
- ✅ Trim de espacios en username

#### CartScreen.test.js
- ✅ Renderizado de items del carrito
- ✅ Cálculo de total
- ✅ Carrito vacío
- ✅ Carga de restricciones
- ✅ Manejo de notas

#### SIPAPPaymentScreen.test.js
- ✅ Renderizado con datos de pago
- ✅ Generación de QR al montar
- ✅ Polling de estado de pago
- ✅ Manejo de pago aprobado/rechazado
- ✅ Formateo de montos

## Utilidades de Testing

El archivo `testUtils.js` proporciona:

- **Mock data**: usuarios, productos, transacciones
- **Helpers**: navigation mocks, route mocks
- **Formatters**: moneda, fechas
- **Setup helpers**: AsyncStorage, SecureStore mocks

### Ejemplo de uso

```javascript
import { mockUser, createMockNavigation, mockSIPAPTransaction } from '../testUtils';

const mockNavigation = createMockNavigation();
const route = { params: { user: mockUser } };
```

## Mocks Configurados (jest.setup.js)

- ✅ AsyncStorage
- ✅ SecureStore
- ✅ expo-image-picker
- ✅ @react-navigation/native

## Cobertura Objetivo

El objetivo es mantener una cobertura de código alta:

- **Servicios**: >90%
- **Pantallas**: >80%
- **Total**: >85%

## Comandos Útiles

```bash
# Ejecutar tests de un archivo específico
npm test -- LoginScreen.test.js

# Ejecutar tests con verbose output
npm test -- --verbose

# Actualizar snapshots
npm test -- -u

# Ver cobertura en HTML
npm run test:coverage && open coverage/lcov-report/index.html
```

## Próximos Tests a Implementar

- [ ] ProfileScreen.test.js
- [ ] MenuScreen.test.js
- [ ] RestrictionsScreen.test.js
- [ ] AddRestrictionScreen.test.js
- [ ] AccountScreen.test.js
- [ ] Tests de integración E2E

## Mejores Prácticas

1. **Nombrar tests descriptivamente**: Usa `it('should ...')` o `it('debería ...')`
2. **Arrange-Act-Assert**: Organiza el código de test en estas 3 secciones
3. **Mock solo lo necesario**: No sobre-mockear
4. **Limpiar entre tests**: Usa `beforeEach` y `afterEach`
5. **Tests independientes**: Cada test debe poder ejecutarse solo
6. **Evitar detalles de implementación**: Testea comportamiento, no implementación

## Troubleshooting

### Error: Cannot find module 'expo-secure-store'

```bash
npm install expo-secure-store
```

### Tests colgados o timeout

Asegúrate de que los mocks de async están configurados correctamente:

```javascript
jest.useFakeTimers();
// ... test code ...
jest.useRealTimers();
```

### Warning: act() wrapper

Usa `waitFor` de testing-library para operaciones asíncronas:

```javascript
await waitFor(() => {
  expect(someElement).toBeTruthy();
});
```
