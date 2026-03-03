/**
 * Tests para el componente Badge
 */
import { render, screen } from '@testing-library/react';
import Badge from './Badge';

describe('Badge Component', () => {
  test('renderiza children correctamente', () => {
    render(<Badge>Test Badge</Badge>);
    expect(screen.getByText('Test Badge')).toBeInTheDocument();
  });

  test('aplica variant default por defecto', () => {
    const { container } = render(<Badge>Default</Badge>);
    const badge = container.firstChild;
    expect(badge).toHaveClass('bg-gray-100', 'text-gray-800');
  });

  test('aplica variant primary correctamente', () => {
    const { container } = render(<Badge variant="primary">Primary</Badge>);
    const badge = container.firstChild;
    expect(badge).toHaveClass('bg-amber-100', 'text-amber-800');
  });

  test('aplica variant success correctamente', () => {
    const { container } = render(<Badge variant="success">Success</Badge>);
    const badge = container.firstChild;
    expect(badge).toHaveClass('bg-green-100', 'text-green-800');
  });

  test('aplica variant warning correctamente', () => {
    const { container } = render(<Badge variant="warning">Warning</Badge>);
    const badge = container.firstChild;
    expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800');
  });

  test('aplica variant danger correctamente', () => {
    const { container } = render(<Badge variant="danger">Danger</Badge>);
    const badge = container.firstChild;
    expect(badge).toHaveClass('bg-red-100', 'text-red-800');
  });

  test('aplica variant info correctamente', () => {
    const { container } = render(<Badge variant="info">Info</Badge>);
    const badge = container.firstChild;
    expect(badge).toHaveClass('bg-blue-100', 'text-blue-800');
  });

  test('aplica tamaño sm correctamente', () => {
    const { container } = render(<Badge size="sm">Small</Badge>);
    const badge = container.firstChild;
    expect(badge).toHaveClass('px-2', 'py-0.5', 'text-xs');
  });

  test('aplica tamaño md por defecto', () => {
    const { container } = render(<Badge>Medium</Badge>);
    const badge = container.firstChild;
    expect(badge).toHaveClass('px-2.5', 'py-1', 'text-sm');
  });

  test('aplica tamaño lg correctamente', () => {
    const { container } = render(<Badge size="lg">Large</Badge>);
    const badge = container.firstChild;
    expect(badge).toHaveClass('px-3', 'py-1.5', 'text-base');
  });

  test('muestra dot cuando dot=true', () => {
    const { container } = render(<Badge dot>With Dot</Badge>);
    const dot = container.querySelector('.rounded-full.bg-gray-500');
    expect(dot).toBeInTheDocument();
  });

  test('dot tiene color según variant', () => {
    const { container } = render(<Badge variant="success" dot>Success</Badge>);
    const dot = container.querySelector('.bg-green-500');
    expect(dot).toBeInTheDocument();
  });

  test('aplica className personalizado', () => {
    const { container } = render(<Badge className="custom-class">Custom</Badge>);
    expect(container.firstChild).toHaveClass('custom-class');
  });
});
