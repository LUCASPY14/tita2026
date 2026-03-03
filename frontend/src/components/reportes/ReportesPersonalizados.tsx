/**
 * Reportes Personalizados
 * 
 * Permite generar reportes específicos:
 * - Reporte de ventas
 * - Reporte de recargas
 * - Reporte de productos más vendidos
 * - Reporte de consumos por tarjeta
 * - Reporte financiero consolidado
 */

import { useState } from 'react';
import { FileText, Download, Calendar, Search, TrendingUp } from 'lucide-react';
import toast from 'react-hot-toast';

import { Card, Button, Input } from '../common';
import reportesService from '../../services/reportes.service';
import type {
  ReporteVentas,
  ReporteFinanciero
} from '../../types';

type TipoReporte = 'ventas' | 'recargas' | 'top-productos' | 'consumos-tarjeta' | 'financiero';

export default function ReportesPersonalizados() {
  const [tipoReporte, setTipoReporte] = useState<TipoReporte>('ventas');
  const [cargando, setCargando] = useState(false);
  
  // Filtros generales
  const [fechaInicio, setFechaInicio] = useState(
    new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [fechaFin, setFechaFin] = useState(new Date().toISOString().split('T')[0]);
  
  // Filtros específicos
  const [metodoPago, setMetodoPago] = useState('');
  const [nroTarjeta, setNroTarjeta] = useState('');
  const [limite, setLimite] = useState(20);

  // Resultados
  const [reporteVentas, setReporteVentas] = useState<ReporteVentas | null>(null);
  const [reporteFinanciero, setReporteFinanciero] = useState<ReporteFinanciero | null>(null);

  const generarReporte = async () => {
    setCargando(true);
    try {
      switch (tipoReporte) {
        case 'ventas':
          const ventas = await reportesService.getReporteVentas({
            fecha_inicio: fechaInicio,
            fecha_fin: fechaFin,
            metodo_pago: metodoPago || undefined
          });
          setReporteVentas(ventas);
          break;

        case 'recargas':
          await reportesService.getReporteRecargas({
            fecha_inicio: fechaInicio,
            fecha_fin: fechaFin,
            metodo_pago: metodoPago || undefined
          });
          break;

        case 'top-productos':
          await reportesService.getReporteTopProductos({
            fecha_inicio: fechaInicio,
            fecha_fin: fechaFin,
            limite
          });
          break;

        case 'consumos-tarjeta':
          if (!nroTarjeta) {
            toast.error('Debe ingresar un número de tarjeta');
            return;
          }
          await reportesService.getReporteConsumosTarjeta({
            nro_tarjeta: nroTarjeta,
            fecha_inicio: fechaInicio,
            fecha_fin: fechaFin
          });
          break;

        case 'financiero':
          const financiero = await reportesService.getReporteFinanciero({
            fecha_inicio: fechaInicio,
            fecha_fin: fechaFin
          });
          setReporteFinanciero(financiero);
          break;
      }
      
      toast.success('Reporte generado exitosamente');
    } catch (error) {
      console.error('Error generando reporte:', error);
      toast.error('Error al generar el reporte');
    } finally {
      setCargando(false);
    }
  };

  const formatearMoneda = (valor: number) => {
    return new Intl.NumberFormat('es-PY', {
      style: 'currency',
      currency: 'PYG',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(valor);
  };

  return (
    <div className="space-y-6">
      {/* Selector de tipo de reporte */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <FileText className="text-blue-600" size={20} />
          <h3 className="text-lg font-medium text-gray-900">Generar Reporte Personalizado</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
          <button
            onClick={() => setTipoReporte('ventas')}
            className={`p-4 rounded-lg border-2 transition-all ${
              tipoReporte === 'ventas'
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-200 hover:border-gray-300 text-gray-700'
            }`}
          >
            <TrendingUp className="mx-auto mb-2" size={24} />
            <p className="text-sm font-medium">Ventas</p>
          </button>

          <button
            onClick={() => setTipoReporte('recargas')}
            className={`p-4 rounded-lg border-2 transition-all ${
              tipoReporte === 'recargas'
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-200 hover:border-gray-300 text-gray-700'
            }`}
          >
            <Download className="mx-auto mb-2" size={24} />
            <p className="text-sm font-medium">Recargas</p>
          </button>

          <button
            onClick={() => setTipoReporte('top-productos')}
            className={`p-4 rounded-lg border-2 transition-all ${
              tipoReporte === 'top-productos'
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-200 hover:border-gray-300 text-gray-700'
            }`}
          >
            <FileText className="mx-auto mb-2" size={24} />
            <p className="text-sm font-medium">Top Productos</p>
          </button>

          <button
            onClick={() => setTipoReporte('consumos-tarjeta')}
            className={`p-4 rounded-lg border-2 transition-all ${
              tipoReporte === 'consumos-tarjeta'
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-200 hover:border-gray-300 text-gray-700'
            }`}
          >
            <Search className="mx-auto mb-2" size={24} />
            <p className="text-sm font-medium">Consumos</p>
          </button>

          <button
            onClick={() => setTipoReporte('financiero')}
            className={`p-4 rounded-lg border-2 transition-all ${
              tipoReporte === 'financiero'
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-200 hover:border-gray-300 text-gray-700'
            }`}
          >
            <Calendar className="mx-auto mb-2" size={24} />
            <p className="text-sm font-medium">Financiero</p>
          </button>
        </div>

        {/* Filtros */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fecha Inicio
            </label>
            <Input
              type="date"
              value={fechaInicio}
              onChange={(e) => setFechaInicio(e.target.value)}
              max={fechaFin}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fecha Fin
            </label>
            <Input
              type="date"
              value={fechaFin}
              onChange={(e) => setFechaFin(e.target.value)}
              min={fechaInicio}
              max={new Date().toISOString().split('T')[0]}
            />
          </div>

          {(tipoReporte === 'ventas' || tipoReporte === 'recargas') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Método de Pago (Opcional)
              </label>
              <select
                value={metodoPago}
                onChange={(e) => setMetodoPago(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos</option>
                <option value="efectivo">Efectivo</option>
                <option value="tarjeta">Tarjeta</option>
                <option value="online">Online</option>
                <option value="transferencia">Transferencia</option>
              </select>
            </div>
          )}

          {tipoReporte === 'top-productos' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cantidad de Productos
              </label>
              <Input
                type="number"
                value={limite}
                onChange={(e) => setLimite(Number(e.target.value))}
                min={5}
                max={100}
              />
            </div>
          )}

          {tipoReporte === 'consumos-tarjeta' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Número de Tarjeta
              </label>
              <Input
                type="text"
                leftIcon={<Search className="h-5 w-5 text-gray-400" />}
                value={nroTarjeta}
                onChange={(e) => setNroTarjeta(e.target.value)}
                placeholder="Ej: 1234567890"
              />
            </div>
          )}
        </div>

        <Button
          onClick={generarReporte}
          disabled={cargando}
          className="w-full md:w-auto"
        >
          {cargando ? 'Generando...' : 'Generar Reporte'}
        </Button>
      </Card>

      {/* Resultados - Reporte de Ventas */}
      {reporteVentas && tipoReporte === 'ventas' && (
        <Card>
          <h4 className="text-lg font-medium text-gray-900 mb-6">Reporte de Ventas</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Total Ventas</p>
              <p className="text-2xl font-bold text-blue-600">{reporteVentas.total_ventas}</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Monto Total</p>
              <p className="text-2xl font-bold text-green-600">
                {formatearMoneda(reporteVentas.total_monto)}
              </p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Ticket Promedio</p>
              <p className="text-2xl font-bold text-purple-600">
                {formatearMoneda(reporteVentas.promedio_ticket)}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="text-center p-3 bg-gray-50 rounded">
              <p className="text-xs text-gray-600">Efectivo</p>
              <p className="text-lg font-semibold">{formatearMoneda(reporteVentas.ventas_efectivo)}</p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded">
              <p className="text-xs text-gray-600">Tarjeta</p>
              <p className="text-lg font-semibold">{formatearMoneda(reporteVentas.ventas_tarjeta)}</p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded">
              <p className="text-xs text-gray-600">Online</p>
              <p className="text-lg font-semibold">{formatearMoneda(reporteVentas.ventas_online)}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Resultados - Reporte Financiero */}
      {reporteFinanciero && tipoReporte === 'financiero' && (
        <Card>
          <h4 className="text-lg font-medium text-gray-900 mb-6">Reporte Financiero</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex justify-between items-center p-4 bg-green-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Ingresos por Ventas</span>
                <span className="text-lg font-bold text-green-600">
                  {formatearMoneda(reporteFinanciero.ingresos_ventas)}
                </span>
              </div>
              <div className="flex justify-between items-center p-4 bg-blue-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Comisiones Cobradas</span>
                <span className="text-lg font-bold text-blue-600">
                  {formatearMoneda(reporteFinanciero.comisiones_cobradas)}
                </span>
              </div>
              <div className="flex justify-between items-center p-4 bg-purple-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Ingreso Total</span>
                <span className="text-xl font-bold text-purple-600">
                  {formatearMoneda(reporteFinanciero.ingreso_total)}
                </span>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center p-4 bg-orange-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Costo Inventario</span>
                <span className="text-lg font-bold text-orange-600">
                  {formatearMoneda(reporteFinanciero.costo_inventario)}
                </span>
              </div>
              <div className="flex justify-between items-center p-4 bg-green-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Margen Bruto</span>
                <span className="text-xl font-bold text-green-600">
                  {formatearMoneda(reporteFinanciero.margen_bruto)}
                </span>
              </div>
              <div className="flex justify-between items-center p-4 bg-blue-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">% Margen</span>
                <span className="text-2xl font-bold text-blue-600">
                  {reporteFinanciero.porcentaje_margen.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Más resultados para otros tipos de reportes... */}
    </div>
  );
}
