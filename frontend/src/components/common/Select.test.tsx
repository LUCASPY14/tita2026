/**
 * Tests para el componente Select
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Select from './Select';

const mockOptions = [
  { value: '1', label: 'Opción 1' },
  { value: '2', label: 'Opción 2' },
  { value: '3', label: 'Opción 3' },
  { value: '4', label: 'Opción 4', disabled: true },
];

describe('Select Component', () => {
  test('renderiza correctamente', () => {
    render(<Select name="test" options={mockOptions} />);
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
  });

  test('renderiza todas las opciones', () => {
    render(<Select name="test" options={mockOptions} />);
    mockOptions.forEach(option => {
      expect(screen.getByText(option.label)).toBeInTheDocument();
    });
  });

  test('muestra label cuando se proporciona', () => {
    render(<Select name="category" label="Categoría" options={mockOptions} />);
    expect(screen.getByText('Categoría')).toBeInTheDocument();
  });

  test('muestra asterisco cuando required=true', () => {
    render(<Select name="test" label="Required" required options={mockOptions} />);
    const asterisk = screen.getByText('*');
    expect(asterisk).toBeInTheDocument();
    expect(asterisk).toHaveClass('text-red-500');
  });

  test('muestra placeholder cuando se proporciona', () => {
    render(<Select name="test" options={mockOptions} placeholder="Seleccione..." />);
    expect(screen.getByText('Seleccione...')).toBeInTheDocument();
  });

  test('placeholder está deshabilitado', () => {
    render(<Select name="test" options={mockOptions} placeholder="Seleccione..." />);
    const placeholderOption = screen.getByText('Seleccione...') as HTMLOptionElement;
    expect(placeholderOption).toHaveAttribute('disabled');
  });

  test('puede seleccionar una opción', async () => {
    const user = userEvent.setup();
    render(<Select name="test" options={mockOptions} />);
    const select = screen.getByRole('combobox');
    
    await user.selectOptions(select, '2');
    expect(select).toHaveValue('2');
  });

  test('opciones deshabilitadas no son seleccionables', () => {
    render(<Select name="test" options={mockOptions} />);
    const disabledOption = screen.getByText('Opción 4') as HTMLOptionElement;
    expect(disabledOption).toHaveAttribute('disabled');
  });

  test('muestra mensaje de error cuando error está presente', () => {
    render(<Select name="test" options={mockOptions} error="Campo requerido" />);
    expect(screen.getByText('Campo requerido')).toBeInTheDocument();
  });

  test('aplica clases de error cuando hay error', () => {
    render(<Select name="test" options={mockOptions} error="Error" />);
    const select = screen.getByRole('combobox');
    expect(select).toHaveClass('border-red-500');
  });

  test('muestra helper text cuando se proporciona', () => {
    render(<Select name="test" options={mockOptions} helperText="Seleccione una opción" />);
    expect(screen.getByText('Seleccione una opción')).toBeInTheDocument();
  });

  test('está deshabilitado cuando disabled=true', () => {
    render(<Select name="test" options={mockOptions} disabled />);
    const select = screen.getByRole('combobox');
    expect(select).toBeDisabled();
    expect(select).toHaveClass('disabled:bg-gray-100');
  });

  test('aplica tamaño sm correctamente', () => {
    render(<Select name="test" options={mockOptions} selectSize="sm" />);
    const select = screen.getByRole('combobox');
    expect(select).toHaveClass('px-3', 'py-1.5', 'text-sm');
  });

  test('aplica tamaño md por defecto', () => {
    render(<Select name="test" options={mockOptions} />);
    const select = screen.getByRole('combobox');
    expect(select).toHaveClass('px-3', 'py-2', 'text-base');
  });

  test('aplica tamaño lg correctamente', () => {
    render(<Select name="test" options={mockOptions} selectSize="lg" />);
    const select = screen.getByRole('combobox');
    expect(select).toHaveClass('px-4', 'py-3', 'text-lg');
  });

  test('muestra ícono chevron', () => {
    const { container } = render(<Select name="test" options={mockOptions} />);
    const icon = container.querySelector('.lucide-chevron-down');
    expect(icon).toBeInTheDocument();
  });

  test('aplica className personalizado', () => {
    render(<Select name="test" options={mockOptions} className="custom-class" />);
    const select = screen.getByRole('combobox');
    expect(select).toHaveClass('custom-class');
  });

  test('establece aria-invalid cuando hay error', () => {
    render(<Select name="test" options={mockOptions} error="Error message" />);
    const select = screen.getByRole('combobox');
    expect(select).toHaveAttribute('aria-invalid', 'true');
  });

  test('asocia label con select mediante htmlFor/id', () => {
    render(<Select name="category" label="Categoría" options={mockOptions} />);
    const label = screen.getByText('Categoría');
    const select = screen.getByRole('combobox');
    expect(label).toHaveAttribute('for', 'category');
    expect(select).toHaveAttribute('id', 'category');
  });

  test('llama onChange cuando cambia la selección', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    render(<Select name="test" options={mockOptions} onChange={handleChange} />);
    const select = screen.getByRole('combobox');
    
    await user.selectOptions(select, '2');
    expect(handleChange).toHaveBeenCalledTimes(1);
  });
});
