import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './assets/styles/global.css';
import { swManager } from './utils/serviceWorker';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Registrar Service Worker para PWA
if (import.meta.env.PROD) {
  swManager.register().then((result) => {
    if (result.isSupported && result.registration) {
      console.log('🚀 PWA Service Worker registrado exitosamente');
    } else if (result.error) {
      console.error('❌ Error registrando Service Worker:', result.error);
    } else {
      console.log('⚠️  Service Workers no soportados en este navegador');
    }
  });
}
