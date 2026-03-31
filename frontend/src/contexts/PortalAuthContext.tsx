import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { portalAuthService, PortalUser } from '../services/portalAuth.service';

interface PortalAuthContextType {
  user: PortalUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const PortalAuthContext = createContext<PortalAuthContextType | undefined>(undefined);

export const PortalAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<PortalUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const stored = portalAuthService.getCurrentUser();
    if (portalAuthService.isAuthenticated() && stored) {
      setUser(stored);
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const portalUser = await portalAuthService.login(email, password);
    setUser(portalUser);
  }, []);

  const logout = useCallback(() => {
    portalAuthService.logout();
    setUser(null);
  }, []);

  return (
    <PortalAuthContext.Provider
      value={{ user, isAuthenticated: !!user, isLoading, login, logout }}
    >
      {children}
    </PortalAuthContext.Provider>
  );
};

export const usePortalAuth = (): PortalAuthContextType => {
  const ctx = useContext(PortalAuthContext);
  if (!ctx) throw new Error('usePortalAuth debe usarse dentro de PortalAuthProvider');
  return ctx;
};
