import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import Routes from './routes';
import { ToastProvider } from './utils/toast';
import { AuthProvider } from './contexts/AuthContext';
import { PermissionsProvider } from './contexts/PermissionsContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { PortalAuthProvider } from './contexts/PortalAuthContext';
// Configurar interceptores de axios para tracking automático
import './utils/axiosConfig';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <PortalAuthProvider>
          <PermissionsProvider>
            <NotificationProvider>
              <ToastProvider />
              <Routes />
            </NotificationProvider>
          </PermissionsProvider>
        </PortalAuthProvider>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;

