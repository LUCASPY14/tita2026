import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import Routes from './routes';
import { ToastProvider } from './utils/toast';
import { AuthProvider } from './contexts/AuthContext';
import { PermissionsProvider } from './contexts/PermissionsContext';
// Configurar interceptores de axios para tracking automático
import './utils/axiosConfig';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <PermissionsProvider>
          <ToastProvider />
          <Routes />
        </PermissionsProvider>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;

