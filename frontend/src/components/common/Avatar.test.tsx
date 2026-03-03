/**
 * Tests para el componente Avatar
 */
import { render } from '@testing-library/react';
import Avatar from './Avatar';

describe('Avatar Component', () => {
  test('renderiza con imagen cuando se proporciona src', () => {
    const { container } = render(<Avatar src="/test.jpg" alt="Test User" />);
    const img = container.querySelector('img');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', '/test.jpg');
    expect(img).toHaveAttribute('alt', 'Test User');
  });

  test('muestra iniciales cuando no hay imagen pero sí name', () => {
    const { container } = render(<Avatar name="Juan Pérez" />);
    expect(container.textContent).toBe('JP');
  });

  test('muestra iniciales correctas para nombres largos', () => {
    const { container } = render(<Avatar name="María José González López" />);
    expect(container.textContent).toBe('ML');
  });

  test('muestra iniciales para nombre corto', () => {
    const { container } = render(<Avatar name="Ana" />);
    expect(container.textContent).toBe('AN');
  });

  test('muestra ícono por defecto cuando no hay src ni name', () => {
    const { container } = render(<Avatar />);
    const icon = container.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  test('aplica tamaño correcto', () => {
    const { container, rerender } = render(<Avatar size="xs" />);
    expect(container.firstChild?.firstChild).toHaveClass('h-6', 'w-6');
    
    rerender(<Avatar size="xl" />);
    expect(container.firstChild?.firstChild).toHaveClass('h-16', 'w-16');
  });

  test('aplica forma circular por defecto', () => {
    const { container } = render(<Avatar />);
    expect(container.firstChild?.firstChild).toHaveClass('rounded-full');
  });

  test('aplica forma cuadrada cuando se especifica', () => {
    const { container } = render(<Avatar shape="square" />);
    expect(container.firstChild?.firstChild).toHaveClass('rounded-lg');
  });

  test('muestra indicador de estado online', () => {
    const { container } = render(<Avatar status="online" />);
    const statusDot = container.querySelector('.bg-green-500');
    expect(statusDot).toBeInTheDocument();
  });

  test('muestra indicador de estado offline', () => {
    const { container } = render(<Avatar status="offline" />);
    const statusDot = container.querySelector('.bg-gray-400');
    expect(statusDot).toBeInTheDocument();
  });

  test('muestra indicador de estado away', () => {
    const { container } = render(<Avatar status="away" />);
    const statusDot = container.querySelector('.bg-yellow-500');
    expect(statusDot).toBeInTheDocument();
  });

  test('muestra indicador de estado busy', () => {
    const { container } = render(<Avatar status="busy" />);
    const statusDot = container.querySelector('.bg-red-500');
    expect(statusDot).toBeInTheDocument();
  });

  test('aplica className personalizado', () => {
    const { container } = render(<Avatar className="custom-class" />);
    expect(container.firstChild).toHaveClass('custom-class');
  });
});
