import { useAuthContext } from '../contexts/AuthContext';

/**
 * Hook de autenticación — delega al AuthContext global.
 * Usar este hook en componentes para acceder a login, logout, user, etc.
 */
export const useAuth = () => useAuthContext();
