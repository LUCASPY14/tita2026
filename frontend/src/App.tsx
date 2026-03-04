import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import Routes from './routes';
import { ToastProvider } from './utils/toast';
import { AuthProvider } from './contexts/AuthContext';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider />
        <Routes />
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;

