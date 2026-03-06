/**
 * Gestión de Ventas
 * Vista de administración: historial completo, búsqueda y seguimiento
 * separada del flujo de Punto de Venta (POS).
 */

import React from 'react';
import { HistorialVentas } from '../pos/components';

const Ventas: React.FC = () => (
  <div className="space-y-6">
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Gestión de Ventas</h1>
      <p className="text-gray-600 mt-1">
        Historial completo de ventas, filtros y seguimiento de pagos
      </p>
    </div>
    <HistorialVentas />
  </div>
);

export default Ventas;
