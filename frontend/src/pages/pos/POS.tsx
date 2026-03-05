import React, { useState, useEffect } from 'react';
import { ShoppingCart, History, RotateCcw } from 'lucide-react';
import { Card } from '../../components/common';
import { CatalogoProductos, CarritoCompras, ProcesarVenta, HistorialVentas, NotasCredito } from './components';
import type { ItemCarrito, Producto } from '../../types';

type Vista = 'pos' | 'historial' | 'devoluciones';

const POS: React.FC = () => {
  const [vista, setVista] = useState<Vista>('pos');
  const [carrito, setCarrito] = useState<ItemCarrito[]>([]);
  const [mostrarProcesar, setMostrarProcesar] = useState(false);

  const agregarAlCarrito = (producto: Producto, cantidad: number = 1) => {
    setCarrito(prev => {
      const itemExistente = prev.find(item => item.producto.id_producto === producto.id_producto);
      
      if (itemExistente) {
        // Incrementar cantidad del producto existente
        return prev.map(item =>
          item.producto.id_producto === producto.id_producto
            ? {
                ...item,
                cantidad: item.cantidad + cantidad,
                subtotal: (item.cantidad + cantidad) * item.precio_unitario,
              }
            : item
        );
      } else {
        // Agregar nuevo producto
        const precioUnitario = producto.precio || 0;
        return [
          ...prev,
          {
            producto,
            cantidad,
            precio_unitario: precioUnitario,
            subtotal: precioUnitario * cantidad,
          },
        ];
      }
    });
  };

  const actualizarCantidad = (productoId: number, cantidad: number) => {
    if (cantidad <= 0) {
      eliminarDelCarrito(productoId);
      return;
    }

    setCarrito(prev =>
      prev.map(item =>
        item.producto.id_producto === productoId
          ? {
              ...item,
              cantidad,
              subtotal: cantidad * item.precio_unitario,
            }
          : item
      )
    );
  };

  const eliminarDelCarrito = (productoId: number) => {
    setCarrito(prev => prev.filter(item => item.producto.id_producto !== productoId));
  };

  const vaciarCarrito = () => {
    setCarrito([]);
  };

  const handleVentaExitosa = () => {
    vaciarCarrito();
    setMostrarProcesar(false);
  };

  const totalCarrito = carrito.reduce((sum, item) => sum + item.subtotal, 0);
  const cantidadItems = carrito.reduce((sum, item) => sum + item.cantidad, 0);

  // Atajos de teclado
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignorar si hay un input/textarea activo
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

      if (e.key === 'Enter' && vista === 'pos' && carrito.length > 0 && !mostrarProcesar) {
        e.preventDefault();
        setMostrarProcesar(true);
      }
      if (e.key === 'Escape' && mostrarProcesar) {
        e.preventDefault();
        setMostrarProcesar(false);
      }
      if (e.key === 'F2' && vista === 'pos') {
        e.preventDefault();
        vaciarCarrito();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [vista, carrito.length, mostrarProcesar]);
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Punto de Venta</h1>
          <p className="mt-2 text-gray-600">
            Gestiona las ventas de productos de la cantina
          </p>
          <div className="mt-1 flex gap-3 text-xs text-gray-400">
            <span className="rounded bg-gray-100 px-1.5 py-0.5 font-mono">Enter</span> Procesar venta
            <span className="rounded bg-gray-100 px-1.5 py-0.5 font-mono">F2</span> Vaciar carrito
            <span className="rounded bg-gray-100 px-1.5 py-0.5 font-mono">Esc</span> Cerrar modal
          </div>
        </div>
        
        {/* Indicador de Carrito */}
        {vista === 'pos' && cantidadItems > 0 && (
          <div className="flex items-center gap-3 rounded-lg bg-amber-50 px-4 py-3">
            <ShoppingCart className="h-6 w-6 text-amber-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Carrito</p>
              <p className="text-lg font-bold text-amber-600">
                {cantidadItems} item{cantidadItems !== 1 && 's'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl bg-gray-100 p-1">
        <button
          type="button"
          onClick={() => setVista('pos')}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
            vista === 'pos'
              ? 'bg-white text-amber-700 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <ShoppingCart className="h-4 w-4" />
          Venta
          {cantidadItems > 0 && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-500 text-xs text-white">
              {cantidadItems}
            </span>
          )}
        </button>
        <button
          type="button"
          onClick={() => setVista('historial')}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
            vista === 'historial'
              ? 'bg-white text-amber-700 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <History className="h-4 w-4" />
          Historial de Ventas
        </button>
        <button
          type="button"
          onClick={() => setVista('devoluciones')}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
            vista === 'devoluciones'
              ? 'bg-white text-amber-700 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <RotateCcw className="h-4 w-4" />
          Devoluciones
        </button>
      </div>

      {/* Vista: POS */}
      {vista === 'pos' && (
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Columna izquierda: Catálogo */}
        <div className="lg:col-span-2">
          <Card title="Catálogo de Productos" subtitle="Selecciona productos para agregar a la venta">
            <CatalogoProductos onAgregarProducto={agregarAlCarrito} />
          </Card>
        </div>

        {/* Columna derecha: Carrito */}
        <div className="lg:col-span-1">
          <div className="space-y-4">
            <Card 
              title="Carrito de Compras" 
              subtitle={`${cantidadItems} producto${cantidadItems !== 1 ? 's' : ''}`}
            >
              <CarritoCompras
                items={carrito}
                onActualizarCantidad={actualizarCantidad}
                onRemoverItem={eliminarDelCarrito}
                onLimpiar={vaciarCarrito}
                onProcesar={() => setMostrarProcesar(true)}
              />
            </Card>

            {/* Resumen Total */}
            {carrito.length > 0 && (
              <div className="rounded-lg bg-gradient-to-r from-amber-50 to-yellow-50 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-lg font-semibold text-gray-700">Total a Pagar:</span>
                  <span className="text-2xl font-bold text-amber-600">
                    Gs. {totalCarrito.toLocaleString('es-PY')}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      )}

      {/* Vista: Historial */}
      {vista === 'historial' && (
        <Card title="Historial de Ventas" subtitle="Consulta y filtra todas las ventas realizadas">
          <HistorialVentas />
        </Card>
      )}

      {/* Vista: Devoluciones */}
      {vista === 'devoluciones' && (
        <Card title="Devoluciones y Notas de Crédito" subtitle="Gestiona las devoluciones y notas de crédito emitidas">
          <NotasCredito />
        </Card>
      )}

      {/* Modal de Procesar Venta */}
      {mostrarProcesar && (
        <ProcesarVenta
          items={carrito}
          total={totalCarrito}
          onCerrar={() => setMostrarProcesar(false)}
          onVentaExitosa={handleVentaExitosa}
        />
      )}
    </div>
  );
};

export default POS;
