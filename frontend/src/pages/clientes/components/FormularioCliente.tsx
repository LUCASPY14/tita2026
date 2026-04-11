import React, { useState, useEffect } from 'react';
import { Save, X } from 'lucide-react';
import { Input, Button, Select } from '../../../components/common';
import { clientesService, ciudadesService, ClienteData } from '../../../services/clientes.service';
import type { Cliente, TipoCliente, Ciudad } from '../../../types';
import toast from 'react-hot-toast';

interface FormularioClienteProps {
  cliente: Cliente | null;
  onGuardado: () => void;
  onCancelar: () => void;
}

const FormularioCliente: React.FC<FormularioClienteProps> = ({
  cliente,
  onGuardado,
  onCancelar,
}) => {
  const [guardando, setGuardando] = useState(false);
  const [tiposCliente, setTiposCliente] = useState<TipoCliente[]>([]);
  const [ciudades, setCiudades] = useState<Ciudad[]>([]);
  const [formData, setFormData] = useState<ClienteData>({
    nombres: '',
    apellidos: '',
    razon_social: '',
    ruc_ci: '',
    direccion: '',
    ciudad: '',
    id_ciudad: null,
    telefono: '',
    email: '',
    limite_credito: 0,
    estado: true,
    id_lista: 1, // Default lista de precios
    id_tipo_cliente: 1, // Default tipo cliente
  });

  const [errores, setErrores] = useState<Record<string, string>>({});

  useEffect(() => {
    cargarTiposCliente();
    cargarCiudades();
    if (cliente) {
      setFormData({
        nombres: cliente.nombres,
        apellidos: cliente.apellidos,
        razon_social: cliente.razon_social || '',
        ruc_ci: cliente.ruc_ci,
        direccion: cliente.direccion || '',
        ciudad: cliente.ciudad || '',
        id_ciudad: cliente.id_ciudad ?? null,
        telefono: cliente.telefono || '',
        email: cliente.email || '',
        limite_credito: cliente.limite_credito || 0,
        estado: cliente.estado,
        id_lista: cliente.id_lista,
        id_tipo_cliente: cliente.id_tipo_cliente,
      });
    }
  }, [cliente]);

  const cargarCiudades = async () => {
    try {
      setCiudades(await ciudadesService.getCiudades());
    } catch {
      console.error('Error al cargar ciudades');
    }
  };

  const cargarTiposCliente = async () => {
    try {
      const tipos = await clientesService.getTiposCliente();
      setTiposCliente(tipos);
    } catch (error) {
      console.error('Error al cargar tipos de cliente:', error);
    }
  };

  const validarFormulario = (): boolean => {
    const nuevosErrores: Record<string, string> = {};

    if (!formData.nombres.trim()) {
      nuevosErrores.nombres = 'Los nombres son requeridos';
    }

    if (!formData.apellidos.trim()) {
      nuevosErrores.apellidos = 'Los apellidos son requeridos';
    }

    if (!formData.ruc_ci.trim()) {
      nuevosErrores.ruc_ci = 'El RUC/CI es requerido';
    }

    if (formData.email && !/\S+@\S+\.\S+/.test(formData.email)) {
      nuevosErrores.email = 'Email inválido';
    }

    if (formData.limite_credito && formData.limite_credito < 0) {
      nuevosErrores.limite_credito = 'El límite de crédito no puede ser negativo';
    }

    setErrores(nuevosErrores);
    return Object.keys(nuevosErrores).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value,
    }));

    // Limpiar error del campo
    if (errores[name]) {
      setErrores(prev => {
        const nuevos = { ...prev };
        delete nuevos[name];
        return nuevos;
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validarFormulario()) {
      toast.error('Por favor, corrije los errores en el formulario');
      return;
    }

    setGuardando(true);
    try {
      if (cliente) {
        await clientesService.actualizarCliente(cliente.id_cliente, formData);
        toast.success('Cliente actualizado exitosamente');
      } else {
        await clientesService.crearCliente(formData);
        toast.success('Cliente creado exitosamente');
      }
      onGuardado();
    } catch (error: any) {
      console.error('Error al guardar cliente:', error);
      toast.error(error.response?.data?.detail || 'Error al guardar el cliente');
    } finally {
      setGuardando(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Información Personal */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Información Personal</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Nombres *"
            name="nombres"
            value={formData.nombres}
            onChange={handleChange}
            error={errores.nombres}
            required
          />

          <Input
            label="Apellidos *"
            name="apellidos"
            value={formData.apellidos}
            onChange={handleChange}
            error={errores.apellidos}
            required
          />

          <Input
            label="Razón Social"
            name="razon_social"
            value={formData.razon_social}
            onChange={handleChange}
            helperText="Solo para empresas"
          />

          <Input
            label="RUC/CI *"
            name="ruc_ci"
            value={formData.ruc_ci}
            onChange={handleChange}
            error={errores.ruc_ci}
            required
          />
        </div>
      </div>

      {/* Información de Contacto */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Información de Contacto</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Dirección"
            name="direccion"
            value={formData.direccion}
            onChange={handleChange}
          />

          <Input
            label="Ciudad"
            name="ciudad"
            value={formData.ciudad}
            onChange={handleChange}
            helperText="Texto libre o seleccione del catálogo"
          />

          {ciudades.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ciudad (catálogo)
              </label>
              <select
                name="id_ciudad"
                value={formData.id_ciudad ?? ''}
                onChange={e => setFormData(prev => ({
                  ...prev,
                  id_ciudad: e.target.value ? Number(e.target.value) : null,
                }))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-400 focus:outline-none"
              >
                <option value="">— Sin selección —</option>
                {ciudades.map(c => (
                  <option key={c.id_ciudad} value={c.id_ciudad}>{c.nombre}</option>
                ))}
              </select>
            </div>
          )}

          <Input
            label="Teléfono"
            name="telefono"
            type="tel"
            value={formData.telefono}
            onChange={handleChange}
          />

          <Input
            label="Email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            error={errores.email}
          />
        </div>
      </div>

      {/* Configuración Comercial */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Configuración Comercial</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Límite de Crédito (Gs.)"
            name="limite_credito"
            type="number"
            value={formData.limite_credito}
            onChange={handleChange}
            error={errores.limite_credito}
            helperText="Monto máximo de crédito permitido"
          />

          <Select
            label="Tipo de Cliente *"
            name="id_tipo_cliente"
            value={formData.id_tipo_cliente}
            onChange={handleChange}
            options={tiposCliente.map(tipo => ({
              value: tipo.id_tipo_cliente.toString(),
              label: tipo.nombre_tipo || tipo.nombre || '',
            }))}
            required
          />
        </div>
      </div>

      {/* Botones de Acción */}
      <div className="flex justify-end gap-3 border-t pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={onCancelar}
          disabled={guardando}
          leftIcon={<X className="h-5 w-5" />}
        >
          Cancelar
        </Button>
        <Button
          type="submit"
          variant="primary"
          disabled={guardando}
          leftIcon={guardando ? undefined : <Save className="h-5 w-5" />}
        >
          {guardando ? 'Guardando...' : cliente ? 'Actualizar' : 'Crear Cliente'}
        </Button>
      </div>
    </form>
  );
};

export default FormularioCliente;
