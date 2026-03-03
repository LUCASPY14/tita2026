/**
 * Tests para el componente Card
 */
import { render, screen } from '@testing-library/react';
import Card from './Card';

describe('Card Component', () => {
  test('renderiza children correctamente', () => {
    render(
      <Card>
        <p>Card content</p>
      </Card>
    );
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  test('renderiza título cuando se proporciona', () => {
    render(<Card title="Test Title">Content</Card>);
    expect(screen.getByText('Test Title')).toBeInTheDocument();
  });

  test('aplica className personalizado', () => {
    const { container } = render(
      <Card className="custom-class">Content</Card>
    );
    const card = container.firstChild;
    expect(card).toHaveClass('custom-class');
  });

  test('aplica estilos base de Card', () => {
    const { container } = render(<Card>Content</Card>);
    const card = container.firstChild;
    expect(card).toHaveClass('bg-white', 'rounded-lg', 'border', 'border-gray-200');
  });

  test('renderiza múltiples children', () => {
    render(
      <Card>
        <h2>Title</h2>
        <p>Description</p>
        <button>Action</button>
      </Card>
    );
    
    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Description')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });
});
