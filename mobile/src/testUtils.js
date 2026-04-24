/**
 * Utilidades de testing para la aplicación móvil
 */

/**
 * Mock user data para tests
 */
export const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
};

/**
 * Mock token para tests
 */
export const mockToken = 'mock-auth-token-12345';

/**
 * Mock hijo con restricciones
 */
export const mockHijo = {
  id_hijo: 1,
  nombre: 'Juan',
  apellido: 'Pérez',
  fecha_nacimiento: '2015-05-10',
  grado: '3er grado',
  restricciones: [
    {
      id: 1,
      tipo: 'Alergia',
      tipo_restriccion: 'Alergia',
      descripcion: 'Maní',
      estado: true,
      severidad: 'alta',
      requiere_autorizacion: true,
    },
  ],
};

/**
 * Mock productos para tests
 */
export const mockProductos = [
  {
    id: 1,
    nombre: 'Pizza',
    descripcion: 'Pizza de mozzarella',
    precio: 25000,
    disponible: true,
    categoria: 'Comida',
  },
  {
    id: 2,
    nombre: 'Refresco',
    descripcion: 'Refresco de 500ml',
    precio: 5000,
    disponible: true,
    categoria: 'Bebidas',
  },
  {
    id: 3,
    nombre: 'Ensalada',
    descripcion: 'Ensalada verde',
    precio: 15000,
    disponible: true,
    categoria: 'Comida',
  },
];

/**
 * Mock carrito de compras
 */
export const mockCart = [
  {
    id: 1,
    nombre: 'Pizza',
    precio: 25000,
    cantidad: 2,
  },
  {
    id: 2,
    nombre: 'Refresco',
    precio: 5000,
    cantidad: 1,
  },
];

/**
 * Mock transacción SIPAP
 */
export const mockSIPAPTransaction = {
  txn_id: 'TXN123456',
  qr_image: 'data:image/png;base64,iVBORw0KGgoAAAANS...',
  monto: 50000,
  estado: 'pendiente',
  fecha_creacion: '2026-04-21T10:00:00Z',
  descripcion: 'Carga de saldo',
};

/**
 * Mock estado de pago aprobado
 */
export const mockPaymentApproved = {
  txn_id: 'TXN123456',
  estado: 'aprobado',
  fecha_confirmacion: '2026-04-21T10:05:00Z',
  monto: 50000,
};

/**
 * Mock estado de pago rechazado
 */
export const mockPaymentRejected = {
  txn_id: 'TXN123456',
  estado: 'rechazado',
  fecha_confirmacion: '2026-04-21T10:05:00Z',
  monto: 50000,
  motivo: 'Fondos insuficientes',
};

/**
 * Helper para esperar actualizaciones asíncronas
 */
export const waitForAsync = () => new Promise((resolve) => setImmediate(resolve));

/**
 * Helper para simular delay
 */
export const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Mock navigation helper
 */
export const createMockNavigation = (overrides = {}) => ({
  navigate: jest.fn(),
  goBack: jest.fn(),
  replace: jest.fn(),
  setOptions: jest.fn(),
  addListener: jest.fn(),
  removeListener: jest.fn(),
  ...overrides,
});

/**
 * Mock route helper
 */
export const createMockRoute = (params = {}) => ({
  params,
  key: 'test-route-key',
  name: 'TestScreen',
});

/**
 * Formatea monto en guaraníes con separador de miles
 */
export const formatCurrency = (amount) => {
  return amount.toLocaleString('es-PY');
};

/**
 * Mock de AsyncStorage con datos precargados
 */
export const mockAsyncStorageWithData = (data) => {
  const AsyncStorage = require('@react-native-async-storage/async-storage');
  
  Object.entries(data).forEach(([key, value]) => {
    AsyncStorage.getItem.mockImplementation((k) => {
      if (k === key) {
        return Promise.resolve(typeof value === 'string' ? value : JSON.stringify(value));
      }
      return Promise.resolve(null);
    });
  });
};

/**
 * Mock de SecureStore con datos precargados
 */
export const mockSecureStoreWithData = (data) => {
  const SecureStore = require('expo-secure-store');
  
  Object.entries(data).forEach(([key, value]) => {
    SecureStore.getItemAsync.mockImplementation((k) => {
      if (k === key) {
        return Promise.resolve(typeof value === 'string' ? value : JSON.stringify(value));
      }
      return Promise.resolve(null);
    });
  });
};
