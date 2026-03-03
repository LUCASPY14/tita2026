/**
 * Tests para el componente Checkbox
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Checkbox from './Checkbox';

describe('Checkbox Component', () => {
  test('renderiza checkbox correctamente', () => {
    render(<Checkbox name="test" />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeInTheDocument();
  });

  test('muestra label cuando se proporciona', () => {
    render(<Checkbox name="terms" label="Acepto términos y condiciones" />);
    expect(screen.getByText('Acepto términos y condiciones')).toBeInTheDocument();
  });

  test('checkbox no está marcado por defecto', () => {
    render(<Checkbox name="test" />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).not.toBeChecked();
  });

  test('puede ser marcado y desmarcado', async () => {
    const user = userEvent.setup();
    render(<Checkbox name="test" label="Test checkbox" />);
    const checkbox = screen.getByRole('checkbox');

    await user.click(checkbox);
    expect(checkbox).toBeChecked();

    await user.click(checkbox);
    expect(checkbox).not.toBeChecked();
  });

  test('acepta valor defaultChecked', () => {
    render(<Checkbox name="test" defaultChecked />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeChecked();
  });

  test('está deshabilitado cuando disabled=true', () => {
    render(<Checkbox name="test" disabled />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeDisabled();
    expect(checkbox).toHaveClass('disabled:bg-gray-100');
  });

  test('muestra mensaje de error cuando error está presente', () => {
    render(<Checkbox name="terms" error="Debes aceptar los términos" />);
    expect(screen.getByText('Debes aceptar los términos')).toBeInTheDocument();
  });

  test('aplica clases de error cuando hay error', () => {
    render(<Checkbox name="test" error="Error" />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toHaveClass('border-red-500');
  });

  test('muestra helper text cuando se proporciona', () => {
    render(<Checkbox name="newsletter" helperText="Recibirás emails semanales" />);
    expect(screen.getByText('Recibirás emails semanales')).toBeInTheDocument();
  });

  test('aplica tamaño sm correctamente', () => {
    render(<Checkbox name="test" checkboxSize="sm" />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toHaveClass('h-4', 'w-4');
  });

  test('aplica tamaño md por defecto', () => {
    render(<Checkbox name="test" />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toHaveClass('h-5', 'w-5');
  });

  test('aplica tamaño lg correctamente', () => {
    render(<Checkbox name="test" checkboxSize="lg" />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toHaveClass('h-6', 'w-6');
  });

  test('label tiene color deshabilitado cuando disabled', () => {
    const { container } = render(<Checkbox name="test" label="Disabled Label" disabled />);
    const label = screen.getByText('Disabled Label');
    expect(label).toHaveClass('text-gray-400');
  });

  test('aplica className personalizado', () => {
    render(<Checkbox name="test" className="custom-class" />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toHaveClass('custom-class');
  });

  test('establece aria-invalid cuando hay error', () => {
    render(<Checkbox name="test" error="Error message" />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toHaveAttribute('aria-invalid', 'true');
  });

  test('label es clickeable y marca el checkbox', async () => {
    const user = userEvent.setup();
    render(<Checkbox name="test" label="Click me" />);
    const label = screen.getByText('Click me');
    const checkbox = screen.getByRole('checkbox');

    await user.click(label);
    expect(checkbox).toBeChecked();
  });

  test('llama onChange cuando cambia el estado', async () => {
    const user = userEvent.setup();
    const handleChange = jest.fn();
    render(<Checkbox name="test" onChange={handleChange} />);
    const checkbox = screen.getByRole('checkbox');

    await user.click(checkbox);
    expect(handleChange).toHaveBeenCalledTimes(1);
  });
});
