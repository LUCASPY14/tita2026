/**
 * Tests para el componente Input
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Mail } from 'lucide-react';
import Input from './Input';

describe('Input Component', () => {
  test('renderiza input básico correctamente', () => {
    render(<Input name="test" />);
    const input = screen.getByRole('textbox');
    expect(input).toBeInTheDocument();
  });

  test('muestra label cuando se proporciona', () => {
    render(<Input name="email" label="Correo Electrónico" />);
    expect(screen.getByText('Correo Electrónico')).toBeInTheDocument();
  });

  test('muestra asterisco cuando required=true', () => {
    render(<Input name="email" label="Email" required />);
    const asterisk = screen.getByText('*');
    expect(asterisk).toBeInTheDocument();
    expect(asterisk).toHaveClass('text-red-500');
  });

  test('acepta entrada de texto del usuario', async () => {
    const user = userEvent.setup();
    render(<Input name="username" />);
    const input = screen.getByRole('textbox');
    
    await user.type(input, 'test@example.com');
    expect(input).toHaveValue('test@example.com');
  });

  test('muestra mensaje de error cuando error está presente', () => {
    render(<Input name="email" error="Email inválido" />);
    expect(screen.getByText('Email inválido')).toBeInTheDocument();
  });

  test('aplica clases de error cuando hay error', () => {
    render(<Input name="email" error="Error" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('border-red-500');
  });

  test('muestra helper text cuando se proporciona', () => {
    render(<Input name="password" helperText="Mínimo 8 caracteres" />);
    expect(screen.getByText('Mínimo 8 caracteres')).toBeInTheDocument();
  });

  test('está deshabilitado cuando disabled=true', () => {
    render(<Input name="test" disabled />);
    const input = screen.getByRole('textbox');
    expect(input).toBeDisabled();
    expect(input).toHaveClass('disabled:bg-gray-100');
  });

  test('aplica type correcto', () => {
    const { rerender } = render(<Input name="email" type="email" />);
    let input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('type', 'email');

    rerender(<Input name="password" type="password" />);
    input = screen.getByDisplayValue('') as HTMLInputElement;
    expect(input).toHaveAttribute('type', 'password');
  });

  test('aplica tamaño sm correctamente', () => {
    render(<Input name="test" inputSize="sm" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('px-3', 'py-1.5', 'text-sm');
  });

  test('aplica tamaño md por defecto', () => {
    render(<Input name="test" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('px-3', 'py-2', 'text-base');
  });

  test('aplica tamaño lg correctamente', () => {
    render(<Input name="test" inputSize="lg" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('px-4', 'py-3', 'text-lg');
  });

  test('renderiza leftIcon cuando se proporciona', () => {
    const { container } = render(<Input name="email" leftIcon={<Mail data-testid="email-icon" />} />);
    expect(screen.getByTestId('email-icon')).toBeInTheDocument();
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('pl-10');
  });

  test('renderiza rightIcon cuando se proporciona', () => {
    const { container } = render(<Input name="search" rightIcon={<Mail data-testid="search-icon" />} />);
    expect(screen.getByTestId('search-icon')).toBeInTheDocument();
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('pr-10');
  });

  test('aplica className personalizado', () => {
    render(<Input name="test" className="custom-class" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('custom-class');
  });

  test('establece aria-invalid cuando hay error', () => {
    render(<Input name="test" error="Error message" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('aria-invalid', 'true');
  });

  test('asocia label con input mediante htmlFor/id', () => {
    render(<Input name="username" label="Usuario" />);
    const label = screen.getByText('Usuario');
    const input = screen.getByRole('textbox');
    expect(label).toHaveAttribute('for', 'username');
    expect(input).toHaveAttribute('id', 'username');
  });
});
