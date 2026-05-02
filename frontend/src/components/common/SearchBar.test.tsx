/**
 * Tests para el componente SearchBar
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchBar from './SearchBar';

describe('SearchBar Component', () => {
  test('renderiza correctamente', () => {
    render(<SearchBar />);
    const input = screen.getByPlaceholderText('Buscar...');
    expect(input).toBeInTheDocument();
  });

  test('muestra placeholder personalizado', () => {
    render(<SearchBar placeholder="Buscar productos..." />);
    expect(screen.getByPlaceholderText('Buscar productos...')).toBeInTheDocument();
  });

  test('muestra ícono de búsqueda', () => {
    const { container } = render(<SearchBar />);
    const searchIcon = container.querySelector('svg');
    expect(searchIcon).toBeInTheDocument();
  });

  test('acepta entrada de texto del usuario', async () => {
    const user = userEvent.setup();
    render(<SearchBar />);
    const input = screen.getByRole('searchbox');
    
    await user.type(input, 'test search');
    expect(input).toHaveValue('test search');
  });

  test('llama onSearch cuando el usuario escribe', async () => {
    const user = userEvent.setup();
    const handleSearch = vi.fn();
    render(<SearchBar onSearch={handleSearch} />);
    const input = screen.getByRole('searchbox');
    
    await user.type(input, 'test');
    expect(handleSearch).toHaveBeenCalled();
    expect(handleSearch).toHaveBeenLastCalledWith('test');
  });

  test('muestra botón limpiar cuando hay texto', async () => {
    const user = userEvent.setup();
    render(<SearchBar />);
    const input = screen.getByRole('searchbox');
    
    await user.type(input, 'test');
    const clearButton = screen.getByRole('button');
    expect(clearButton).toBeInTheDocument();
  });

  test('no muestra botón limpiar cuando está vacío', () => {
    render(<SearchBar />);
    const clearButton = screen.queryByRole('button');
    expect(clearButton).not.toBeInTheDocument();
  });

  test('limpia el input cuando se hace click en botón limpiar', async () => {
    const user = userEvent.setup();
    render(<SearchBar />);
    const input = screen.getByRole('searchbox');
    
    await user.type(input, 'test');
    expect(input).toHaveValue('test');
    
    const clearButton = screen.getByRole('button');
    await user.click(clearButton);
    expect(input).toHaveValue('');
  });

  test('llama onClear cuando se limpia el input', async () => {
    const user = userEvent.setup();
    const handleClear = vi.fn();
    render(<SearchBar onClear={handleClear} />);
    const input = screen.getByRole('searchbox');
    
    await user.type(input, 'test');
    const clearButton = screen.getByRole('button');
    await user.click(clearButton);
    
    expect(handleClear).toHaveBeenCalledTimes(1);
  });

  test('aplica tamaño sm correctamente', () => {
    render(<SearchBar searchSize="sm" />);
    const input = screen.getByRole('searchbox');
    expect(input).toHaveClass('h-9', 'text-sm');
  });

  test('aplica tamaño md por defecto', () => {
    render(<SearchBar />);
    const input = screen.getByRole('searchbox');
    expect(input).toHaveClass('h-10', 'text-base');
  });

  test('aplica tamaño lg correctamente', () => {
    render(<SearchBar searchSize="lg" />);
    const input = screen.getByRole('searchbox');
    expect(input).toHaveClass('h-12', 'text-lg');
  });

  test('aplica className personalizado', () => {
    const { container } = render(<SearchBar className="custom-class" />);
    expect(container.firstChild).toHaveClass('custom-class');
  });

  test('acepta value controlado', () => {
    render(<SearchBar value="controlled value" onChange={() => {}} />);
    const input = screen.getByRole('searchbox');
    expect(input).toHaveValue('controlled value');
  });

  test('muestra animación cuando isLoading=true', () => {
    const { container } = render(<SearchBar isLoading />);
    const searchIcon = container.querySelector('.animate-pulse');
    expect(searchIcon).toBeInTheDocument();
  });
});
