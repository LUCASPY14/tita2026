/**
 * Tests para el componente Textarea
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Textarea from './Textarea';

describe('Textarea Component', () => {
  test('renderiza textarea correctamente', () => {
    render(<Textarea name="test" />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toBeInTheDocument();
  });

  test('muestra label cuando se proporciona', () => {
    render(<Textarea name="description" label="Descripción" />);
    expect(screen.getByText('Descripción')).toBeInTheDocument();
  });

  test('muestra asterisco cuando required=true', () => {
    render(<Textarea name="test" label="Required field" required />);
    const asterisk = screen.getByText('*');
    expect(asterisk).toBeInTheDocument();
    expect(asterisk).toHaveClass('text-red-500');
  });

  test('acepta entrada de texto del usuario', async () => {
    const user = userEvent.setup();
    render(<Textarea name="test" />);
    const textarea = screen.getByRole('textbox');
    
    await user.type(textarea, 'Este es un texto largo');
    expect(textarea).toHaveValue('Este es un texto largo');
  });

  test('muestra mensaje de error cuando error está presente', () => {
    render(<Textarea name="test" error="Campo requerido" />);
    expect(screen.getByText('Campo requerido')).toBeInTheDocument();
  });

  test('aplica clases de error cuando hay error', () => {
    render(<Textarea name="test" error="Error" />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('border-red-500');
  });

  test('muestra helper text cuando se proporciona', () => {
    render(<Textarea name="test" helperText="Máximo 500 caracteres" />);
    expect(screen.getByText('Máximo 500 caracteres')).toBeInTheDocument();
  });

  test('está deshabilitado cuando disabled=true', () => {
    render(<Textarea name="test" disabled />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toBeDisabled();
    expect(textarea).toHaveClass('disabled:bg-gray-100');
  });

  test('aplica número de filas por defecto (4)', () => {
    render(<Textarea name="test" />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('rows', '4');
  });

  test('aplica número de filas personalizado', () => {
    render(<Textarea name="test" rows={10} />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('rows', '10');
  });

  test('aplica tamaño sm correctamente', () => {
    render(<Textarea name="test" textareaSize="sm" />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('px-3', 'py-1.5', 'text-sm');
  });

  test('aplica tamaño md por defecto', () => {
    render(<Textarea name="test" />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('px-3', 'py-2', 'text-base');
  });

  test('aplica tamaño lg correctamente', () => {
    render(<Textarea name="test" textareaSize="lg" />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('px-4', 'py-3', 'text-lg');
  });

  test('permite redimensionar (resize-y)', () => {
    render(<Textarea name="test" />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('resize-y');
  });

  test('aplica className personalizado', () => {
    render(<Textarea name="test" className="custom-class" />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('custom-class');
  });

  test('establece aria-invalid cuando hay error', () => {
    render(<Textarea name="test" error="Error message" />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('aria-invalid', 'true');
  });

  test('asocia label con textarea mediante htmlFor/id', () => {
    render(<Textarea name="comments" label="Comentarios" />);
    const label = screen.getByText('Comentarios');
    const textarea = screen.getByRole('textbox');
    expect(label).toHaveAttribute('for', 'comments');
    expect(textarea).toHaveAttribute('id', 'comments');
  });

  test('acepta placeholder', () => {
    render(<Textarea name="test" placeholder="Escribe aquí..." />);
    const textarea = screen.getByPlaceholderText('Escribe aquí...');
    expect(textarea).toBeInTheDocument();
  });

  test('llama onChange cuando cambia el texto', async () => {
    const user = userEvent.setup();
    const handleChange = jest.fn();
    render(<Textarea name="test" onChange={handleChange} />);
    const textarea = screen.getByRole('textbox');
    
    await user.type(textarea, 'test');
    expect(handleChange).toHaveBeenCalled();
  });
});
