import React from 'react';
import { ShoppingCart, Trash2, Plus, Minus } from 'lucide-react';
import { Button, Card, Badge } from '../../../components/common';
import type { Producto } from '../../../types';

interface ItemCarrito {
  producto: Producto;
  cantidad: number;
  subtotal: number;
}

interface CarritoComprasProps {
  items: ItemCarrito[];
  onActualizarCantidad: (productoId: number, nuevaCantidad: number) => void;
  onRemoverItem: (productoId: number) => void;
  onLimpiar: () => void;
  onProcesar: () => void;
}

const CarritoCompras: React.FC<CarritoComprasProps> = ({
  items,
  onActualizarCantidad,
  onRemoverItem,
  onLimpiar,
  onProcesar,
}) => {
  const total = items.reduce((sum, item) => sum + item.subtotal, 0);

  const formatearPrecio = (precio?: number): string => {
    if (!precio) return 'Gs. 0';
    return `Gs. ${precio.toLocaleString('es-PY')}`;
  };

  return (
    <Card className="sticky top-6">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b pb-4">
          <div className="flex items-center gap-2">
            <ShoppingCart className="h-5 w-5 text-amber-600" />
            <h3 className="text-lg font-semibold text-gray-900">Carrito</h3>
          </div>
          <Badge variant="primary">{items.length} items</Badge>
        </div>

        {/* Items */}
        {items.length === 0 ? (
          <div className="py-8 text-center">
            <ShoppingCart className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-4 text-sm text-gray-500">
              El carrito está vacío
            </p>
            <p className="mt-1 text-xs text-gray-400">
              Agrega productos para comenzar
            </p>
          </div>
        ) : (
          <>
            <div className="max-h-96 space-y-3 overflow-y-auto">
              {items.map((item) => (
                <div
                  key={item.producto.id_producto}
                  className="rounded-lg border border-gray-200 bg-gray-50 p-3"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="text-sm font-medium text-gray-900">
                        {item.producto.descripcion}
                      </h4>
                      <p className="mt-1 text-xs text-gray-500">
                        {formatearPrecio(item.producto.precio)} c/u
                      </p>
                    </div>
                    <button
                      onClick={() => onRemoverItem(item.producto.id_producto)}
                      className="text-red-600 hover:text-red-700"
                      title="Eliminar"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="mt-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() =>
                          onActualizarCantidad(
                            item.producto.id_producto,
                            item.cantidad - 1
                          )
                        }
                        className="rounded-md border border-gray-300 bg-white p-1 hover:bg-gray-100"
                        disabled={item.cantidad <= 1}
                      >
                        <Minus className="h-4 w-4" />
                      </button>
                      <span className="w-8 text-center font-medium">
                        {item.cantidad}
                      </span>
                      <button
                        onClick={() =>
                          onActualizarCantidad(
                            item.producto.id_producto,
                            item.cantidad + 1
                          )
                        }
                        className="rounded-md border border-gray-300 bg-white p-1 hover:bg-gray-100"
                      >
                        <Plus className="h-4 w-4" />
                      </button>
                    </div>

                    <p className="text-sm font-bold text-gray-900">
                      {formatearPrecio(item.subtotal)}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Divider */}
            <div className="border-t pt-4">
              <div className="flex items-center justify-between">
                <span className="text-lg font-semibold text-gray-900">Total</span>
                <span className="text-2xl font-bold text-amber-600">
                  {formatearPrecio(total)}
                </span>
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-2">
              <Button
                variant="primary"
                fullWidth
                onClick={onProcesar}
                disabled={items.length === 0}
                className="h-12 text-base font-bold"
                leftIcon={<ShoppingCart className="h-5 w-5" />}
              >
                Procesar Venta
              </Button>
              <Button
                variant="outline"
                fullWidth
                onClick={onLimpiar}
              >
                Limpiar Carrito
              </Button>
            </div>
          </>
        )}
      </div>
    </Card>
  );
};

export default CarritoCompras;
