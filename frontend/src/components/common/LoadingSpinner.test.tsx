/**
 * Tests para el componente LoadingSpinner
 */
import { render, screen } from '@testing-library/react';
import { Spinner } from './LoadingSpinner';

describe('LoadingSpinner Component', () => {
  test('renderiza el spinner correctamente', () => {
    const { container } = render(<Spinner />);
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  test('aplica tamaño md por defecto', () => {
    const { container } = render(<Spinner />);
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toHaveClass('h-8', 'w-8');
  });

  test('aplica tamaño xs correctamente', () => {
    const { container } = render(<Spinner size="xs" />);
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toHaveClass('h-4', 'w-4');
  });

  test('aplica tamaño xl correctamente', () => {
    const { container } = render(<Spinner size="xl" />);
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toHaveClass('h-16', 'w-16');
  });

  test('aplica variant primary por defecto', () => {
    const { container } = render(<Spinner />);
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toHaveClass('text-amber-500');
  });

  test('aplica variant secondary correctamente', () => {
    const { container } = render(<Spinner variant="secondary" />);
    const spinner = container.querySelector('.text-green-500');
    expect(spinner).toBeInTheDocument();
  });

  test('aplica variant white correctamente', () => {
    const { container } = render(<Spinner variant="white" />);
    const spinner = container.querySelector('.text-white');
    expect(spinner).toBeInTheDocument();
  });

  test('muestra texto cuando se proporciona', () => {
    render(<Spinner text="Cargando..." />);
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
  });

  test('no muestra texto cuando no se proporciona', () => {
    const { container } = render(<Spinner />);
    const text = container.querySelector('p');
    expect(text).not.toBeInTheDocument();
  });

  test('muestra fullScreen cuando fullScreen=true', () => {
    const { container } = render(<Spinner fullScreen />);
    const overlay = container.querySelector('.fixed');
    expect(overlay).toBeInTheDocument();
    expect(overlay).toHaveClass('z-50', 'flex');
  });

  test('no muestra overlay cuando fullScreen=false', () => {
    const { container } = render(<Spinner fullScreen={false} />);
    const overlay = container.querySelector('.fixed');
    expect(overlay).not.toBeInTheDocument();
  });

  test('aplica className personalizado', () => {
    const { container } = render(<Spinner className="custom-class" />);
    const wrapper = container.querySelector('.custom-class');
    expect(wrapper).toBeInTheDocument();
  });

  test('texto tiene color correcto según variant white', () => {
    const { container } = render(<Spinner variant="white" text="Loading" />);
    const textElement = container.querySelector('.text-white');
    expect(textElement).toBeInTheDocument();
  });
});
