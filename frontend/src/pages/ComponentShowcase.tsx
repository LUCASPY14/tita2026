/**
 * GUÍA DE USO - Componentes UI Base
 * Ejemplos de uso de todos los componentes creados
 */

import React, { useState } from 'react';
import {
  Button,
  Input,
  Select,
  Checkbox,
  Badge,
  Avatar,
  Spinner,
  Textarea,
  Card,
  Modal,
  ModalFooter,
  SearchBar,
  FormInput,
  FormSelect,
  FormCheckbox,
  FormGroup,
} from '../components/common';
import { toast, toastCustom } from '../utils/toast';
import { Download, Plus, Mail, Lock } from 'lucide-react';

const ComponentShowcase: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const [checkboxValue, setCheckboxValue] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Componentes UI - Cantina Tita
          </h1>
          <p className="text-gray-600">
            Sistema de diseño completo con componentes reutilizables
          </p>
        </div>

        {/* Buttons */}
        <Card title="Buttons" subtitle="Botones con diferentes variantes y tamaños">
          <div className="space-y-4">
            <div className="flex flex-wrap gap-3">
              <Button variant="primary">Primary</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="success">Success</Button>
              <Button variant="danger">Danger</Button>
              <Button variant="warning">Warning</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button size="sm">Small</Button>
              <Button size="md">Medium</Button>
              <Button size="lg">Large</Button>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button leftIcon={<Plus className="h-4 w-4" />}>Con Icono Izq</Button>
              <Button rightIcon={<Download className="h-4 w-4" />}>Con Icono Der</Button>
              <Button isLoading>Cargando</Button>
              <Button disabled>Deshabilitado</Button>
            </div>

            <Button fullWidth>Botón de Ancho Completo</Button>
          </div>
        </Card>

        {/* Inputs */}
        <Card title="Inputs" subtitle="Campos de entrada con diferentes configuraciones">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Nombre"
              placeholder="Ingrese su nombre"
              required
            />
            <Input
              label="Email"
              type="email"
              placeholder="email@ejemplo.com"
              leftIcon={<Mail className="h-5 w-5" />}
            />
            <Input
              label="Contraseña"
              type="password"
              placeholder="••••••••"
              leftIcon={<Lock className="h-5 w-5" />}
              helperText="Mínimo 8 caracteres"
            />
            <Input
              label="Con Error"
              placeholder="Campo inválido"
              error="Este campo es requerido"
            />
            <Input
              label="Input Small"
              inputSize="sm"
              placeholder="Tamaño pequeño"
            />
            <Input
              label="Input Large"
              inputSize="lg"
              placeholder="Tamaño grande"
            />
          </div>
        </Card>

        {/* Select */}
        <Card title="Select" subtitle="Selects con opciones">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Select
              label="Categoría"
              placeholder="Seleccione una categoría"
              options={[
                { value: '1', label: 'Alimentos' },
                { value: '2', label: 'Bebidas' },
                { value: '3', label: 'Snacks' },
              ]}
            />
            <Select
              label="Estado"
              options={[
                { value: 'activo', label: 'Activo' },
                { value: 'inactivo', label: 'Inactivo' },
                { value: 'pendiente', label: 'Pendiente', disabled: true },
              ]}
              required
            />
          </div>
        </Card>

        {/* Checkbox & Textarea */}
        <Card title="Checkbox & Textarea" subtitle="Casillas de verificación y áreas de texto">
          <div className="space-y-4">
            <div className="flex gap-4">
              <Checkbox
                label="Acepto los términos y condiciones"
                checked={checkboxValue}
                onChange={(e) => setCheckboxValue(e.target.checked)}
              />
              <Checkbox checkboxSize="sm" label="Small" />
              <Checkbox checkboxSize="lg" label="Large" />
            </div>

            <Textarea
              label="Descripción"
              placeholder="Ingrese una descripción..."
              rows={4}
              helperText="Máximo 500 caracteres"
            />
          </div>
        </Card>

        {/* Badges */}
        <Card title="Badges" subtitle="Etiquetas y estados">
          <div className="flex flex-wrap gap-3">
            <Badge variant="default">Default</Badge>
            <Badge variant="primary">Primary</Badge>
            <Badge variant="success">Success</Badge>
            <Badge variant="warning">Warning</Badge>
            <Badge variant="danger">Danger</Badge>
            <Badge variant="info">Info</Badge>
          </div>
          <div className="flex flex-wrap gap-3 mt-4">
            <Badge variant="success" dot>Con Punto</Badge>
            <Badge size="sm">Small</Badge>
            <Badge size="md">Medium</Badge>
            <Badge size="lg">Large</Badge>
          </div>
        </Card>

        {/* Avatars */}
        <Card title="Avatars" subtitle="Avatares de usuario">
          <div className="flex flex-wrap items-center gap-4">
            <Avatar name="Juan Pérez" size="xs" />
            <Avatar name="María González" size="sm" status="online" />
            <Avatar name="Pedro Ramírez" size="md" status="away" />
            <Avatar name="Ana Silva" size="lg" status="busy" />
            <Avatar name="Carlos López" size="xl" status="offline" />
            <Avatar shape="square" name="Admin" />
          </div>
        </Card>

        {/* Spinner */}
        <Card title="Spinners" subtitle="Indicadores de carga">
          <div className="flex flex-wrap items-center gap-6">
            <Spinner size="xs" />
            <Spinner size="sm" />
            <Spinner size="md" />
            <Spinner size="lg" />
            <Spinner size="xl" />
            <Spinner variant="secondary" text="Cargando..." />
          </div>
        </Card>

        {/* SearchBar */}
        <Card title="SearchBar" subtitle="Barra de búsqueda">
          <div className="space-y-4">
            <SearchBar
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              placeholder="Buscar productos..."
            />
            <SearchBar searchSize="sm" placeholder="Búsqueda pequeña" />
            <SearchBar searchSize="lg" placeholder="Búsqueda grande" />
          </div>
        </Card>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card 
            title="Card Default" 
            subtitle="Variante por defecto"
            variant="default"
          >
            Contenido de la tarjeta
          </Card>
          <Card 
            title="Card Bordered" 
            subtitle="Con borde grueso"
            variant="bordered"
          >
            Contenido de la tarjeta
          </Card>
          <Card 
            title="Card Elevated" 
            subtitle="Con sombra elevada"
            variant="elevated"
            hoverable
          >
            Contenido de la tarjeta
          </Card>
        </div>

        {/* Toasts */}
        <Card title="Toasts" subtitle="Notificaciones">
          <div className="flex flex-wrap gap-3">
            <Button onClick={() => toast.success('Operación exitosa')}>
              Toast Success
            </Button>
            <Button onClick={() => toast.error('Error al procesar')}>
              Toast Error
            </Button>
            <Button onClick={() => toast.warning('Advertencia importante')}>
              Toast Warning
            </Button>
            <Button onClick={() => toast.info('Información útil')}>
              Toast Info
            </Button>
            <Button onClick={() => toastCustom.success('¡Guardado!', 'Los cambios se guardaron correctamente')}>
              Toast Custom
            </Button>
          </div>
        </Card>

        {/* Modal */}
        <Card title="Modal" subtitle="Ventanas modales">
          <Button onClick={() => setIsModalOpen(true)}>
            Abrir Modal
          </Button>

          <Modal
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            title="Ejemplo de Modal"
            subtitle="Este es un modal de ejemplo con footer personalizado"
            footer={
              <ModalFooter
                onCancel={() => setIsModalOpen(false)}
                onConfirm={() => {
                  toast.success('Modal confirmado');
                  setIsModalOpen(false);
                }}
                confirmText="Guardar"
                cancelText="Cancelar"
              />
            }
          >
            <div className="space-y-4">
              <p>Este es el contenido del modal. Aquí puedes agregar formularios, información, etc.</p>
              <Input label="Nombre" placeholder="Ingrese un nombre" />
              <Textarea label="Descripción" rows={3} />
            </div>
          </Modal>
        </Card>

        {/* Form Components */}
        <Card title="Form Components" subtitle="Componentes de formulario con React Hook Form">
          <div className="space-y-4">
            <FormGroup label="Información Personal" required>
              <div className="grid grid-cols-2 gap-4">
                <FormInput name="firstName" label="Nombre" required />
                <FormInput name="lastName" label="Apellido" required />
              </div>
            </FormGroup>

            <FormGroup label="Contacto">
              <FormInput 
                name="email" 
                type="email" 
                label="Email" 
                leftIcon={<Mail className="h-5 w-5" />}
              />
            </FormGroup>

            <FormSelect
              name="role"
              label="Rol"
              options={[
                { value: 'admin', label: 'Administrador' },
                { value: 'user', label: 'Usuario' },
              ]}
            />

            <FormCheckbox
              name="terms"
              label="Acepto los términos y condiciones"
            />
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ComponentShowcase;
