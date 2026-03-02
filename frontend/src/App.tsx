import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import Routes from './routes';
import { ToastProvider } from './utils/toast';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <ToastProvider />
      <Routes />
    </BrowserRouter>
  );
};

export default App;

